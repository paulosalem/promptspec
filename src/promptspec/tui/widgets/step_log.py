"""Step log widget — displays execution progress."""

from __future__ import annotations

from textual.widgets import RichLog


class StepLog(RichLog):
    """Scrollable log showing strategy execution steps."""

    DEFAULT_CSS = """
    StepLog {
        height: 1fr;
        border: round $primary-darken-1;
        padding: 1;
    }
    """

    _STEP_ICONS = {
        "generate": "🔵",
        "critique": "🟡",
        "revise": "🟢",
        "continue": "🔄",
        "branch": "🌿",
        "evaluate": "⚖️",
        "select": "✅",
        "done": "🏁",
        "error": "❌",
    }

    def add_step(self, step_name: str, text: str, metadata: dict | None = None) -> None:
        """Add a step entry to the log."""
        icon = self._STEP_ICONS.get(step_name, "⚪")
        line = f"{icon} [bold]{step_name}[/bold]: {text[:200]}"
        if metadata:
            meta_str = ", ".join(f"{k}={v}" for k, v in metadata.items())
            line += f" [dim]({meta_str})[/dim]"
        self.write(line)

    def add_error(self, text: str) -> None:
        self.write(f"❌ [bold red]{text}[/bold red]")

    def add_info(self, text: str) -> None:
        self.write(f"ℹ️  [dim]{text}[/dim]")
