"""Input screen — dynamic form generated from SpecInput list."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import (
    Input,
    Select,
    Static,
    Switch,
    TextArea,
)

from promptspec.tui.scanner import SpecInput


class InputForm(Vertical):
    """Dynamically generates form widgets from a list of SpecInputs."""

    DEFAULT_CSS = """
    InputForm {
        height: auto;
        padding: 1;
    }
    """

    def __init__(self, inputs: list[SpecInput], **kwargs) -> None:
        super().__init__(**kwargs)
        self._inputs = inputs
        self._widgets: dict[str, Input | TextArea | Select | Switch] = {}

    def compose(self) -> ComposeResult:
        for spec_input in self._inputs:
            yield from self._build_input_group(spec_input)

    def _build_input_group(self, spec_input: SpecInput) -> ComposeResult:
        """Build a label + help text + widget for one SpecInput."""
        # Label
        source_tag = f" [dim]({spec_input.source_directive})[/dim]" if spec_input.source_directive else ""
        yield Static(
            f"[bold]{spec_input.name}[/bold]{source_tag}",
            classes="input-label",
            markup=True,
        )

        # Help text from @note
        if spec_input.description:
            yield Static(
                f"[italic dim]{spec_input.description}[/italic dim]",
                classes="input-help",
                markup=True,
            )

        # Widget based on type
        widget_id = f"input-{spec_input.name}"

        if spec_input.input_type == "select":
            options = [(opt, opt) for opt in (spec_input.options or [])]
            widget = Select(
                options,
                id=widget_id,
                prompt=f"Select {spec_input.name}…",
            )

        elif spec_input.input_type == "boolean":
            widget = Switch(
                id=widget_id,
                value=spec_input.default == "true",
            )

        elif spec_input.input_type == "multiline":
            widget = TextArea(
                id=widget_id,
            )

        elif spec_input.input_type == "file":
            hint = spec_input.file_hint or ""
            widget = Input(
                id=widget_id,
                placeholder=f"File path… {hint}",
            )

        else:  # "text"
            widget = Input(
                id=widget_id,
                placeholder=spec_input.name,
            )

        self._widgets[spec_input.name] = widget
        yield widget

    def get_values(self) -> dict[str, str]:
        """Collect current values from all form widgets."""
        values: dict[str, str] = {}
        for name, widget in self._widgets.items():
            if isinstance(widget, Switch):
                values[name] = "true" if widget.value else "false"
            elif isinstance(widget, Select):
                val = widget.value
                values[name] = str(val) if val is not None and val != Select.BLANK else ""
            elif isinstance(widget, TextArea):
                values[name] = widget.text
            elif isinstance(widget, Input):
                values[name] = widget.value
            else:
                values[name] = ""
        return values

    def set_values(self, values: dict[str, str]) -> None:
        """Pre-fill form widgets with values (e.g. from a JSON vars file)."""
        for name, val in values.items():
            widget = self._widgets.get(name)
            if widget is None:
                continue
            if isinstance(widget, Switch):
                widget.value = val.lower() in ("true", "1", "yes")
            elif isinstance(widget, Select):
                widget.value = val
            elif isinstance(widget, TextArea):
                widget.load_text(val)
            elif isinstance(widget, Input):
                widget.value = val
