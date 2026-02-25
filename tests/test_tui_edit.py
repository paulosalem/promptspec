"""Pilot tests for EditScreen and TuiEditCallback."""

from __future__ import annotations

import asyncio

import pytest
from textual.app import App, ComposeResult
from textual.widgets import Button, Static, TextArea

from promptspec.tui.screens.edit import EditResult, EditScreen
from promptspec.tui.callbacks import TuiEditCallback


SAMPLE_CONTENT = "This is AI-generated text.\nSecond paragraph."


class _EditApp(App):
    """App that pushes an EditScreen on mount and exits on dismiss."""

    def __init__(self, content: str = SAMPLE_CONTENT, context: str = "",
                 done_signal: str = "DONE", **kwargs):
        super().__init__(**kwargs)
        self._content = content
        self._ctx = context
        self._done_signal = done_signal
        self.edit_result: EditResult | None = None

    def compose(self) -> ComposeResult:
        yield Static("host")

    def on_mount(self) -> None:
        self.push_screen(
            EditScreen(
                content=self._content,
                context=self._ctx,
                done_signal=self._done_signal,
            ),
            callback=self._on_edit_done,
        )

    def _on_edit_done(self, result: EditResult) -> None:
        self.edit_result = result
        self.exit()


# ═══════════════════════════════════════════════════════════════════
# Tests: EditScreen mounting
# ═══════════════════════════════════════════════════════════════════

class TestEditScreenMounting:
    """Verify EditScreen mounts and renders correctly."""

    @pytest.mark.asyncio
    async def test_screen_has_textarea(self):
        app = _EditApp()
        async with app.run_test(size=(100, 40)) as pilot:
            await pilot.pause()
            area = app.screen.query_one("#edit-area", TextArea)
            assert area is not None
            await pilot.press("escape")  # dismiss so app exits

    @pytest.mark.asyncio
    async def test_textarea_prefilled(self):
        app = _EditApp()
        async with app.run_test(size=(100, 40)) as pilot:
            await pilot.pause()
            area = app.screen.query_one("#edit-area", TextArea)
            assert area.text == SAMPLE_CONTENT
            await pilot.press("escape")

    @pytest.mark.asyncio
    async def test_context_displayed(self):
        app = _EditApp(context="Round 3 — Edit as needed")
        async with app.run_test(size=(100, 40)) as pilot:
            await pilot.pause()
            ctx = app.screen.query_one("#edit-context", Static)
            assert ctx is not None
            await pilot.press("escape")

    @pytest.mark.asyncio
    async def test_no_context_element_when_empty(self):
        app = _EditApp(context="")
        async with app.run_test(size=(100, 40)) as pilot:
            await pilot.pause()
            results = app.screen.query("#edit-context")
            assert len(results) == 0
            await pilot.press("escape")

    @pytest.mark.asyncio
    async def test_four_buttons_present(self):
        app = _EditApp()
        async with app.run_test(size=(100, 40)) as pilot:
            await pilot.pause()
            s = app.screen
            assert s.query_one("#btn-approve", Button)
            assert s.query_one("#btn-submit", Button)
            assert s.query_one("#btn-done", Button)
            assert s.query_one("#btn-abort", Button)
            await pilot.press("escape")

    @pytest.mark.asyncio
    async def test_title_present(self):
        app = _EditApp()
        async with app.run_test(size=(100, 40)) as pilot:
            await pilot.pause()
            title = app.screen.query_one("#edit-title", Static)
            assert title is not None
            await pilot.press("escape")


# ═══════════════════════════════════════════════════════════════════
# Tests: EditScreen actions
# ═══════════════════════════════════════════════════════════════════

class TestEditScreenActions:
    """Verify each button returns the correct EditResult."""

    @pytest.mark.asyncio
    async def test_approve_returns_original(self):
        app = _EditApp()
        async with app.run_test(size=(100, 40)) as pilot:
            await pilot.pause()
            app.screen.query_one("#btn-approve", Button).press()
            await pilot.pause()
        assert app.edit_result is not None
        assert app.edit_result.action == "approve"
        assert app.edit_result.text == SAMPLE_CONTENT

    @pytest.mark.asyncio
    async def test_submit_returns_edited_text(self):
        app = _EditApp()
        async with app.run_test(size=(100, 40)) as pilot:
            await pilot.pause()
            area = app.screen.query_one("#edit-area", TextArea)
            area.load_text("Edited content here.")
            await pilot.pause()
            app.screen.query_one("#btn-submit", Button).press()
            await pilot.pause()
        assert app.edit_result is not None
        assert app.edit_result.action == "submit"
        assert app.edit_result.text == "Edited content here."

    @pytest.mark.asyncio
    async def test_abort_returns_empty(self):
        app = _EditApp()
        async with app.run_test(size=(100, 40)) as pilot:
            await pilot.pause()
            app.screen.query_one("#btn-abort", Button).press()
            await pilot.pause()
        assert app.edit_result is not None
        assert app.edit_result.action == "abort"
        assert app.edit_result.text == ""

    @pytest.mark.asyncio
    async def test_done_appends_signal(self):
        app = _EditApp()
        async with app.run_test(size=(100, 40)) as pilot:
            await pilot.pause()
            app.screen.query_one("#btn-done", Button).press()
            await pilot.pause()
        assert app.edit_result is not None
        assert app.edit_result.action == "done"
        assert app.edit_result.text.rstrip().endswith("DONE")

    @pytest.mark.asyncio
    async def test_done_doesnt_duplicate_signal(self):
        content_with_done = SAMPLE_CONTENT + "\nDONE"
        app = _EditApp(content=content_with_done)
        async with app.run_test(size=(100, 40)) as pilot:
            await pilot.pause()
            app.screen.query_one("#btn-done", Button).press()
            await pilot.pause()
        assert app.edit_result is not None
        assert app.edit_result.text.count("DONE") == 1

    @pytest.mark.asyncio
    async def test_escape_approves(self):
        app = _EditApp()
        async with app.run_test(size=(100, 40)) as pilot:
            await pilot.pause()
            await pilot.press("escape")
            await pilot.pause()
        assert app.edit_result is not None
        assert app.edit_result.action == "approve"
        assert app.edit_result.text == SAMPLE_CONTENT


# ═══════════════════════════════════════════════════════════════════
# Tests: EditResult dataclass
# ═══════════════════════════════════════════════════════════════════

class TestEditResult:
    def test_dataclass_fields(self):
        r = EditResult(text="hello", action="submit")
        assert r.text == "hello"
        assert r.action == "submit"

    def test_approve_result(self):
        r = EditResult(text="content", action="approve")
        assert r.action == "approve"

    def test_abort_result(self):
        r = EditResult(text="", action="abort")
        assert r.text == ""


# ═══════════════════════════════════════════════════════════════════
# Tests: TuiEditCallback
# ═══════════════════════════════════════════════════════════════════

class TestTuiEditCallback:
    """Test the callback initialization."""

    def test_callback_init(self):
        callback = TuiEditCallback(app=None, done_signal="FINISH")
        assert callback._done_signal == "FINISH"
        assert callback._round == 0

    def test_round_starts_at_zero(self):
        callback = TuiEditCallback(app=None)
        assert callback._round == 0
