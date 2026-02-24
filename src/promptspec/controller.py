"""PromptSpec controller — orchestrates prompt composition via LLM tool calling."""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from ellements.core import LLMClient, ToolCallResponse

logger = logging.getLogger(__name__)

# Path to the system prompt shipped with the package
_SYSTEM_PROMPT_PATH = (
    Path(__file__).resolve().parent
    / "prompts"
    / "prompt-composition-helper.system.md"
)

# Tool definitions in OpenAI function-calling format
TOOLS: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": (
                "Read the content of a file from the filesystem. "
                "Use this when a directive like @refine references an external file."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "file_name": {
                        "type": "string",
                        "description": "Path to the file to read (relative to the spec's directory)",
                    }
                },
                "required": ["file_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "log_transition",
            "description": (
                "Log a composition transition. Call this exactly once after each "
                "iteration pass to record what changed and why."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": (
                            "Free-form description of what changed and why. "
                            "If nothing changed, use 'no change' with a brief reason."
                        ),
                    }
                },
                "required": ["text"],
            },
        },
    },
]


@dataclass
class CompositionResult:
    """Result of a prompt composition run."""

    composed_prompt: str
    prompts: Dict[str, str] = field(default_factory=dict)
    prompt_roles: Dict[str, str] = field(default_factory=dict)
    raw_xml: str = ""
    analysis: str = ""
    tools: List[Dict[str, Any]] = field(default_factory=list)
    execution: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    transitions: List[str] = field(default_factory=list)
    tool_calls_made: int = 0

    @property
    def issues(self) -> List[Dict[str, str]]:
        """Backward-compatible list of all issues."""
        result: List[Dict[str, str]] = []
        for w in self.warnings:
            result.append({"type": "warning", "message": w})
        for e in self.errors:
            result.append({"type": "error", "message": e})
        for s in self.suggestions:
            result.append({"type": "suggestion", "message": s})
        return result

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "composed_prompt": self.composed_prompt,
            "raw_xml": self.raw_xml,
            "analysis": self.analysis,
            "warnings": self.warnings,
            "errors": self.errors,
            "suggestions": self.suggestions,
            "transitions": self.transitions,
            "tool_calls_made": self.tool_calls_made,
        }
        if self.prompts:
            d["prompts"] = self.prompts
        if self.tools:
            d["tools"] = self.tools
        if self.execution:
            d["execution"] = self.execution
        return d


def _extract_tag(text: str, tag: str) -> str:
    """Extract content between <tag> and </tag>, or return empty string."""
    pattern = re.compile(
        rf"<{re.escape(tag)}>\s*(.*?)\s*</{re.escape(tag)}>",
        re.DOTALL,
    )
    m = pattern.search(text)
    return m.group(1).strip() if m else ""


def _parse_issue_lines(block: str) -> List[str]:
    """Parse a warnings/errors/suggestions block into individual items."""
    if not block:
        return []
    items: List[str] = []
    for line in block.splitlines():
        line = line.strip()
        if not line:
            continue
        # Strip leading "- " or "* " or numbered "1. "
        line = re.sub(r"^[-*]\s+", "", line)
        line = re.sub(r"^\d+\.\s+", "", line)
        # Strip leading label like "Warning 1: " or "Error: "
        line = re.sub(r"^(Warning|Error|Suggestion)\s*\d*:\s*", "", line, flags=re.IGNORECASE)
        if line:
            items.append(line)
    return items


def _parse_tools_json(block: str) -> List[Dict[str, Any]]:
    """Parse the <tools> block — expects a JSON array of tool definitions."""
    if not block or not block.strip():
        return []
    try:
        parsed = json.loads(block)
        if isinstance(parsed, list):
            return parsed
        return []
    except json.JSONDecodeError:
        logger.warning("Failed to parse <tools> JSON: %s", block[:200])
        return []


def _parse_json_object(block: str, tag_name: str) -> Dict[str, Any]:
    """Parse a JSON object from an XML tag block."""
    if not block or not block.strip():
        return {}
    try:
        parsed = json.loads(block)
        if isinstance(parsed, dict):
            return parsed
        return {}
    except json.JSONDecodeError:
        logger.warning("Failed to parse <%s> JSON: %s", tag_name, block[:200])
        return {}


