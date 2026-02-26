"""EditScreen — modal for collaborative editing rounds.

Displayed when a collaborative strategy needs user input. The user
can review the LLM-generated text in a full TextArea (with mouse
click-to-position), edit it, then choose an action:

  ✓ Approve   — accept the text unchanged
  ✏ Submit    — send the edited version back to the LLM
  🏁 Done     — signal that the collaboration is finished
  ✗ Abort     — cancel the collaboration entirely
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Static, TextArea


@dataclass
class EditResult:
    """Result returned by EditScreen."""

    text: str
    action: str  # "approve", "submit", "done", "abort"
    message: str = ""  # optional instruction to the LLM


class EditScreen(ModalScreen[EditResult]):
    """Modal screen for reviewing and editing collaborative content."""

    DEFAULT_CSS = """
    EditScreen {
        align: center middle;
    }

    #edit-container {
        width: 90%;
        height: 90%;
        border: thick $primary;
        background: $surface;
        padding: 1 2;
    }

    #edit-header {
        height: auto;
        margin-bottom: 1;
    }

    #edit-title {
        text-style: bold;
        color: $primary;
    }

    #edit-context {
        color: $text-muted;
        text-style: italic;
        height: auto;
    }

    #edit-area {
        height: 1fr;
        margin-bottom: 1;
    }

    #edit-buttons {
        height: auto;
        layout: horizontal;
        align: center middle;
    }

    #edit-buttons Button {
        margin: 0 1;
        min-width: 16;
    }

    #btn-approve {
        background: $success;
        color: $text;
    }

    #btn-submit {
        background: $primary;
        color: #1A1612;
        text-style: bold;
    }

    #btn-done {
        background: $secondary;
        color: #1A1612;
    }

    #btn-abort {
        background: $error;
        color: $text;
    }

    #edit-hints {
        height: 1;
        color: $text-muted;
        text-align: center;
        margin-top: 1;
    }

    #msg-bar {
        height: auto;
        margin-bottom: 1;
    }

    #msg-bar.hidden {
        display: none;
    }

    #msg-input {
        height: 3;
        margin-top: 0;
    }

    #msg-label {
        height: 1;
        color: $text-muted;
        text-style: italic;
    }

    #btn-toggle-msg {
        min-width: 28;
        margin: 0 1;
    }
    """

    BINDINGS = [
        Binding("escape", "approve", "Approve (no changes)", show=True),
        Binding("ctrl+s", "submit", "Submit edit", show=True),
        Binding("ctrl+m", "toggle_message", "Message to AI", show=True),
    ]

    def __init__(
        self,
        content: str,
        context: str = "",
        done_signal: str = "DONE",
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self._content = content
        self._edit_context = context
        self._done_signal = done_signal

    def compose(self) -> ComposeResult:
        with Vertical(id="edit-container"):
            with Vertical(id="edit-header"):
                yield Static(
                    "✏️  [bold]Collaborative Editing[/bold]",
                    id="edit-title",
                    markup=True,
                )
                if self._edit_context:
                    yield Static(
                        f"[italic]{self._edit_context}[/italic]",
                        id="edit-context",
                        markup=True,
                    )

            yield TextArea(self._content, id="edit-area")

            with Vertical(id="msg-bar", classes="hidden"):
                yield Static("💬 Message to AI:", id="msg-label", markup=True)
                yield Input(
                    placeholder="Tell the AI what to do with your edits…",
                    id="msg-input",
                )

            yield Static(
                "[dim]Escape = Approve unchanged  •  Ctrl+S = Submit edit[/dim]",
                id="edit-hints",
                markup=True,
            )

            with Horizontal(id="edit-buttons"):
                yield Button("✓ Approve", id="btn-approve", variant="success")
                yield Button("✏ Submit Edit", id="btn-submit", variant="primary")
                yield Button("💬 Message", id="btn-toggle-msg", variant="default")
                yield Button("🏁 Done", id="btn-done", variant="warning")
                yield Button("✗ Abort", id="btn-abort", variant="error")

    def on_mount(self) -> None:
        """Focus the TextArea on mount."""
        self.query_one("#edit-area", TextArea).focus()

    # ── Button handlers ───────────────────────────────────────────

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-approve":
            self.action_approve()
        elif event.button.id == "btn-submit":
            self.action_submit()
        elif event.button.id == "btn-toggle-msg":
            self.action_toggle_message()
        elif event.button.id == "btn-done":
            self._finish_done()
        elif event.button.id == "btn-abort":
            self._finish_abort()

    # ── Actions ───────────────────────────────────────────────────

    def _get_user_message(self) -> str:
        """Get the optional user message, or empty string."""
        try:
            return self.query_one("#msg-input", Input).value.strip()
        except Exception:
            return ""

    def action_toggle_message(self) -> None:
        """Show or hide the message-to-AI input."""
        bar = self.query_one("#msg-bar")
        bar.toggle_class("hidden")
        if not bar.has_class("hidden"):
            self.query_one("#msg-input", Input).focus()

    def action_approve(self) -> None:
        """Return the original content unchanged."""
        self.dismiss(EditResult(text=self._content, action="approve", message=self._get_user_message()))

    def action_submit(self) -> None:
        """Return the edited content."""
        area = self.query_one("#edit-area", TextArea)
        self.dismiss(EditResult(text=area.text, action="submit", message=self._get_user_message()))

    def _finish_done(self) -> None:
        """Signal that collaboration is complete."""
        area = self.query_one("#edit-area", TextArea)
        text = area.text
        if not text.rstrip().endswith(self._done_signal):
            text = text.rstrip() + f"\n{self._done_signal}"
        self.dismiss(EditResult(text=text, action="done", message=self._get_user_message()))

    def _finish_abort(self) -> None:
        """Signal abort — return empty string."""
        self.dismiss(EditResult(text="", action="abort"))
