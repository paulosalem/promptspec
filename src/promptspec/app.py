"""PromptSpec — CLI entry point.

Composes prompts from spec files containing directives (@refine, @if,
@match, @note) and variable substitutions.

Usage:
    promptspec spec.md --var key=value                    # interactive
    promptspec spec.md --vars-file v.json                 # interactive
    promptspec spec.md --batch-only --var k=v             # pure batch
    promptspec spec.md --output result.md                 # write to file
    promptspec spec.md --format json --output result.json # JSON to file
    cat spec.md | promptspec --stdin --batch-only
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict

from ellements.ui.cli import CliPrinter

from promptspec.controller import (
    CompositionResult,
    PromptSpecConfig,
    PromptSpecController,
)


# ------------------------------------------------------------------
# Argument parsing
# ------------------------------------------------------------------

def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="promptspec",
        description="Compose prompts from spec files with directives and variables.",
    )

    # Input
    parser.add_argument(
        "spec_file",
        nargs="?",
        help="Path to the prompt specification file (.promptspec.md)",
    )
    parser.add_argument(
        "--stdin",
        action="store_true",
        help="Read the prompt specification from stdin",
    )

    # Variables
    parser.add_argument(
        "--var",
        action="append",
        metavar="KEY=VALUE",
        help="Set a variable (repeatable). Example: --var topic=cats",
    )
    parser.add_argument(
        "--vars-file",
        type=Path,
        help="Path to a JSON file containing variable values",
    )

    # Output
    parser.add_argument(
        "-o", "--output",
        type=Path,
        help="Write output to a file instead of stdout",
    )
    parser.add_argument(
        "--format",
        choices=["markdown", "json", "xml"],
        default="markdown",
        dest="format",
        help="Output format: markdown (default), json, or xml (raw LLM XML)",
    )

    # Mode
    parser.add_argument(
        "--batch-only",
        action="store_true",
        help="Disable all interactivity — pure batch mode",
    )
    parser.add_argument(
        "--run",
        action="store_true",
        help="Compile AND execute: run the composed prompt(s) through an engine",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Show detailed step-by-step progress",
    )

    # Model
    parser.add_argument(
        "--model",
        default="gpt-4.1",
        help="LLM model to use (default: gpt-4.1)",
    )

    # Config
    parser.add_argument(
        "--config",
        type=Path,
        help="Path to a .promptspec.yaml or .json runtime config file",
    )

    # TUI
    parser.add_argument(
        "--ui",
        action="store_true",
        help="Launch an interactive TUI (requires promptspec[ui])",
    )

    # Discovery
    parser.add_argument(
        "--discover",
        action="store_true",
        help="Launch spec discovery chat — find the right spec interactively",
    )
    parser.add_argument(
        "--specs-dir",
        action="append",
        type=Path,
        metavar="DIR",
        help="Additional spec directory to search (repeatable)",
    )
    parser.add_argument(
        "--env",
        action="store_true",
        help="Print resolved configuration and environment, then exit",
    )

    # Machine-readable scan (used by VS Code extension)
    parser.add_argument(
        "--scan",
        action="store_true",
        help="Output spec metadata as JSON (inputs, title, execution strategy). Used by IDE integrations.",
    )

    return parser


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _parse_variables(printer: CliPrinter, args: argparse.Namespace) -> Dict[str, Any]:
    """Merge variables from --var flags and --vars-file."""
    variables: Dict[str, Any] = {}

    if args.vars_file:
        with open(args.vars_file, encoding="utf-8") as f:
            variables.update(json.load(f))

    if args.var:
        for item in args.var:
            if "=" not in item:
                printer.warning(f"Ignoring malformed --var '{item}' (expected KEY=VALUE)")
                continue
            key, _, value = item.partition("=")
            if value.lower() in ("true", "yes", "1"):
                variables[key.strip()] = True
            elif value.lower() in ("false", "no", "0"):
                variables[key.strip()] = False
            else:
                variables[key.strip()] = value

    return variables


def _format_raw_output(result: CompositionResult, fmt: str) -> str:
    """Format the primary output for stdout or file.

    Always returns ONLY the prompt content (no issues):
    - ``markdown``: the composed prompt text
    - ``json``: full structured data (includes issues in JSON fields)
    - ``xml``: raw XML from the LLM
    """
    if fmt == "xml":
        return result.raw_xml
    if fmt == "json":
        return json.dumps(result.to_dict(), indent=2, ensure_ascii=False)
    return result.composed_prompt


def _show_result(
    printer: CliPrinter,
    result: CompositionResult,
    fmt: str,
    elapsed: float,
    verbose: bool = False,
) -> None:
    """Display the composition result using the printer."""
    if fmt == "xml":
        printer.output_console.print(result.raw_xml, highlight=False)
    elif fmt == "json":
        printer.result_json(result.to_dict())
    else:
        # Markdown — always show the prompt
        printer.result_markdown(result.composed_prompt)
        if result.tools:
            printer.console.print()
            printer.console.print("[bold bright_blue]📦 Tools[/]")
            printer.console.print(
                json.dumps(result.tools, indent=2, ensure_ascii=False),
                highlight=False,
            )

    if verbose:
        printer.stats(
            {"Tool calls": result.tool_calls_made,
             "Issues": len(result.issues),
             "Output": f"{len(result.composed_prompt):,} chars"},
            elapsed=elapsed,
        )


# ------------------------------------------------------------------
# Modes
# ------------------------------------------------------------------

async def run_batch(
    printer: CliPrinter,
    spec_text: str,
    variables: Dict[str, Any],
    base_dir: Path,
    args: argparse.Namespace,
) -> int:
    """Run in batch mode — no interactivity."""
    config = PromptSpecConfig(model=args.model)
    controller = PromptSpecController(config)

    result = await controller.compose(
        spec_text, variables, base_dir, on_event=printer.event,
    )
    output = _format_raw_output(result, args.format)

    if args.output:
        args.output.write_text(output, encoding="utf-8")
        printer.file_written(args.output)
    else:
        print(output)

    return 0


async def run_interactive(
    printer: CliPrinter,
    spec_text: str,
    variables: Dict[str, Any],
    base_dir: Path,
    args: argparse.Namespace,
) -> int:
    """Run in interactive mode — compose, show result, allow follow-up."""
    config = PromptSpecConfig(model=args.model)
    controller = PromptSpecController(config)

    printer.header({"Spec": args.spec_file or "stdin", "Model": args.model})
    printer.variables(variables)
    printer.status("Composing prompt…")

    t0 = time.perf_counter()
    result = await controller.compose(
        spec_text, variables, base_dir, on_event=printer.event,
    )
    elapsed = time.perf_counter() - t0

    if args.output:
        raw = _format_raw_output(result, args.format)
        args.output.write_text(raw, encoding="utf-8")
        printer.file_written(args.output)
    else:
        _show_result(printer, result, args.format, elapsed, verbose=args.verbose)

    # Interactive follow-up loop
    while True:
        printer.console.print()
        try:
            follow_up = printer.console.input(
                "[bold bright_blue]Enter feedback to refine, or press Enter to finish:[/] "
            ).strip()
        except (EOFError, KeyboardInterrupt):
            printer.console.print()
            break

        if not follow_up:
            break

        spec_text_updated = f"{spec_text}\n\n# Additional Instructions\n\n{follow_up}"
        printer.status("Re-composing…")
        t0 = time.perf_counter()
        result = await controller.compose(
            spec_text_updated, variables, base_dir, on_event=printer.event,
        )
        elapsed = time.perf_counter() - t0
        _show_result(printer, result, args.format, elapsed, verbose=args.verbose)

    printer.done()
    return 0


async def run_execute(
    printer: CliPrinter,
    spec_text: str,
    variables: Dict[str, Any],
    base_dir: Path,
    args: argparse.Namespace,
) -> int:
    """Compile + execute: compose the spec, then run through an engine."""
    from ellements.patterns.strategies import StepRecord
    from promptspec.engines import ExecutionResult, RuntimeConfig, resolve_engine

    config = PromptSpecConfig(model=args.model)
    controller = PromptSpecController(config)

    # Load runtime config
    runtime_config = None
    if args.config:
        if not args.config.is_file():
            printer.error(f"Config file [bright_cyan]'{args.config}'[/] not found.")
            return 1
        if args.config.suffix in (".yaml", ".yml"):
            runtime_config = RuntimeConfig.from_yaml(args.config)
        else:
            runtime_config = RuntimeConfig.from_json(args.config)
        # Merge config variables (CLI overrides config)
        merged_vars = {**runtime_config.variables, **variables}
        variables = merged_vars

    printer.header({"Spec": args.spec_file or "stdin", "Model": args.model, "Mode": "run"})
    printer.variables(variables)
    printer.status("Composing prompt…")

    t0 = time.perf_counter()
    result = await controller.compose(
        spec_text, variables, base_dir, on_event=printer.event,
    )

    # Determine engine
    engine_name = "single-call"
    if runtime_config and runtime_config.engine:
        engine_name = runtime_config.engine
    elif result.execution and result.execution.get("type"):
        engine_name = result.execution["type"]

    printer.status(f"Executing with engine: {engine_name}…")

    # Build live-step callback for --verbose
    step_counter = [0]
    step_icons = {
        "generate": "✏️ ",
        "evaluate": "🔍",
        "synthesize": "🧩",
        "critique": "🧐",
        "revise": "📝",
        "sample": "🎲",
        "vote": "🗳️ ",
        "judge": "⚖️ ",
        "call": "📡",
        "stop": "🛑",
    }

    def _on_step(step: StepRecord) -> None:
        step_counter[0] += 1
        elapsed_so_far = time.perf_counter() - t0
        base_name = step.name.split("_")[0]
        icon = step_icons.get(base_name, "▸ ")
        preview = step.response[:120].replace("\n", " ")
        if len(step.response) > 120:
            preview += "…"
        meta_parts = []
        if step.metadata.get("round") is not None:
            meta_parts.append(f"round {step.metadata['round']}")
        if step.metadata.get("reason"):
            meta_parts.append(step.metadata["reason"])
        if step.metadata.get("aggregation"):
            meta_parts.append(step.metadata["aggregation"])
        meta_str = f" ({', '.join(meta_parts)})" if meta_parts else ""
        printer.console.print(
            f"  {icon} [bold]Step {step_counter[0]}[/]: "
            f"[bright_cyan]{step.name}[/]{meta_str}  "
            f"[dim]{elapsed_so_far:.1f}s[/]"
        )
        if args.verbose:
            printer.console.print(f"     [dim]{preview}[/]")

    on_step = _on_step if args.verbose else None

    engine = resolve_engine(engine_name)
    exec_result = await engine.execute(result, runtime_config, on_step=on_step)
    elapsed = time.perf_counter() - t0

    if args.output:
        output = exec_result.output
        if args.format == "json":
            output = json.dumps({
                "output": exec_result.output,
                "steps": [{"name": s.name, "prompt_key": s.prompt_key} for s in exec_result.steps],
                "metadata": exec_result.metadata,
            }, indent=2, ensure_ascii=False)
        args.output.write_text(output, encoding="utf-8")
        printer.file_written(args.output)
    else:
        printer.result_markdown(exec_result.output)

    if args.verbose:
        printer.stats(
            {
                "Engine": engine_name,
                "Steps": len(exec_result.steps),
                "Output": f"{len(exec_result.output):,} chars",
            },
            elapsed=elapsed,
        )

    printer.done()
    return 0


async def run_discover(args: argparse.Namespace) -> int:
    """Run the spec discovery chat mode."""
    from promptspec.discovery.catalog import scan_directories
    from promptspec.discovery.chat_ui import DiscoveryChatUI
    from promptspec.discovery.config import load_config, print_env
    from promptspec.discovery.metadata import ensure_metadata
    from promptspec.discovery.tools import (
        DISCOVERY_TOOLS,
        SpecSelected,
        create_tool_executor,
    )
    from promptspec.engines.chat import ChatEngine

    ui = DiscoveryChatUI()

    # 1. Load config
    ui.show_step("⚙️ ", "Loading configuration…")
    env_config = load_config(
        project_dir=Path.cwd(),
        extra_specs_dirs=getattr(args, "specs_dir", None),
    )
    dirs = env_config.effective_specs_dirs(Path.cwd())
    if env_config._global_path:
        ui.show_step("  ", f"[dim]Global:  {env_config._global_path}[/dim]")
    if env_config._project_path:
        ui.show_step("  ", f"[dim]Project: {env_config._project_path}[/dim]")

    # 2. Scan directories
    ui.show_step("📂", "Scanning spec directories…")
    entries = scan_directories(dirs)
    ui.show_scan_progress(entries, dirs)

    if not entries:
        ui.show_error("No specs found. Add specs to ./specs/ or configure specs_dirs.")
        return 1

    # 3. Compute/load metadata
    ui.show_step("🔍", "Loading metadata…")
    cached_count = [0]
    analyzed_count = [0]
    progress = ui.show_metadata_progress_start(len(entries))
    task_id = [None]

    def on_progress(current: int, total: int, title: str) -> None:
        analyzed_count[0] = current
        if task_id[0] is not None:
            progress.update(task_id[0], completed=current, description=f"[gold]Analyzing:[/gold] {title}")

    with progress:
        task_id[0] = progress.add_task("Analyzing specs…", total=len(entries))
        metadata = await ensure_metadata(
            entries,
            model=args.model,
            on_progress=on_progress,
        )
        # Mark any cached (not analyzed) specs as completed in the bar
        progress.update(task_id[0], completed=len(entries))

    cached_count[0] = len(entries) - analyzed_count[0]
    ui.show_cache_summary(cached_count[0], analyzed_count[0], len(entries))

    # 4. Load the discovery system prompt
    discovery_spec = Path(__file__).parent.parent / "promptspec" / "specs" / "spec-discovery.promptspec.md"
    # Try multiple locations
    for candidate in [
        Path.cwd() / "specs" / "spec-discovery.promptspec.md",
        Path(__file__).resolve().parent / ".." / ".." / "specs" / "spec-discovery.promptspec.md",
    ]:
        if candidate.is_file():
            discovery_spec = candidate
            break

    if discovery_spec.is_file():
        # Strip the @note and @tool blocks — use the text as system prompt
        raw = discovery_spec.read_text(encoding="utf-8")
        # Remove @note blocks and @tool blocks (they're handled by the tools system)
        lines = []
        in_note = False
        in_tool = False
        for line in raw.splitlines():
            stripped = line.strip()
            if stripped.startswith("@note"):
                in_note = True
                continue
            if stripped.startswith("@tool"):
                in_tool = True
                continue
            if in_note and (not stripped or stripped.startswith("@") or not line.startswith(" ")):
                in_note = False
            if in_tool and (stripped.startswith("@") and not stripped.startswith("@tool") and not line.startswith(" ")):
                in_tool = False
            if in_note or in_tool:
                continue
            # Skip lines starting with "## Tools" header
            if stripped == "## Tools":
                in_tool = True
                continue
            lines.append(line)
        system_prompt = "\n".join(lines).strip()
    else:
        system_prompt = (
            "You are PromptSpec Discovery — a friendly assistant that helps users "
            "find the right prompt specification. Use search_catalog to find specs, "
            "read_spec to examine them, and select_spec when the user is ready."
        )

    # 5. Build the chat engine
    tool_executor = create_tool_executor(entries, metadata)

    ui.show_ready()
    ui.show_banner()

    engine = ChatEngine(
        system_prompt=system_prompt,
        tools=DISCOVERY_TOOLS,
        tool_executor=tool_executor,
        ui=ui,
        model=args.model,
    )

    # 6. Run the chat loop
    try:
        await engine.run()
    except SpecSelected as sel:
        # Hand off to TUI
        spec_path = Path(sel.spec_path)
        if spec_path.is_file():
            # Find the matching entry for a nice display
            matching = [e for e in entries if str(e.path) == sel.spec_path]
            if matching:
                meta = metadata.get(str(matching[0].path))
                ui.show_selected(matching[0], meta)
            try:
                from promptspec.tui.app import launch_tui
                launch_tui(spec_path=spec_path)
            except ImportError:
                ui.show_error(
                    "Textual is required for the TUI. "
                    "Install with: pip install promptspec[ui]"
                )
                return 1
        else:
            ui.show_error(f"Spec file not found: {spec_path}")
            return 1
    except KeyboardInterrupt:
        pass

    ui.show_goodbye()
    return 0


# ------------------------------------------------------------------
# Entry point
# ------------------------------------------------------------------

def cli() -> None:
    """Main entry point for the promptspec command."""
    parser = create_parser()
    args = parser.parse_args()

    printer = CliPrinter(
        "PromptSpec",
        icon="🧩",
        verbose=args.verbose,
    )

    # --env: print environment and exit
    if getattr(args, "env", False):
        from promptspec.discovery.config import load_config, print_env
        config = load_config(
            project_dir=Path.cwd(),
            extra_specs_dirs=getattr(args, "specs_dir", None),
        )
        printer.console.print(print_env(config))
        sys.exit(0)

    # --discover: launch spec discovery chat
    if getattr(args, "discover", False):
        try:
            exit_code = asyncio.run(run_discover(args))
        except KeyboardInterrupt:
            printer.console.print("\n[dim]Interrupted. 👋[/]")
            exit_code = 130
        sys.exit(exit_code)

    # Read spec
    if args.stdin:
        spec_text = sys.stdin.read()
        base_dir = Path.cwd()
        spec_path = None
    elif args.spec_file:
        spec_path = Path(args.spec_file).resolve()
        if not spec_path.is_file():
            printer.error(f"Spec file [bright_cyan]'{args.spec_file}'[/] not found.")
            sys.exit(1)
        spec_text = spec_path.read_text(encoding="utf-8")
        base_dir = spec_path.parent
    else:
        parser.print_help()
        sys.exit(1)

    variables = _parse_variables(printer, args)

    # --scan: output spec metadata as JSON and exit
    if getattr(args, "scan", False):
        from promptspec.tui.scanner import scan_spec
        import dataclasses as _dc

        meta = scan_spec(spec_text)
        scan_data = {
            "title": meta.title,
            "description": meta.description,
            "inputs": [_dc.asdict(i) for i in meta.inputs],
            "execution": meta.execution,
            "prompt_names": meta.prompt_names,
            "tool_names": meta.tool_names,
            "refine_files": meta.refine_files,
            "embed_files": meta.embed_files,
        }
        print(json.dumps(scan_data, indent=2, ensure_ascii=False))
        sys.exit(0)

    # TUI mode
    if getattr(args, "ui", False):
        if spec_path is None:
            printer.error("--ui requires a spec file (not stdin).")
            sys.exit(1)
        try:
            from promptspec.tui.app import launch_tui
        except ImportError:
            printer.error(
                "Textual is required for --ui mode. "
                "Install with: [bright_cyan]pip install promptspec\\[ui][/]"
            )
            sys.exit(1)
        launch_tui(
            spec_path=spec_path,
            vars_path=args.vars_file,
            config_path=args.config,
        )
        sys.exit(0)

    try:
        if args.run:
            exit_code = asyncio.run(
                run_execute(printer, spec_text, variables, base_dir, args),
            )
        elif args.batch_only or args.stdin:
            exit_code = asyncio.run(
                run_batch(printer, spec_text, variables, base_dir, args),
            )
        else:
            exit_code = asyncio.run(
                run_interactive(printer, spec_text, variables, base_dir, args),
            )
    except KeyboardInterrupt:
        printer.console.print("\n[dim]Interrupted. 👋[/]")
        exit_code = 130

    sys.exit(exit_code)


if __name__ == "__main__":
    cli()
