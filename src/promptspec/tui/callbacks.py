"""TUI-based EditCallback for collaborative editing in the Textual app.

When a collaborative strategy calls ``request_edit()``, this callback
pushes an :class:`EditScreen` modal and waits for the user to review,
edit, approve, or abort via the TUI.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from promptspec.tui.screens.edit import EditResult, EditScreen

if TYPE_CHECKING:
    from textual.app import App


class TuiEditCallback:
    """EditCallback that uses the Textual TUI for collaborative editing.

    Compatible with the ``EditCallback`` protocol from
    ``ellements.patterns.callbacks``.  Pass this as ``edit_callback``
    in engine config when running collaborative specs in ``--ui`` mode.
    """

    def __init__(self, app: App, done_signal: str = "DONE") -> None:
        self._app = app
        self._done_signal = done_signal
        self._round = 0

    async def request_edit(self, content: str, context: str = "") -> str:
        """Push a modal EditScreen and wait for the user's response."""
        self._round += 1
        ctx = context or f"Round {self._round} — Review the AI-generated text and edit as needed."

        future: asyncio.Future[EditResult] = asyncio.get_running_loop().create_future()

        def _on_dismiss(result: EditResult | None) -> None:
            if result is None:
                # Screen dismissed without result → treat as approve
                future.set_result(EditResult(text=content, action="approve"))
            else:
                future.set_result(result)

        screen = EditScreen(
            content=content,
            context=ctx,
            done_signal=self._done_signal,
        )
        self._app.push_screen(screen, callback=_on_dismiss)

        result = await future
        return result.text
