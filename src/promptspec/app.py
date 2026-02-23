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

    # Read spec
    if args.stdin:
        spec_text = sys.stdin.read()
        base_dir = Path.cwd()
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

    try:
        if args.batch_only or args.stdin:
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
