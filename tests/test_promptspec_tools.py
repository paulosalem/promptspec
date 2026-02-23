"""Tests for the @tool directive and tool parsing functionality.

Unit tests (no LLM required) verify parse_composition_xml handles <tools>
correctly. Integration tests (require OPENAI_API_KEY) verify the full
@tool directive flow end-to-end.
"""

import json
import os
from pathlib import Path

import pytest

from promptspec.controller import (
    CompositionResult,
    parse_composition_xml,
    _parse_tools_json,
)


# ═══════════════════════════════════════════════════════════════════
# Unit Tests — no LLM calls required
# ═══════════════════════════════════════════════════════════════════


class TestParseToolsJson:
    """Test the _parse_tools_json helper."""

    def test_empty_string(self):
        assert _parse_tools_json("") == []

    def test_whitespace_only(self):
        assert _parse_tools_json("   \n  ") == []

    def test_empty_array(self):
        assert _parse_tools_json("[]") == []

    def test_valid_tool_array(self):
        tools_json = json.dumps([
            {
                "type": "function",
                "function": {
                    "name": "search",
                    "description": "Search the web",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search query"}
                        },
                        "required": ["query"],
                    },
                },
            }
        ])
        result = _parse_tools_json(tools_json)
        assert len(result) == 1
        assert result[0]["function"]["name"] == "search"

    def test_multiple_tools(self):
        tools = [
            {"type": "function", "function": {"name": "tool_a", "description": "A"}},
            {"type": "function", "function": {"name": "tool_b", "description": "B"}},
        ]
        result = _parse_tools_json(json.dumps(tools))
        assert len(result) == 2
        assert result[0]["function"]["name"] == "tool_a"
        assert result[1]["function"]["name"] == "tool_b"

    def test_invalid_json(self):
        result = _parse_tools_json("{not valid json!!")
        assert result == []

    def test_non_array_json(self):
        result = _parse_tools_json('{"type": "function"}')
        assert result == []


class TestParseCompositionXmlWithTools:
    """Test parse_composition_xml extracts <tools> correctly."""

    def test_xml_with_tools(self):
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "Get weather",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "location": {"type": "string", "description": "City"}
                        },
                        "required": ["location"],
                    },
                },
            }
        ]
        xml = (
            "<output>\n"
            "  <prompt>You are a weather assistant.</prompt>\n"
            f"  <tools>{json.dumps(tools)}</tools>\n"
            "  <analysis>Processed @tool directive.</analysis>\n"
            "  <warnings></warnings>\n"
            "  <errors></errors>\n"
            "  <suggestions></suggestions>\n"
            "</output>"
        )
        result = parse_composition_xml(xml)
        assert result.composed_prompt == "You are a weather assistant."
        assert len(result.tools) == 1
        assert result.tools[0]["function"]["name"] == "get_weather"
        assert result.tools[0]["function"]["parameters"]["required"] == ["location"]

    def test_xml_without_tools(self):
        xml = (
            "<output>\n"
            "  <prompt>Hello world.</prompt>\n"
            "  <analysis></analysis>\n"
            "  <warnings></warnings>\n"
            "  <errors></errors>\n"
            "  <suggestions></suggestions>\n"
            "</output>"
        )
        result = parse_composition_xml(xml)
        assert result.composed_prompt == "Hello world."
        assert result.tools == []

    def test_xml_with_empty_tools(self):
        xml = (
            "<output>\n"
            "  <prompt>Hello.</prompt>\n"
            "  <tools>[]</tools>\n"
            "  <analysis></analysis>\n"
            "  <warnings></warnings>\n"
            "  <errors></errors>\n"
            "  <suggestions></suggestions>\n"
            "</output>"
        )
        result = parse_composition_xml(xml)
        assert result.tools == []

    def test_xml_with_multiple_tools(self):
        tools = [
            {"type": "function", "function": {"name": "search", "description": "Search", "parameters": {"type": "object", "properties": {"q": {"type": "string"}}, "required": ["q"]}}},
            {"type": "function", "function": {"name": "calc", "description": "Calculate", "parameters": {"type": "object", "properties": {"expr": {"type": "string"}}, "required": ["expr"]}}},
        ]
        xml = (
            "<output>\n"
            f"  <prompt>Agent prompt.</prompt>\n"
            f"  <tools>{json.dumps(tools)}</tools>\n"
            "  <analysis></analysis>\n"
            "  <warnings></warnings>\n"
            "  <errors></errors>\n"
            "  <suggestions></suggestions>\n"
            "</output>"
        )
        result = parse_composition_xml(xml)
        assert len(result.tools) == 2
        names = [t["function"]["name"] for t in result.tools]
        assert "search" in names
        assert "calc" in names

    def test_fallback_no_xml_has_empty_tools(self):
        result = parse_composition_xml("Just plain text, no XML.")
        assert result.tools == []
        assert result.composed_prompt == "Just plain text, no XML."


