"""Reusable chat engine — multi-turn conversation with tool calling.

Uses the ellements ``LLMClient.complete_with_tools()`` pattern:
  - tools: list of OpenAI function-calling dicts
  - tool_executor: async (name, args) → str

The engine maintains conversation history and delegates rendering
to a pluggable ``ChatUI`` callback.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Dict, List, Optional, Protocol


class ChatUI(Protocol):
    """Protocol for chat UI renderers."""

    def show_assistant(self, text: str) -> None:
        """Display an assistant message."""
        ...

    def show_tool_call(self, name: str, args: Dict[str, Any]) -> None:
        """Display a tool call notification."""
        ...

    def show_thinking(self) -> None:
        """Show a 'thinking' indicator."""
        ...

    def hide_thinking(self) -> None:
        """Hide the thinking indicator."""
        ...

    def get_user_input(self) -> str:
        """Prompt the user for input. Return empty string to quit."""
        ...


@dataclass
class ChatEngine:
    """Multi-turn conversational engine with tool support.

    Parameters
    ----------
    system_prompt : str
        The system prompt for the conversation.
    tools : list
        OpenAI function-calling tool definitions.
    tool_executor : callable
        Async callback ``(name, args) → str`` for executing tools.
    ui : ChatUI
        UI renderer for displaying messages and getting input.
    model : str
        LLM model to use.
    history : list
        Conversation history (auto-managed).
    """

    system_prompt: str
    tools: List[Dict[str, Any]]
    tool_executor: Callable[[str, Dict[str, Any]], Awaitable[str]]
    ui: Any  # ChatUI protocol
    model: str = "gpt-4.1"
    history: List[Dict[str, Any]] = field(default_factory=list)

    async def run(self) -> Optional[str]:
        """Run the chat loop until the user quits or a tool signals exit.

        Returns
        -------
        str or None
            If a tool raises an exception to signal exit (e.g. SpecSelected),
            the exception is propagated. Otherwise returns None on normal exit.
        """
        from ellements.core.clients import LLMClient

        client = LLMClient(model=self.model, temperature=0.3)

        # Initialize with system prompt
        if not self.history:
            self.history.append({"role": "system", "content": self.system_prompt})

        while True:
            # Get user input
            user_input = self.ui.get_user_input()
            if not user_input:
                break

            self.history.append({"role": "user", "content": user_input})

            # Show thinking
            self.ui.show_thinking()

            try:
                response = await client.complete_with_tools(
                    messages=self.history,
                    tools=self.tools,
                    tool_executor=self._wrapped_executor,
                )
            finally:
                self.ui.hide_thinking()

            # Add assistant response to history
            assistant_text = response.text
            self.history.append({"role": "assistant", "content": assistant_text})

            # Show the response
            self.ui.show_assistant(assistant_text)

        return None

    async def _wrapped_executor(self, name: str, args: Dict[str, Any]) -> str:
        """Wrap the tool executor to show tool calls in the UI."""
        self.ui.show_tool_call(name, args)
        return await self.tool_executor(name, args)
