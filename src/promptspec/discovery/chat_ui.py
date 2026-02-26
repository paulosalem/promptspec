"""Rich-based chat UI for spec discovery.

A gorgeous text-based chat interface with:
- Gold-themed styling
- User and assistant message bubbles
- Tool call notifications
- Animated thinking indicator
- Step-by-step progress output
"""

from __future__ import annotations

import itertools
import sys
import threading
import time
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn
from rich.text import Text
from rich.theme import Theme

from promptspec.discovery.catalog import SpecEntry
from promptspec.discovery.metadata import SpecMetadataEntry

# Gold theme
DISCOVERY_THEME = Theme({
    "gold": "bold #FFD700",
    "gold.dim": "#B8960F",
    "user": "bold bright_cyan",
    "assistant": "bold #FFD700",
    "tool": "dim #FFA500",
    "info": "dim",
    "success": "bold bright_green",
    "warn": "bold bright_yellow",
})


class DiscoveryChatUI:
    """Rich-powered chat UI for the discovery conversation."""

    def __init__(self, console: Optional[Console] = None) -> None:
        self.console = console or Console(theme=DISCOVERY_THEME)
        self._spinner_stop = threading.Event()
        self._spinner_thread: Optional[threading.Thread] = None

    # ── Progress helpers (for startup phases) ──────────────────────

    def show_banner(self) -> None:
        """Print the discovery mode banner."""
        self.console.print()
        self.console.print(
            Panel(
                "[gold]⚡ PromptSpec Discovery[/gold]\n\n"
                "[info]Describe what you need and I'll find the right spec for you.[/info]\n"
                "[info]Type [bold]quit[/bold] or press Ctrl+C to exit.[/info]",
                border_style="gold",
                padding=(1, 3),
            )
        )
        self.console.print()

    def show_step(self, icon: str, message: str) -> None:
        """Print a step-by-step status line."""
        self.console.print(f"  {icon}  {message}")

    def show_scan_progress(
        self,
        entries: List[SpecEntry],
        dirs: List,
    ) -> None:
        """Show scan results summary."""
        self.show_step("📂", f"Scanned [bold]{len(dirs)}[/] director{'y' if len(dirs) == 1 else 'ies'} — found [bold]{len(entries)}[/] specs")

    def show_metadata_progress_start(self, total: int) -> Progress:
        """Start a Rich progress bar for metadata analysis."""
        progress = Progress(
            SpinnerColumn("dots", style="gold"),
            TextColumn("[gold]Analyzing specs…[/gold]"),
            BarColumn(bar_width=30, style="gold.dim", complete_style="gold"),
            TextColumn("[info]{task.completed}/{task.total}[/info]"),
            console=self.console,
        )
        return progress

    def show_cache_summary(self, cached: int, analyzed: int, total: int) -> None:
        """Show cache statistics."""
        parts = []
        if analyzed > 0:
            parts.append(f"[bold]{analyzed}[/] analyzed")
        if cached > 0:
            parts.append(f"{cached} cached")
        self.show_step("💾", f"Metadata ready — {', '.join(parts)} ({total} total)")

    def show_ready(self) -> None:
        """Print the 'ready for chat' message."""
        self.console.print()
        self.console.print(
            "  💬  [gold]Ready![/gold] Tell me what you're looking for.",
        )
        self.console.print()

    # ── Chat messages ──────────────────────────────────────────────

    def get_user_input(self) -> str:
        """Prompt user for input."""
        try:
            text = self.console.input("[user]You:[/user] ").strip()
        except (EOFError, KeyboardInterrupt):
            self.console.print()
            return ""
        if text.lower() in ("quit", "exit", "q"):
            return ""
        return text

    def show_assistant(self, text: str) -> None:
        """Render an assistant response."""
        self.console.print()
        self.console.print("[assistant]Assistant:[/assistant]")
        self.console.print(
            Panel(
                Markdown(text),
                border_style="gold.dim",
                padding=(0, 2),
            )
        )
        self.console.print()

    def show_tool_call(self, name: str, args: Dict[str, Any]) -> None:
        """Show a tool call notification."""
        args_str = ", ".join(f"{k}={v!r}" for k, v in args.items())
        self.console.print(f"  [tool]🔧 {name}({args_str})[/tool]")

    def show_thinking(self) -> None:
        """Start an animated thinking indicator."""
        self._spinner_stop.clear()

        def _spin():
            frames = itertools.cycle(["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"])
            while not self._spinner_stop.is_set():
                frame = next(frames)
                sys.stdout.write(f"\r  [thinking] {frame} ")
                sys.stdout.flush()
                time.sleep(0.1)
            sys.stdout.write("\r" + " " * 30 + "\r")
            sys.stdout.flush()

        self._spinner_thread = threading.Thread(target=_spin, daemon=True)
        self._spinner_thread.start()

    def hide_thinking(self) -> None:
        """Stop the thinking indicator."""
        self._spinner_stop.set()
        if self._spinner_thread:
            self._spinner_thread.join(timeout=1)
            self._spinner_thread = None

    # ── Spec selection ─────────────────────────────────────────────

    def show_selected(self, entry: SpecEntry, meta: Optional[SpecMetadataEntry]) -> None:
        """Show the selected spec before handing off to TUI."""
        title = meta.summary if meta and meta.summary else entry.title
        self.console.print()
        self.console.print(
            Panel(
                f"[gold]Selected:[/gold] [bold]{entry.title}[/bold]\n"
                f"[info]{title}[/info]\n\n"
                f"[info]Launching interactive TUI…[/info]",
                border_style="success",
                padding=(1, 3),
            )
        )
        self.console.print()

    def show_error(self, message: str) -> None:
        """Show an error message."""
        self.console.print(f"  [bold red]✗[/bold red] {message}")

    def show_goodbye(self) -> None:
        """Print exit message."""
        self.console.print("[info]  👋 Goodbye![/info]")
        self.console.print()