def parse_composition_xml(raw: str) -> CompositionResult:
    """Parse the XML-structured LLM output into a CompositionResult.

    Handles both well-formed ``<output>…</output>`` responses and
    fallback cases where the model returns plain text.
    Also handles XML wrapped in markdown code fences.
    """
    # Strip markdown code fences if present (```xml ... ```)
    cleaned = re.sub(r"```(?:xml)?\s*\n?", "", raw)

    # Try to find the <output> envelope
    output_block = _extract_tag(cleaned, "output")
    if not output_block:
        # Fallback: no XML structure — treat entire response as prompt
        return CompositionResult(composed_prompt=raw.strip(), raw_xml=raw)

    prompt = _extract_tag(output_block, "prompt")
    raw_prompts = _parse_json_object(_extract_tag(output_block, "prompts"), "prompts")

    # Normalise prompts: support both {"name": "text"} and {"name": {"text": "...", "role": "..."}}
    prompts: Dict[str, str] = {}
    prompt_roles: Dict[str, str] = {}
    for name, value in raw_prompts.items():
        if isinstance(value, dict):
            prompts[name] = value.get("text", "")
            if "role" in value:
                prompt_roles[name] = value["role"]
        else:
            prompts[name] = str(value)

    tools = _parse_tools_json(_extract_tag(output_block, "tools"))
    execution = _parse_json_object(_extract_tag(output_block, "execution"), "execution")
    analysis = _extract_tag(output_block, "analysis")
    warnings = _parse_issue_lines(_extract_tag(output_block, "warnings"))
    errors = _parse_issue_lines(_extract_tag(output_block, "errors"))
    suggestions = _parse_issue_lines(_extract_tag(output_block, "suggestions"))

    # If no <prompts> was emitted, default to {"default": prompt}
    if not prompts and prompt:
        prompts = {"default": prompt}

    return CompositionResult(
        composed_prompt=prompt,
        prompts=prompts,
        prompt_roles=prompt_roles,
        raw_xml=raw.strip(),
        analysis=analysis,
        tools=tools,
        execution=execution,
        warnings=warnings,
        errors=errors,
        suggestions=suggestions,
    )


@dataclass
class PromptSpecConfig:
    """Configuration for the PromptSpec controller."""

    model: str = "gpt-4.1"
    temperature: float = 0.3
    max_iterations: int = 15


