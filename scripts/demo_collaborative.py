#!/usr/bin/env python3
"""demo_collaborative.py — Interactive collaborative editing demo.

Demonstrates the Collaborative Editing strategy by drafting an
investment strategy with the user acting as editor.

Usage:
    # Interactive mode (opens $EDITOR for each round):
    python scripts/demo_collaborative.py

    # Non-interactive mode (auto-approves — useful for CI / demos):
    python scripts/demo_collaborative.py --non-interactive

    # Custom spec + vars:
    python scripts/demo_collaborative.py \
        --spec specs/collaborative-writer.promptspec.md \
        --vars specs/vars/some-vars.json

Requires: OPENAI_API_KEY set, promptspec installed (pip install -e '.[all,dev]')
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Ensure the project is importable
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from promptspec.controller import PromptSpecConfig, PromptSpecController, CompositionResult
from promptspec.engines.collaborative import CollaborativeEngine
from promptspec.engines.base import RuntimeConfig

from ellements.patterns.callbacks import (
    FileEditCallback,
    PassthroughEditCallback,
    CallableEditCallback,
)
from ellements.patterns.strategies import StepRecord

# ── ANSI colours ─────────────────────────────────────────────────

BOLD = "\033[1m"
DIM = "\033[2m"
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
MAGENTA = "\033[35m"
RED = "\033[31m"
RESET = "\033[0m"
RULE = "═" * 72


def banner(title: str) -> None:
    print(f"\n{MAGENTA}{RULE}{RESET}")
    print(f"{BOLD}{MAGENTA}  {title}{RESET}")
    print(f"{MAGENTA}{RULE}{RESET}\n")


def step_label(step: StepRecord) -> None:
    source = step.metadata.get("source", "?")
    rnd = step.metadata.get("round", "-")
    colour = GREEN if source == "llm" else YELLOW
    icon = "🤖" if source == "llm" else "✏️"
    reason = step.metadata.get("reason", "")
    extra = f" ({reason})" if reason else ""
    print(f"{colour}{icon}  [{step.name}] round={rnd} source={source}{extra}{RESET}")


def on_step(step: StepRecord) -> None:
    """Pretty-print each step as it happens."""
    step_label(step)
    preview = step.response[:200] if step.response else "(empty)"
    if len(step.response) > 200:
        preview += f"… ({len(step.response)} chars total)"
    print(f"{DIM}    {preview}{RESET}\n")


# ── CLI editing callback ─────────────────────────────────────────

class CLIEditCallback:
    """Interactive callback: prints content and lets user type edits inline.

    Simpler than FileEditCallback — no $EDITOR dependency.
    The user can:
      - Press Enter on empty input to approve (unchanged)
      - Type DONE to finish
      - Type ABORT to cancel
      - Type replacement text line-by-line (end with a blank line)
    """

    async def request_edit(self, content: str, context: str = "") -> str:
        print(f"\n{CYAN}{'─' * 60}{RESET}")
        print(f"{BOLD}{CYAN}  📝 YOUR TURN — {context}{RESET}")
        print(f"{CYAN}{'─' * 60}{RESET}")
        print(content)
        print(f"{CYAN}{'─' * 60}{RESET}")
        print(f"{DIM}Options:{RESET}")
        print(f"{DIM}  • Press Enter to approve this version as-is{RESET}")
        print(f"{DIM}  • Type 'DONE' to finish with the current version{RESET}")
        print(f"{DIM}  • Type 'ABORT' to cancel entirely{RESET}")
        print(f"{DIM}  • Type replacement text (end with an empty line){RESET}")
        print()

        lines = []
        first_line = input(f"{YELLOW}> {RESET}")

        if first_line.strip() == "":
            return content  # Approve unchanged
        if first_line.strip() == "ABORT":
            return ""  # Abort signal
        if first_line.strip() == "DONE":
            return content + "\nDONE"  # Done signal

        lines.append(first_line)
        print(f"{DIM}(Continue typing. Empty line to finish.){RESET}")
        while True:
            line = input(f"{YELLOW}> {RESET}")
            if line == "":
                break
            lines.append(line)

        return "\n".join(lines)


# ── Main ─────────────────────────────────────────────────────────

async def run(
    spec_path: Path,
    vars_path: Path | None,
    config_path: Path | None,
    interactive: bool,
    use_editor: bool,
) -> None:
    # Load vars
    variables = {}
    if vars_path and vars_path.exists():
        variables = json.loads(vars_path.read_text(encoding="utf-8"))

    # Load config
    config = None
    if config_path and config_path.exists():
        config = RuntimeConfig.from_yaml(config_path)

    # Compose the spec
    banner("COMPOSING SPEC")
    print(f"{DIM}  Spec:   {spec_path}{RESET}")
    print(f"{DIM}  Vars:   {vars_path or '(none)'}{RESET}")
    print(f"{DIM}  Config: {config_path or '(none)'}{RESET}")
    print()

    spec_text = spec_path.read_text(encoding="utf-8")
    controller = PromptSpecController(PromptSpecConfig())
    result = await controller.compose(
        spec_text,
        variables=variables,
        base_dir=spec_path.parent,
    )
    print(f"{GREEN}  ✓ Composed successfully{RESET}")
    print(f"{DIM}    Engine:  {result.execution.get('type', 'collaborative') if result.execution else 'collaborative'}{RESET}")
    print(f"{DIM}    Prompts: {list(result.prompts.keys()) if result.prompts else ['default']}{RESET}")
    print()

    # Choose callback
    if not interactive:
        callback = PassthroughEditCallback()
        print(f"{YELLOW}  ▸ Non-interactive mode: auto-approving all drafts{RESET}\n")
    elif use_editor:
        callback = FileEditCallback()
        editor = os.environ.get("VISUAL") or os.environ.get("EDITOR") or "nano"
        print(f"{YELLOW}  ▸ Editor mode: will open {editor} for each round{RESET}\n")
    else:
        callback = CLIEditCallback()
        print(f"{YELLOW}  ▸ Interactive CLI mode: you'll edit inline{RESET}\n")

    # Inject callback into config
    if config is None:
        config = RuntimeConfig(engine="collaborative")
    config.engine_config["edit_callback"] = callback

    # Execute
    banner("EXECUTING — Collaborative Editing")
    engine = CollaborativeEngine()
    exec_result = await engine.execute(result, config=config, on_step=on_step)

    # Show final output
    banner("FINAL OUTPUT")
    print(exec_result.output)
    print()

    # Summary
    rounds = exec_result.metadata.get("rounds_completed", "?")
    max_rounds = exec_result.metadata.get("max_rounds", "?")
    total_steps = len(exec_result.steps)
    print(f"{GREEN}{RULE}{RESET}")
    print(f"{BOLD}{GREEN}  ✓ Collaborative editing complete!{RESET}")
    print(f"{DIM}    Rounds: {rounds}/{max_rounds}  |  Steps: {total_steps}{RESET}")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Collaborative editing demo — draft an investment strategy with LLM + human co-editing."
    )
    parser.add_argument(
        "--spec",
        type=Path,
        default=REPO_ROOT / "specs" / "collaborative-investment-strategy.promptspec.md",
        help="Path to the .promptspec.md file",
    )
    parser.add_argument(
        "--vars",
        type=Path,
        default=REPO_ROOT / "specs" / "vars" / "collaborative-investment-strategy-example.json",
        help="Path to the variables JSON file",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=REPO_ROOT / "specs" / "collaborative-investment-strategy.promptspec.yaml",
        help="Path to the runtime YAML config",
    )
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Auto-approve all drafts (no human editing)",
    )
    parser.add_argument(
        "--editor",
        action="store_true",
        help="Use $EDITOR for editing instead of inline CLI input",
    )

    args = parser.parse_args()

    if not os.environ.get("OPENAI_API_KEY"):
        print(f"{YELLOW}⚠  OPENAI_API_KEY not set. Export it first:{RESET}")
        print("   export OPENAI_API_KEY=sk-...")
        sys.exit(1)

    asyncio.run(run(
        spec_path=args.spec,
        vars_path=args.vars,
        config_path=args.config,
        interactive=not args.non_interactive,
        use_editor=args.editor,
    ))


if __name__ == "__main__":
    main()