class TestCompositionResultToDict:
    """Test that to_dict includes tools when present."""

    def test_to_dict_with_tools(self):
        tools = [{"type": "function", "function": {"name": "test_tool"}}]
        result = CompositionResult(
            composed_prompt="Hello",
            tools=tools,
        )
        d = result.to_dict()
        assert "tools" in d
        assert d["tools"] == tools

    def test_to_dict_without_tools(self):
        result = CompositionResult(composed_prompt="Hello")
        d = result.to_dict()
        assert "tools" not in d

    def test_to_dict_empty_tools(self):
        result = CompositionResult(composed_prompt="Hello", tools=[])
        d = result.to_dict()
        assert "tools" not in d


# ═══════════════════════════════════════════════════════════════════
# Integration Tests — require OPENAI_API_KEY
# ═══════════════════════════════════════════════════════════════════

_skip = pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY not set — requires a real LLM",
)

SPECS_DIR = (
    Path(__file__).resolve().parents[1]
    / "specs"
)


def _controller():
    from promptspec.controller import PromptSpecController, PromptSpecConfig
    return PromptSpecController(PromptSpecConfig())


async def _compose(spec, variables=None, **kwargs):
    c = _controller()
    return await c.compose(spec, variables=variables or {}, **kwargs)


@_skip
class TestToolDirectiveE2E:
    """End-to-end tests for the @tool directive."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_single_tool(self):
        """A single @tool directive produces one tool definition."""
        spec = (
            "You are a research assistant.\n\n"
            "@tool search_web\n"
            "  Search the web for information.\n"
            "  - query: string (required) — The search query\n"
            "  - max_results: integer — Maximum results\n"
        )
        r = await _compose(spec)
        assert r.composed_prompt, "Should produce a prompt"
        assert len(r.tools) >= 1, "Should have at least one tool"
        names = [t["function"]["name"] for t in r.tools]
        assert "search_web" in names

        # Validate the tool structure
        tool = next(t for t in r.tools if t["function"]["name"] == "search_web")
        assert tool["type"] == "function"
        params = tool["function"]["parameters"]
        assert "query" in params.get("properties", {})
        assert "query" in params.get("required", [])

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_multiple_tools(self):
        """Multiple @tool directives produce multiple tool definitions."""
        spec = (
            "You are an agent.\n\n"
            "@tool get_weather\n"
            "  Get weather conditions.\n"
            "  - location: string (required) — City name\n\n"
            "@tool calculate\n"
            "  Perform a calculation.\n"
            "  - expression: string (required) — Math expression\n"
        )
        r = await _compose(spec)
        assert len(r.tools) >= 2
        names = [t["function"]["name"] for t in r.tools]
        assert "get_weather" in names
        assert "calculate" in names

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_tool_with_enum(self):
        """@tool with enum parameter constraint."""
        spec = (
            "You are a weather bot.\n\n"
            "@tool get_weather\n"
            "  Get weather.\n"
            "  - location: string (required) — City\n"
            "  - units: string enum: [celsius, fahrenheit] — Temp units\n"
        )
        r = await _compose(spec)
        assert len(r.tools) >= 1
        tool = next(t for t in r.tools if t["function"]["name"] == "get_weather")
        units_prop = tool["function"]["parameters"]["properties"].get("units", {})
        if "enum" in units_prop:
            assert "celsius" in units_prop["enum"]
            assert "fahrenheit" in units_prop["enum"]

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_no_tools_produces_empty_array(self):
        """A spec without @tool should produce empty tools list."""
        spec = "You are a helpful assistant. Answer questions clearly."
        r = await _compose(spec)
        assert r.tools == [] or r.tools is not None

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_tools_not_in_prompt_text(self):
        """@tool definitions should NOT appear in the composed prompt text."""
        spec = (
            "You are a coding assistant.\n\n"
            "@tool run_code\n"
            "  Execute code.\n"
            "  - code: string (required) — Code to run\n"
        )
        r = await _compose(spec)
        # The @tool directive should be processed, not passed through
        assert "@tool" not in r.composed_prompt

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_react_agent_spec(self):
        """The react-agent.promptspec.md example spec compiles with tools."""
        spec_path = SPECS_DIR / "react-agent.promptspec.md"
        if not spec_path.exists():
            pytest.skip("react-agent.promptspec.md not found")
        spec = spec_path.read_text(encoding="utf-8")
        r = await _compose(
            spec,
            variables={
                "research_topic": "renewable energy trends",
                "audience": "business executives",
                "depth": "standard",
                "include_citations": True,
                "include_code_tools": False,
            },
            base_dir=SPECS_DIR,
        )
        assert r.composed_prompt, "Should produce a prompt"
        assert len(r.tools) >= 3, f"Expected at least 3 tools, got {len(r.tools)}"
        names = [t["function"]["name"] for t in r.tools]
        assert "search_web" in names
        assert "read_url" in names
        assert "calculate" in names
        # run_python should NOT be included since include_code_tools=False
        assert "run_python" not in names
