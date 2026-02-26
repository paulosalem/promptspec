"""PromptSpec TUI — main Textual application.

Launch with:
    promptspec spec.md --ui
    promptspec spec.md --ui --vars vars.json
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, ScrollableContainer
from textual.theme import Theme
from textual.widgets import Button, Footer, Header, Static, LoadingIndicator, TabbedContent, TabPane

from promptspec.tui.scanner import SpecMetadata, scan_spec
from promptspec.tui.screens.input import InputForm
from promptspec.tui.widgets.preview import PreviewPane
from promptspec.tui.widgets.spec_info import SpecInfoPanel
from promptspec.tui.widgets.step_log import StepLog

# Golden theme inspired by the @execute directive color (#FFD700)
PROMPTSPEC_THEME = Theme(
    name="promptspec-gold",
    primary="#FFD700",       # gold
    secondary="#FFA500",     # orange (prompt directive)
    accent="#E6BE00",        # darker gold
    warning="#FFA500",
    error="#FF6B6B",
    success="#50C878",       # emerald green
    foreground="#F5F0E1",    # warm white
    background="#1A1612",    # very dark warm brown
    surface="#241E18",       # dark brown
    panel="#2E2720",         # slightly lighter brown
    dark=True,
)


class PromptSpecApp(App):
    """Interactive TUI for PromptSpec files."""

    TITLE = "PromptSpec Runner"
    CSS_PATH = "theme.tcss"

    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit", show=True),
        Binding("ctrl+r", "run_spec", "Run", show=True),
        Binding("ctrl+p", "compose_spec", "Compose", show=True),
        Binding("ctrl+l", "toggle_left_panel", "Toggle Inputs", show=True),
    ]

    def __init__(
        self,
        spec_path: Path,
        vars_path: Optional[Path] = None,
        config_path: Optional[Path] = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.register_theme(PROMPTSPEC_THEME)
        self.theme = "promptspec-gold"
        self._spec_path = spec_path
        self._vars_path = vars_path
        self._config_path = config_path
        self._spec_text = spec_path.read_text()
        self._metadata = scan_spec(self._spec_text)
        self._initial_vars = self._load_vars(vars_path)

    def compose(self) -> ComposeResult:
        yield Header()

        with Horizontal(id="main-container"):
            # Left: spec info + input form
            with Vertical(id="left-panel"):
                with ScrollableContainer(id="left-scroll"):
                    yield SpecInfoPanel(self._metadata, id="spec-info")
                    yield Static("[bold]Inputs[/bold]", markup=True)
                    yield InputForm(self._metadata.inputs, id="input-form")

                # Action buttons (outside scroll, fixed at bottom)
                with Horizontal(id="action-bar"):
                    yield Button("Compose", id="btn-compose", variant="primary")
                    yield Button("▶ Run", id="btn-run", variant="success")

            # Right: tabbed preview/current-text + output
            with Vertical(id="right-panel"):
                with TabbedContent(id="right-tabs"):
                    with TabPane("Preview", id="tab-preview"):
                        yield Static(
                            f"[bold]Preview[/bold] — {self._spec_path.name}",
                            markup=True,
                            id="preview-title",
                        )
                        yield PreviewPane(self._spec_text, id="preview-pane")
                    with TabPane("Current Text", id="tab-current"):
                        yield Static(
                            "[bold]Current Text[/bold] — updated after each round",
                            markup=True,
                            id="current-title",
                        )
                        yield Static(
                            "[dim italic]No text yet — run the spec to see output here.[/dim italic]",
                            markup=True,
                            id="current-text-pane",
                        )
                yield Static("[bold]Output[/bold]", markup=True, id="output-title")
                yield LoadingIndicator(id="llm-spinner")
                yield StepLog(id="step-log")

        yield Footer()

    def on_mount(self) -> None:
        """Pre-fill form if vars were provided, then refresh preview."""
        if self._initial_vars:
            form = self.query_one("#input-form", InputForm)
            form.set_values(self._initial_vars)
        self._refresh_preview()

    # ── Event handlers ────────────────────────────────────────────

    def on_input_changed(self, event) -> None:
        self._refresh_preview()

    def on_text_area_changed(self, event) -> None:
        self._refresh_preview()

    def on_select_changed(self, event) -> None:
        self._refresh_preview()

    def on_switch_changed(self, event) -> None:
        self._refresh_preview()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-compose":
            self.action_compose_spec()
        elif event.button.id == "btn-run":
            self.action_run_spec()

    # ── Actions ───────────────────────────────────────────────────

    def action_compose_spec(self) -> None:
        """Compose the spec with current form values."""
        self.run_worker(self._do_compose(), exclusive=True, thread=False)

    def action_run_spec(self) -> None:
        """Compose and execute the spec."""
        self.run_worker(self._do_run(), exclusive=True, thread=False)

    def action_toggle_left_panel(self) -> None:
        """Show or hide the left input panel (Ctrl+L)."""
        panel = self.query_one("#left-panel")
        panel.display = not panel.display

    async def _do_compose(self) -> None:
        """Compose the spec using the controller."""
        log = self.query_one("#step-log", StepLog)
        log.clear()
        log.add_info("Composing…")
        self._show_spinner()

        values = self._get_form_values()
        try:
            from promptspec.controller import PromptSpecConfig, PromptSpecController

            config = self._build_config()
            controller = PromptSpecController(config)
            result = await controller.compose(
                self._spec_text,
                variables=values,
                base_dir=self._spec_path.parent,
            )
            # Show result in the preview
            prompt_text = result.composed_prompt
            preview = self.query_one("#preview-pane", PreviewPane)
            preview.update(f"[bold green]Composed prompt:[/bold green]\n\n{prompt_text}")
            log.add_step("done", f"Composed ({len(prompt_text)} chars)")
        except Exception as exc:
            log.add_error(str(exc))
        finally:
            self._hide_spinner()

    async def _do_run(self) -> None:
        """Compose and execute the spec with the engine."""
        log = self.query_one("#step-log", StepLog)
        log.clear()
        log.add_info("Running…")
        self._show_spinner()

        values = self._get_form_values()
        try:
            from promptspec.controller import PromptSpecConfig, PromptSpecController
            from promptspec.engines import resolve_engine
            from promptspec.engines.base import RuntimeConfig

            config = self._build_config()
            controller = PromptSpecController(config)

            # Compose
            log.add_step("generate", "Composing prompt…")
            composed = await controller.compose(
                self._spec_text,
                variables=values,
                base_dir=self._spec_path.parent,
            )

            # Determine engine
            strategy = "single-call"
            if self._metadata.execution:
                strategy = self._metadata.execution.get("type", "single-call")

            engine = resolve_engine(strategy)

            # Build runtime config — inject TUI edit callback for collaborative
            runtime_config = RuntimeConfig(engine=strategy)
            if strategy == "collaborative":
                from promptspec.tui.callbacks import TuiEditCallback
                done_signal = "DONE"
                if self._metadata.execution:
                    done_signal = self._metadata.execution.get("done_signal", "DONE")
                runtime_config.engine_config["edit_callback"] = TuiEditCallback(
                    self, done_signal=done_signal,
                )
                log.add_info("Collaborative mode — edit in the pop-up editor")
                # Hide left panel to give full width to collaboration
                self.query_one("#left-panel").display = False

            # Execute with step callback
            def on_step(step):
                step_name = getattr(step, "name", "step")
                step_text = getattr(step, "response", str(step))[:150]
                step_meta = getattr(step, "metadata", None)
                log.add_step(step_name, step_text, step_meta)
                # Update the "Current Text" pane with latest content
                full_response = getattr(step, "response", "")
                if full_response:
                    self._update_current_text(full_response)

            exec_result = await engine.execute(
                composed, config=runtime_config, on_step=on_step,
            )

            # Show final result
            final_text = exec_result.output
            self._update_current_text(final_text)
            # Auto-switch to Current Text tab
            try:
                self.query_one("#right-tabs", TabbedContent).active = "tab-current"
            except Exception:
                pass
            log.add_step("done", f"Finished ({len(final_text)} chars)")

        except Exception as exc:
            log.add_error(str(exc))
        finally:
            self._hide_spinner()

    def _update_current_text(self, text: str) -> None:
        """Update the 'Current Text' tab pane with new content."""
        try:
            pane = self.query_one("#current-text-pane", Static)
            pane.update(text)
        except Exception:
            pass

    def _show_spinner(self) -> None:
        """Show the animated loading indicator."""
        try:
            self.query_one("#llm-spinner").add_class("active")
        except Exception:
            pass

    def _hide_spinner(self) -> None:
        """Hide the animated loading indicator."""
        try:
            self.query_one("#llm-spinner").remove_class("active")
        except Exception:
            pass

    def _refresh_preview(self) -> None:
        """Update the preview pane with current form values."""
        try:
            preview = self.query_one("#preview-pane", PreviewPane)
            values = self._get_form_values()
            preview.update_values(values)
        except Exception:
            pass  # not mounted yet

    def _get_form_values(self) -> dict[str, str]:
        form = self.query_one("#input-form", InputForm)
        return form.get_values()

    def _build_config(self):
        """Build a PromptSpecConfig, optionally loading YAML config."""
        from promptspec.controller import PromptSpecConfig

        if self._config_path and self._config_path.exists():
            return PromptSpecConfig.from_yaml(self._config_path)
        return PromptSpecConfig()

    @staticmethod
    def _load_vars(vars_path: Optional[Path]) -> dict[str, str]:
        """Load variables from a JSON file."""
        if vars_path is None or not vars_path.exists():
            return {}
        try:
            data = json.loads(vars_path.read_text())
            return {k: str(v) for k, v in data.items()}
        except Exception:
            return {}


def launch_tui(
    spec_path: Path,
    vars_path: Optional[Path] = None,
    config_path: Optional[Path] = None,
) -> None:
    """Entry point for --ui mode."""
    app = PromptSpecApp(
        spec_path=spec_path,
        vars_path=vars_path,
        config_path=config_path,
    )
    app.run()
