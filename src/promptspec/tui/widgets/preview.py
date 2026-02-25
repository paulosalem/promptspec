"""Preview widget — live variable substitution preview of the spec."""

from __future__ import annotations

import re

from textual.widgets import Static


_MUSTACHE_VAR = re.compile(r"\{\{(\w+)\}\}")


class PreviewPane(Static):
    """Shows the spec text with {{variables}} replaced by current form values.

    This is a fast regex-only preview (no LLM). Unresolved variables
    are highlighted with brackets.
    """

    DEFAULT_CSS = """
    PreviewPane {
        height: 1fr;
        border: round $primary-darken-1;
        padding: 1;
        overflow-y: auto;
    }
    """

    def __init__(self, spec_text: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self._spec_text = spec_text
        self._values: dict[str, str] = {}

    def update_values(self, values: dict[str, str]) -> None:
        """Update current variable values and refresh the preview."""
        self._values = values
        self._refresh_preview()

    def _refresh_preview(self) -> None:
        """Render the spec text with current values substituted."""
        def _replace(m: re.Match) -> str:
            var_name = m.group(1)
            val = self._values.get(var_name, "")
            if val:
                return f"[bold green]{val}[/bold green]"
            return f"[bold red]⟨{var_name}⟩[/bold red]"

        rendered = _MUSTACHE_VAR.sub(_replace, self._spec_text)
        # Truncate very long specs for display
        lines = rendered.splitlines()
        if len(lines) > 200:
            rendered = "\n".join(lines[:200]) + "\n[dim]… (truncated)[/dim]"
        self.update(rendered)