class PromptSpecController:
    """Orchestrates prompt composition using LLM tool calling.

    Loads the prompt-composition-helper system prompt, sends the user's
    spec + variables, and lets the LLM drive the composition loop
    (calling ``read_file`` and ``log_transition`` as needed).
    """

    def __init__(
        self,
        config: Optional[PromptSpecConfig] = None,
        *,
        client: Optional[LLMClient] = None,
    ) -> None:
        self.config = config or PromptSpecConfig()
        self.client = client or LLMClient(default_model=self.config.model)
        self._system_prompt = _SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")

    async def compose(
        self,
        spec_text: str,
        variables: Optional[Dict[str, Any]] = None,
        base_dir: Optional[Path] = None,
        on_event: Optional[Callable[[str, Dict[str, Any]], None]] = None,
    ) -> CompositionResult:
        """Compose a prompt from *spec_text* and *variables*.

        Args:
            spec_text: The prompt specification (Markdown with directives).
            variables: Variable values to substitute (``{{name}}`` → value).
            base_dir: Base directory for resolving ``@refine <file>`` paths.
                      Defaults to the current working directory.
            on_event: Optional callback ``(event_type, data)`` for UI updates.
                      Event types: ``"tool_call"``, ``"tool_result"``,
                      ``"transition"``, ``"issue"``, ``"composing"``, ``"done"``.

        Returns:
            A :class:`CompositionResult` with the final prompt and any
            issues logged during processing.
        """
        base_dir = Path(base_dir) if base_dir else Path.cwd()

        def _emit(event: str, data: Dict[str, Any]) -> None:
            if on_event:
                on_event(event, data)

        # Collect transitions from log_transition tool calls
        transitions: List[str] = []

        # Build the user message
        vars_section = ""
        if variables:
            lines = [f"- `{k}`: {v}" for k, v in variables.items()]
            vars_section = "\n".join(lines)
        else:
            vars_section = "No variables provided."

        user_message = (
            "# Current State\n\n"
            "## Current Prompt Specification\n\n"
            f"```\n{spec_text}\n```\n\n"
            "## Current Variables\n\n"
            f"{vars_section}\n\n"
            "## Task\n\n"
            "Process the prompt specification above by following the Composition Flow exactly:\n"
            "1. Substitute ALL variable placeholders (`{{variable}}`, `@variable`, `@{variable}`) with their values.\n"
            "2. Resolve ALL directives — process innermost nested directives first (inside-out), "
            "then apply outer directives to the result. "
            "This includes `@refine`, `@match`, `@if`/`@else`, `@note`, `@revise`, `@canon`, "
            "`@cohere`, `@audience`, `@style`, `@summarize`, `@compress`, `@extract`, "
            "`@generate_examples`, `@output_format`, `@structural_constraints`, `@assert`, "
            "`@prompt`, `@execute`, `@tool`, "
            "and debug queries (`@directives?`, `@vars?`, `@structure?`).\n"
            "3. After each iteration pass, call `log_transition(text)` exactly once.\n"
            "4. Unescape `@@` → `@`.\n\n"
            "**CRITICAL**: The `<prompt>` in your output must contain ONLY the final, "
            "fully-resolved prompt text. It must NOT contain any raw directive syntax "
            "(`@directive`, `==>`, `{{...}}`). "
            "These are instructions for you to execute, not content to pass through.\n\n"
            "## Output Format (MANDATORY)\n\n"
            "You MUST wrap your entire response in the following XML structure. "
            "Do NOT output anything outside the `<output>` tags.\n\n"
            "```\n"
            "<output>\n"
            "  <prompt>\n"
            "    (the fully composed prompt goes here)\n"
            "  </prompt>\n"
            "  <prompts>\n"
            '    (a JSON object mapping prompt names to composed text, e.g. {"default": "..."} or {"generate": "...", "evaluate": "..."}. '
            'When any @prompt has a role parameter, use object values: {"generate": {"text": "...", "role": "user"}, "evaluate": {"text": "...", "role": "system"}})\n'
            "  </prompts>\n"
            "  <tools>\n"
            "    (a JSON array of tool definitions from @tool directives, or [] if none)\n"
            "  </tools>\n"
            "  <execution>\n"
            "    (a JSON object with execution strategy metadata from @execute, or {} if none)\n"
            "  </execution>\n"
            "  <analysis>\n"
            "    (brief high-level rationale for what changed and why; may be empty)\n"
            "  </analysis>\n"
            "  <warnings>\n"
            "    - (any warnings, or leave empty if none)\n"
            "  </warnings>\n"
            "  <errors>\n"
            "    - (any errors, or leave empty if none)\n"
            "  </errors>\n"
            "  <suggestions>\n"
            "    - (any suggestions, or leave empty if none)\n"
            "  </suggestions>\n"
            "</output>\n"
            "```"
        )

        messages = [
            {"role": "system", "content": self._system_prompt},
            {"role": "user", "content": user_message},
        ]

        # Tool executor callback
        async def tool_executor(name: str, args: Dict[str, Any]) -> str:
            _emit("tool_call", {"name": name, "args": args})
            if name == "read_file":
                result_str = self._read_file(args["file_name"], base_dir)
                _emit("tool_result", {
                    "name": name,
                    "file": args["file_name"],
                    "size": len(result_str),
                    "error": result_str.startswith("Error:"),
                })
                return result_str
            elif name == "log_transition":
                text = args.get("text", "")
                transitions.append(text)
                _emit("transition", {"text": text, "step": len(transitions)})
                return "Transition logged."
            else:
                return f"Unknown tool: {name}"

        _emit("composing", {
            "model": self.config.model,
            "num_variables": len(variables) if variables else 0,
            "spec_length": len(spec_text),
        })

        response: ToolCallResponse = await self.client.complete_with_tools(
            messages=messages,
            tools=TOOLS,
            tool_executor=tool_executor,
            model=self.config.model,
            temperature=self.config.temperature,
            max_iterations=self.config.max_iterations,
        )

        result = parse_composition_xml(response.content)
        result.tool_calls_made = len(response.tool_calls_made)
        result.transitions = transitions

        # Emit individual issues so verbose UI shows them inline
        for issue in result.issues:
            _emit("issue", issue)

        _emit("done", {
            "tool_calls_made": result.tool_calls_made,
            "issues_count": len(result.issues),
            "output_length": len(result.composed_prompt),
        })
        return result

    # ------------------------------------------------------------------
    # Primitive helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _read_file(file_name: str, base_dir: Path) -> str:
        """Read a file relative to *base_dir*."""
        path = (base_dir / file_name).resolve()
        # Basic security: prevent traversal outside base_dir
        if not str(path).startswith(str(base_dir.resolve())):
            return f"Error: path '{file_name}' escapes the base directory."
        if not path.is_file():
            return f"Error: file '{file_name}' not found."
        try:
            return path.read_text(encoding="utf-8")
        except Exception as exc:
            return f"Error reading '{file_name}': {exc}"
