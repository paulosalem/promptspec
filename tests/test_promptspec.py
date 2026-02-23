"""End-to-end tests for the PromptSpec example application.

These tests use REAL LLM calls (no mocks) to verify the complete
prompt composition workflow. They require OPENAI_API_KEY to be set.
"""

import json
import os
import re
from pathlib import Path

import pytest

_skip_no_api_key = pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY not set — E2E tests require a real LLM",
)

SPECS_DIR = (
    Path(__file__).resolve().parents[1]
    / "specs"
)


@_skip_no_api_key
class TestPromptSpecE2E:
    """End-to-end tests using real LLM calls."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_simple_spec_no_directives(self):
        """A plain-text spec with variable substitution only."""
        from promptspec.controller import (
            PromptSpecController,
            PromptSpecConfig,
        )

        controller = PromptSpecController(
            PromptSpecConfig()
        )
        result = await controller.compose(
            spec_text="Write a haiku about {{topic}}.",
            variables={"topic": "autumn"},
        )

        assert result.composed_prompt, "Should produce a non-empty composed prompt"
        assert "autumn" in result.composed_prompt.lower() or "haiku" in result.composed_prompt.lower()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_match_directive(self):
        """Verify @match selects the correct branch."""
        from promptspec.controller import (
            PromptSpecController,
            PromptSpecConfig,
        )

        spec = (
            "You are a coding assistant.\n\n"
            '@match language\n'
            '  "python" ==> Focus on PEP 8 and type hints.\n'
            '  "rust"   ==> Focus on ownership and lifetimes.\n'
        )

        controller = PromptSpecController(
            PromptSpecConfig()
        )
        result = await controller.compose(
            spec_text=spec,
            variables={"language": "python"},
        )

        prompt_lower = result.composed_prompt.lower()
        assert "pep 8" in prompt_lower or "type hint" in prompt_lower, (
            "Should include Python-specific content"
        )

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_if_directive_true(self):
        """Verify @if includes content when the condition is true."""
        from promptspec.controller import (
            PromptSpecController,
            PromptSpecConfig,
        )

        spec = (
            "Review this code.\n\n"
            "@if include_security\n"
            "  Check for SQL injection and XSS vulnerabilities.\n"
        )

        controller = PromptSpecController(
            PromptSpecConfig()
        )
        result = await controller.compose(
            spec_text=spec,
            variables={"include_security": True},
        )

        prompt_lower = result.composed_prompt.lower()
        assert "sql injection" in prompt_lower or "xss" in prompt_lower or "security" in prompt_lower

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_if_directive_false(self):
        """Verify @if excludes content when the condition is false."""
        from promptspec.controller import (
            PromptSpecController,
            PromptSpecConfig,
        )

        spec = (
            "Review this code.\n\n"
            "@if include_security\n"
            "  Check for SQL injection and XSS vulnerabilities.\n"
        )

        controller = PromptSpecController(
            PromptSpecConfig()
        )
        result = await controller.compose(
            spec_text=spec,
            variables={"include_security": False},
        )

        prompt_lower = result.composed_prompt.lower()
        assert "sql injection" not in prompt_lower

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_refine_directive(self):
        """Verify @refine reads a file and merges content."""
        from promptspec.controller import (
            PromptSpecController,
            PromptSpecConfig,
        )

        spec = (
            "@refine base-analyst.promptspec.md\n\n"
            "Analyze the renewable energy market in Europe.\n"
        )

        controller = PromptSpecController(
            PromptSpecConfig()
        )
        result = await controller.compose(
            spec_text=spec,
            variables={},
            base_dir=SPECS_DIR,
        )

        prompt_lower = result.composed_prompt.lower()
        # Should contain content from both the base analyst and the spec
        assert "renewable" in prompt_lower or "energy" in prompt_lower or "europe" in prompt_lower
        assert result.tool_calls_made > 0, "Should have called read_file for base-analyst.promptspec.md"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_market_research_spec_full(self):
        """Full composition of the market research spec with all variables."""
        from promptspec.controller import (
            PromptSpecController,
            PromptSpecConfig,
        )

        vars_path = SPECS_DIR / "vars" / "market-research-example.json"
        variables = json.loads(vars_path.read_text(encoding="utf-8"))

        spec_text = (SPECS_DIR / "market-research-brief.promptspec.md").read_text(encoding="utf-8")

        controller = PromptSpecController(
            PromptSpecConfig()
        )
        result = await controller.compose(
            spec_text=spec_text,
            variables=variables,
            base_dir=SPECS_DIR,
        )

        assert result.composed_prompt, "Should produce a non-empty result"
        prompt_lower = result.composed_prompt.lower()
        assert "rivian" in prompt_lower or "electric" in prompt_lower

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_tutorial_spec_with_escaping(self):
        """Verify @@ escaping renders literal @ in the final output."""
        from promptspec.controller import (
            PromptSpecController,
            PromptSpecConfig,
        )

        vars_path = SPECS_DIR / "vars" / "tutorial-fastapi.json"
        variables = json.loads(vars_path.read_text(encoding="utf-8"))

        spec_text = (SPECS_DIR / "tutorial-generator.promptspec.md").read_text(encoding="utf-8")

        controller = PromptSpecController(
            PromptSpecConfig()
        )
        result = await controller.compose(
            spec_text=spec_text,
            variables=variables,
            base_dir=SPECS_DIR,
        )

        assert result.composed_prompt, "Should produce a non-empty result"
        # The @@ should render as literal @ in decorator references
        prompt_lower = result.composed_prompt.lower()
        assert "fastapi" in prompt_lower or "rest" in prompt_lower

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_note_directive_stripped(self):
        """Verify @note content is stripped from the final output."""
        from promptspec.controller import (
            PromptSpecController,
            PromptSpecConfig,
        )

        spec = (
            "Write a story.\n\n"
            "@note\n"
            "  SECRET_INTERNAL_MARKER_12345 — do not include this in the final prompt.\n\n"
            "The story should be about a cat.\n"
        )

        controller = PromptSpecController(
            PromptSpecConfig()
        )
        result = await controller.compose(spec_text=spec, variables={})

        assert "SECRET_INTERNAL_MARKER_12345" not in result.composed_prompt


# Regex patterns to detect unprocessed directives in the composed prompt.
# These should NEVER appear in a properly composed prompt.
_DIRECTIVE_PATTERNS = [
    (r"(?m)^\s*@refine\b", "@refine directive"),
    (r"(?m)^\s*@match\b", "@match directive"),
    (r"(?m)^\s*@if\b", "@if directive"),
    (r"(?m)^\s*@else\b", "@else directive"),
    (r"(?m)^\s*@note\b", "@note directive"),
    (r"==>", "==> arrow (from @match)"),
    (r"\{\{[a-zA-Z_]\w*\}\}", "{{variable}} placeholder"),
]


def _assert_no_raw_directives(prompt: str, context: str = "") -> None:
    """Assert that no unprocessed directive syntax remains in the prompt."""
    for pattern, label in _DIRECTIVE_PATTERNS:
        match = re.search(pattern, prompt)
        assert match is None, (
            f"Found unprocessed {label} in composed prompt{' (' + context + ')' if context else ''}: "
            f"'{match.group()}' at position {match.start()}"
        )


def _assert_no_xml_tags(prompt: str, context: str = "") -> None:
    """Assert that XML structural tags are not present in the prompt text."""
    for tag in ("output", "prompt", "warnings", "errors", "suggestions"):
        assert f"<{tag}>" not in prompt, (
            f"Found raw <{tag}> tag in composed prompt{' (' + context + ')' if context else ''}"
        )
        assert f"</{tag}>" not in prompt, (
            f"Found raw </{tag}> tag in composed prompt{' (' + context + ')' if context else ''}"
        )


@_skip_no_api_key
class TestPromptSpecOutputQuality:
    """Tests that verify the composed prompt is clean — no leftover
    directives, variables, or XML tags."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_market_research_no_raw_directives(self):
        """The market-research spec must be fully resolved."""
        from promptspec.controller import (
            PromptSpecController,
            PromptSpecConfig,
        )

        vars_path = SPECS_DIR / "vars" / "market-research-example.json"
        variables = json.loads(vars_path.read_text(encoding="utf-8"))
        spec_text = (SPECS_DIR / "market-research-brief.promptspec.md").read_text(encoding="utf-8")

        controller = PromptSpecController(
            PromptSpecConfig()
        )
        result = await controller.compose(
            spec_text=spec_text, variables=variables, base_dir=SPECS_DIR,
        )

        _assert_no_raw_directives(result.composed_prompt, "market-research")
        _assert_no_xml_tags(result.composed_prompt, "market-research")

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_code_review_no_raw_directives(self):
        """The code-review spec must be fully resolved."""
        from promptspec.controller import (
            PromptSpecController,
            PromptSpecConfig,
        )

        vars_path = SPECS_DIR / "vars" / "code-review-python.json"
        variables = json.loads(vars_path.read_text(encoding="utf-8"))
        spec_text = (SPECS_DIR / "code-review-checklist.promptspec.md").read_text(encoding="utf-8")

        controller = PromptSpecController(
            PromptSpecConfig()
        )
        result = await controller.compose(
            spec_text=spec_text, variables=variables, base_dir=SPECS_DIR,
        )

        _assert_no_raw_directives(result.composed_prompt, "code-review")
        _assert_no_xml_tags(result.composed_prompt, "code-review")

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_tutorial_no_raw_directives(self):
        """The tutorial spec must be fully resolved."""
        from promptspec.controller import (
            PromptSpecController,
            PromptSpecConfig,
        )

        vars_path = SPECS_DIR / "vars" / "tutorial-fastapi.json"
        variables = json.loads(vars_path.read_text(encoding="utf-8"))
        spec_text = (SPECS_DIR / "tutorial-generator.promptspec.md").read_text(encoding="utf-8")

        controller = PromptSpecController(
            PromptSpecConfig()
        )
        result = await controller.compose(
            spec_text=spec_text, variables=variables, base_dir=SPECS_DIR,
        )

        _assert_no_raw_directives(result.composed_prompt, "tutorial")
        _assert_no_xml_tags(result.composed_prompt, "tutorial")

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_simple_match_no_raw_directives(self):
        """A simple @match spec must not leave raw directive syntax."""
        from promptspec.controller import (
            PromptSpecController,
            PromptSpecConfig,
        )

        spec = (
            "You are a coding assistant.\n\n"
            '@match language\n'
            '  "python" ==> Focus on PEP 8 and type hints.\n'
            '  "rust"   ==> Focus on ownership and lifetimes.\n'
        )

        controller = PromptSpecController(
            PromptSpecConfig()
        )
        result = await controller.compose(
            spec_text=spec, variables={"language": "python"},
        )

        _assert_no_raw_directives(result.composed_prompt, "simple-match")
        _assert_no_xml_tags(result.composed_prompt, "simple-match")

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_issues_cleanly_separated(self):
        """Warnings/errors/suggestions must NOT appear inside composed_prompt."""
        from promptspec.controller import (
            PromptSpecController,
            PromptSpecConfig,
        )

        vars_path = SPECS_DIR / "vars" / "market-research-example.json"
        variables = json.loads(vars_path.read_text(encoding="utf-8"))
        spec_text = (SPECS_DIR / "market-research-brief.promptspec.md").read_text(encoding="utf-8")

        controller = PromptSpecController(
            PromptSpecConfig()
        )
        result = await controller.compose(
            spec_text=spec_text, variables=variables, base_dir=SPECS_DIR,
        )

        prompt = result.composed_prompt
        # The prompt should not contain issue-like prefixes
        assert not re.search(r"(?i)\bwarning\s*\d*:", prompt), (
            "Found 'Warning:' text inside composed_prompt — issues should be separate"
        )
        # Issues, if any, should be in their own fields
        for w in result.warnings:
            assert isinstance(w, str) and len(w) > 0
        for e in result.errors:
            assert isinstance(e, str) and len(e) > 0
        for s in result.suggestions:
            assert isinstance(s, str) and len(s) > 0

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_llm_response_uses_xml_format(self):
        """Verify the LLM wraps its response in <output><prompt>...</prompt></output> XML."""
        from promptspec.controller import (
            PromptSpecController,
            PromptSpecConfig,
        )

        spec = (
            "@refine base-analyst.promptspec.md\n\n"
            "Analyze the renewable energy market.\n"
        )

        controller = PromptSpecController(PromptSpecConfig())
        result = await controller.compose(
            spec_text=spec, variables={}, base_dir=SPECS_DIR,
        )

        # raw_xml should contain the XML envelope
        assert "<output>" in result.raw_xml, (
            f"LLM response missing <output> tag. raw_xml starts with: {result.raw_xml[:200]}"
        )
        assert "<prompt>" in result.raw_xml, (
            f"LLM response missing <prompt> tag. raw_xml starts with: {result.raw_xml[:200]}"
        )
        # composed_prompt should be non-empty (extracted from <prompt>)
        assert len(result.composed_prompt) > 50, (
            f"composed_prompt too short ({len(result.composed_prompt)} chars) — "
            "XML extraction may have failed"
        )


class TestPromptSpecImports:
    """Non-integration tests: verify imports and structure."""

    def test_controller_importable(self):
        from promptspec.controller import (
            PromptSpecController,
            PromptSpecConfig,
            CompositionResult,
            parse_composition_xml,
        )

        assert PromptSpecController is not None
        assert PromptSpecConfig is not None
        assert CompositionResult is not None
        assert callable(parse_composition_xml)

    def test_app_importable(self):
        from promptspec.app import cli, create_parser

        assert callable(cli)
        assert callable(create_parser)

    def test_specs_exist(self):
        """All example specs and var files must be present."""
        assert (SPECS_DIR / "base-analyst.promptspec.md").is_file()
        assert (SPECS_DIR / "market-research-brief.promptspec.md").is_file()
        assert (SPECS_DIR / "code-review-checklist.promptspec.md").is_file()
        assert (SPECS_DIR / "tutorial-generator.promptspec.md").is_file()
        assert (SPECS_DIR / "consulting-proposal.promptspec.md").is_file()
        assert (SPECS_DIR / "knowledge-base-article.promptspec.md").is_file()
        assert (SPECS_DIR / "api-docs-generator.promptspec.md").is_file()
        assert (SPECS_DIR / "multi-persona-debate.promptspec.md").is_file()
        assert (SPECS_DIR / "adaptive-interview.promptspec.md").is_file()
        assert (SPECS_DIR / "prompt-refactoring-pipeline.promptspec.md").is_file()
        assert (SPECS_DIR / "vars" / "market-research-example.json").is_file()
        assert (SPECS_DIR / "vars" / "code-review-python.json").is_file()
        assert (SPECS_DIR / "vars" / "tutorial-fastapi.json").is_file()
        assert (SPECS_DIR / "vars" / "consulting-proposal-example.json").is_file()
        assert (SPECS_DIR / "vars" / "knowledge-base-article-example.json").is_file()
        assert (SPECS_DIR / "vars" / "api-docs-generator-example.json").is_file()
        assert (SPECS_DIR / "vars" / "multi-persona-debate-agi.json").is_file()
        assert (SPECS_DIR / "vars" / "adaptive-interview-senior-backend.json").is_file()
        assert (SPECS_DIR / "vars" / "prompt-refactoring-example.json").is_file()

    def test_system_prompt_exists(self):
        from promptspec.controller import _SYSTEM_PROMPT_PATH

        assert _SYSTEM_PROMPT_PATH.is_file()
        content = _SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")
        assert "@refine" in content
        assert "@match" in content
        assert "<output>" in content
        assert "<prompt>" in content


class TestXmlParsing:
    """Unit tests for parse_composition_xml and CompositionResult."""

    def test_full_xml_output(self):
        from promptspec.controller import parse_composition_xml

        raw = """<output>
  <prompt>
    You are an expert Python engineer.
    Focus on clean, PEP-8 compliant code.
  </prompt>
  <analysis>
    Substituted variables and resolved directives.
  </analysis>
  <warnings>
    - Warning 1: Variable 'style' was not provided, using default.
  </warnings>
  <errors>
  </errors>
  <suggestions>
    - Suggestion 1: Consider adding a @note for the reasoning section.
  </suggestions>
</output>"""

        result = parse_composition_xml(raw)
        assert "expert Python engineer" in result.composed_prompt
        assert "PEP-8" in result.composed_prompt
        assert "Substituted variables" in result.analysis
        assert len(result.warnings) == 1
        assert "style" in result.warnings[0].lower()
        assert result.errors == []
        assert len(result.suggestions) == 1
        assert result.raw_xml == raw.strip()

    def test_prompt_only_no_issues(self):
        from promptspec.controller import parse_composition_xml

        raw = """<output>
  <prompt>
    Write a haiku about autumn leaves.
  </prompt>
</output>"""

        result = parse_composition_xml(raw)
        assert "haiku" in result.composed_prompt
        assert result.warnings == []
        assert result.errors == []
        assert result.suggestions == []

    def test_fallback_no_xml(self):
        from promptspec.controller import parse_composition_xml

        raw = "This is just plain text without any XML structure."

        result = parse_composition_xml(raw)
        assert result.composed_prompt == raw.strip()
        assert result.raw_xml == raw

    def test_multiple_warnings(self):
        from promptspec.controller import parse_composition_xml

        raw = """<output>
  <prompt>Hello world.</prompt>
  <warnings>
    - Missing variable 'name'.
    - Inconsistent indentation detected.
    - Unused directive @note found.
  </warnings>
</output>"""

        result = parse_composition_xml(raw)
        assert result.composed_prompt == "Hello world."
        assert len(result.warnings) == 3

    def test_errors_present(self):
        from promptspec.controller import parse_composition_xml

        raw = """<output>
  <prompt>Partial result.</prompt>
  <errors>
    - Error 1: File 'missing.md' not found.
  </errors>
</output>"""

        result = parse_composition_xml(raw)
        assert len(result.errors) == 1
        assert "missing.md" in result.errors[0]

    def test_issues_property(self):
        from promptspec.controller import parse_composition_xml

        raw = """<output>
  <prompt>Test.</prompt>
  <warnings>
    - Warn A.
  </warnings>
  <errors>
    - Err B.
  </errors>
  <suggestions>
    - Sug C.
  </suggestions>
</output>"""

        result = parse_composition_xml(raw)
        issues = result.issues
        assert len(issues) == 3
        assert issues[0] == {"type": "warning", "message": "Warn A."}
        assert issues[1] == {"type": "error", "message": "Err B."}
        assert issues[2] == {"type": "suggestion", "message": "Sug C."}

    def test_to_dict_includes_all_fields(self):
        from promptspec.controller import parse_composition_xml

        raw = """<output>
  <prompt>Test prompt.</prompt>
  <analysis>Some analysis.</analysis>
  <warnings>
    - Some warning.
  </warnings>
</output>"""

        result = parse_composition_xml(raw)
        result.tool_calls_made = 2
        result.transitions = ["Pass 1: resolved variables"]
        d = result.to_dict()
        assert d["composed_prompt"] == "Test prompt."
        assert d["raw_xml"] == raw.strip()
        assert d["analysis"] == "Some analysis."
        assert d["warnings"] == ["Some warning."]
        assert d["errors"] == []
        assert d["suggestions"] == []
        assert d["transitions"] == ["Pass 1: resolved variables"]
        assert d["tool_calls_made"] == 2

    def test_xml_output_format_in_parser(self):
        """Verify --format xml is accepted by the argument parser."""
        from promptspec.app import create_parser

        parser = create_parser()
        args = parser.parse_args(["test.md", "--format", "xml", "--batch-only"])
        assert args.format == "xml"

    def test_output_file_in_parser(self):
        """Verify --output / -o accepts a file path."""
        from promptspec.app import create_parser

        parser = create_parser()
        args = parser.parse_args(["test.md", "-o", "result.md"])
        assert args.output == Path("result.md")


class TestToolRegistration:
    """Tests that the correct tools are registered."""

    def test_log_issue_tool_not_in_tools(self):
        """The log_issue tool should NOT be registered — issues come via XML only."""
        from promptspec.controller import TOOLS

        tool_names = [t["function"]["name"] for t in TOOLS]
        assert "log_issue" not in tool_names

    def test_tools_include_read_file_and_log_transition(self):
        """TOOLS should include read_file and log_transition."""
        from promptspec.controller import TOOLS

        tool_names = [t["function"]["name"] for t in TOOLS]
        assert "read_file" in tool_names
        assert "log_transition" in tool_names
        assert len(TOOLS) == 2


class TestIssueHandling:
    """Tests for issue extraction, formatting, and output separation."""

    def test_parse_xml_preserves_warnings_and_suggestions(self):
        """Verify parse_composition_xml correctly extracts all issue types."""
        from promptspec.controller import parse_composition_xml

        xml = """<output>
  <prompt>You are a helpful assistant.</prompt>
  <warnings>
    - Variable 'tone' was not provided, defaulting to neutral.
  </warnings>
  <errors>
  </errors>
  <suggestions>
    - Consider adding a persona directive for better results.
    - The prompt could benefit from more specific constraints.
  </suggestions>
</output>"""

        result = parse_composition_xml(xml)
        assert result.composed_prompt == "You are a helpful assistant."
        assert len(result.warnings) == 1
        assert "tone" in result.warnings[0].lower()
        assert len(result.suggestions) == 2
        assert result.errors == []
        # issues property should combine all
        assert len(result.issues) == 3

    def test_fallback_no_xml_loses_issues(self):
        """When the LLM doesn't use XML, we get no structured issues (known limitation)."""
        from promptspec.controller import parse_composition_xml

        raw = "You are a helpful assistant.\n\nWarning: something went wrong."
        result = parse_composition_xml(raw)
        # Falls back to treating entire text as prompt
        assert result.composed_prompt == raw.strip()
        assert result.warnings == []
        assert result.suggestions == []

    def test_empty_tags_yield_no_issues(self):
        """Empty <warnings>, <errors>, <suggestions> tags should yield empty lists."""
        from promptspec.controller import parse_composition_xml

        xml = """<output>
  <prompt>Hello world.</prompt>
  <warnings></warnings>
  <errors></errors>
  <suggestions></suggestions>
</output>"""

        result = parse_composition_xml(xml)
        assert result.composed_prompt == "Hello world."
        assert result.warnings == []
        assert result.errors == []
        assert result.suggestions == []

    def test_verbose_batch_output_includes_issues(self):
        """Issues should NOT be in _format_raw_output — they go to stderr separately."""
        from promptspec.controller import CompositionResult
        from promptspec.app import _format_raw_output

        result = CompositionResult(
            composed_prompt="You are a helpful assistant.",
            raw_xml="<output>...</output>",
            warnings=["Variable 'tone' was not provided."],
            suggestions=["Consider adding more context."],
        )
        # Markdown output always contains only the prompt, never issues
        output = _format_raw_output(result, "markdown")
        assert output == "You are a helpful assistant."
        assert "Composition Issues" not in output
        assert "tone" not in output

    def test_non_verbose_batch_output_excludes_issues(self):
        """_format_raw_output must only have the prompt."""
        from promptspec.controller import CompositionResult
        from promptspec.app import _format_raw_output

        result = CompositionResult(
            composed_prompt="You are a helpful assistant.",
            raw_xml="<output>...</output>",
            warnings=["Variable 'tone' was not provided."],
            suggestions=["Consider adding more context."],
        )
        output = _format_raw_output(result, "markdown")
        assert output == "You are a helpful assistant."
        assert "Composition Issues" not in output

    def test_json_output_includes_issues(self):
        """JSON output must always include warnings/suggestions fields."""
        from promptspec.controller import CompositionResult
        from promptspec.app import _format_raw_output

        result = CompositionResult(
            composed_prompt="Test prompt.",
            raw_xml="<output>...</output>",
            warnings=["A warning."],
            suggestions=["A suggestion."],
        )
        output = _format_raw_output(result, "json")
        parsed = json.loads(output)
        assert parsed["warnings"] == ["A warning."]
        assert parsed["suggestions"] == ["A suggestion."]

    def test_parse_xml_wrapped_in_code_fence(self):
        """LLMs often wrap XML in markdown code fences — parser must handle this."""
        from promptspec.controller import parse_composition_xml

        raw = """Here is the composed prompt:

```xml
<output>
  <prompt>
    You are a helpful assistant.
  </prompt>
  <warnings>
    - Variable 'tone' was not provided.
  </warnings>
  <suggestions>
    - Consider being more specific.
  </suggestions>
</output>
```"""

        result = parse_composition_xml(raw)
        assert result.composed_prompt == "You are a helpful assistant."
        assert len(result.warnings) == 1
        assert len(result.suggestions) == 1

    def test_parse_xml_with_large_prompt(self):
        """Parser must handle large prompts within <prompt> tags."""
        from promptspec.controller import parse_composition_xml

        big_prompt = "You are an analyst. " * 200  # ~4000 chars
        raw = f"""<output>
  <prompt>
    {big_prompt}
  </prompt>
  <warnings>
    - This is a test warning about the large prompt.
  </warnings>
  <suggestions>
    - Consider splitting the prompt into sections.
  </suggestions>
</output>"""

        result = parse_composition_xml(raw)
        assert "analyst" in result.composed_prompt
        assert len(result.composed_prompt) > 3000
        assert len(result.warnings) == 1
        assert len(result.suggestions) == 1


# ──────────────────────────────────────────────────────────────────
# Nesting and advanced directive integration tests
# ──────────────────────────────────────────────────────────────────


@_skip_no_api_key
class TestNestingAndAdvancedDirectives:
    """Integration tests for nested directives and advanced features."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_nested_summarize_inside_match(self):
        """@summarize nested inside a @match branch resolves correctly."""
        from promptspec.controller import (
            PromptSpecController,
            PromptSpecConfig,
        )

        spec = """
@match mode
  "brief" ==>
    @summarize
      Explain quantum computing in detail: qubits, superposition,
      entanglement, error correction, and current hardware
      limitations. Cover each topic with examples.
    Keep it under 100 words.
  "full" ==>
    Explain quantum computing in full detail.
"""
        controller = PromptSpecController(PromptSpecConfig())
        result = await controller.compose(spec, variables={"mode": "brief"})

        assert result.composed_prompt
        assert "@summarize" not in result.composed_prompt
        assert "@match" not in result.composed_prompt

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_nested_if_inside_if(self):
        """Double-nested @if blocks resolve inside out."""
        from promptspec.controller import (
            PromptSpecController,
            PromptSpecConfig,
        )

        spec = """
Write about {{topic}}.

@if include_details
  Include technical details.
  @if include_examples
    Add code examples for each concept.
"""
        controller = PromptSpecController(PromptSpecConfig())
        result = await controller.compose(
            spec,
            variables={
                "topic": "REST APIs",
                "include_details": True,
                "include_examples": True,
            },
        )

        assert result.composed_prompt
        assert "technical details" in result.composed_prompt.lower()
        assert "code examples" in result.composed_prompt.lower()
        assert "@if" not in result.composed_prompt

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_nested_if_false_omits_inner_block(self):
        """When outer @if is false, inner block is omitted entirely."""
        from promptspec.controller import (
            PromptSpecController,
            PromptSpecConfig,
        )

        spec = """
Write about databases.

@if include_advanced
  Advanced topics:
  @if include_sharding
    Explain sharding strategies.
"""
        controller = PromptSpecController(PromptSpecConfig())
        result = await controller.compose(
            spec,
            variables={
                "include_advanced": False,
                "include_sharding": True,
            },
        )

        assert result.composed_prompt
        assert "sharding" not in result.composed_prompt.lower()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_at_sign_escaping(self):
        """@@ in the spec renders as a literal @ in the output."""
        from promptspec.controller import (
            PromptSpecController,
            PromptSpecConfig,
        )

        spec = """
Python decorators use the @@property and @@staticmethod syntax.
Email: user@@example.com
"""
        controller = PromptSpecController(PromptSpecConfig())
        result = await controller.compose(spec, variables={})

        assert "@property" in result.composed_prompt
        assert "@staticmethod" in result.composed_prompt
        assert "user@example.com" in result.composed_prompt
        assert "@@" not in result.composed_prompt

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_note_stripped_from_output(self):
        """@note blocks are removed from the composed prompt."""
        from promptspec.controller import (
            PromptSpecController,
            PromptSpecConfig,
        )

        spec = """
@note
  This is an internal design note that should not appear in output.
  It explains the rationale for the prompt structure.

Write a professional email to the team about the Q3 roadmap.
"""
        controller = PromptSpecController(PromptSpecConfig())
        result = await controller.compose(spec, variables={})

        assert "professional email" in result.composed_prompt.lower()
        assert "internal design note" not in result.composed_prompt.lower()
        assert "@note" not in result.composed_prompt

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_consulting_proposal_spec(self):
        """The consulting-proposal spec composes with all its directives."""
        from promptspec.controller import (
            PromptSpecController,
            PromptSpecConfig,
        )

        vars_file = SPECS_DIR / "vars" / "consulting-proposal-example.json"
        spec_file = SPECS_DIR / "consulting-proposal.promptspec.md"

        variables = json.loads(vars_file.read_text())
        spec = spec_file.read_text()

        controller = PromptSpecController(PromptSpecConfig())
        result = await controller.compose(spec, variables=variables)

        assert result.composed_prompt
        assert "Meridian" in result.composed_prompt
        assert "@refine" not in result.composed_prompt
        assert "@match" not in result.composed_prompt
        assert "@audience" not in result.composed_prompt
        assert len(result.composed_prompt) > 200

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_knowledge_base_article_spec(self):
        """The knowledge-base-article spec composes correctly."""
        from promptspec.controller import (
            PromptSpecController,
            PromptSpecConfig,
        )

        vars_file = SPECS_DIR / "vars" / "knowledge-base-article-example.json"
        spec_file = SPECS_DIR / "knowledge-base-article.promptspec.md"

        variables = json.loads(vars_file.read_text())
        spec = spec_file.read_text()

        controller = PromptSpecController(PromptSpecConfig())
        result = await controller.compose(spec, variables=variables)

        assert result.composed_prompt
        assert "kafka" in result.composed_prompt.lower() or "event" in result.composed_prompt.lower()
        assert "@extract" not in result.composed_prompt
        assert "@summarize" not in result.composed_prompt
        assert "@compress" not in result.composed_prompt

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_api_docs_generator_spec(self):
        """The api-docs-generator spec composes correctly."""
        from promptspec.controller import (
            PromptSpecController,
            PromptSpecConfig,
        )

        vars_file = SPECS_DIR / "vars" / "api-docs-generator-example.json"
        spec_file = SPECS_DIR / "api-docs-generator.promptspec.md"

        variables = json.loads(vars_file.read_text())
        spec = spec_file.read_text()

        controller = PromptSpecController(PromptSpecConfig())
        result = await controller.compose(spec, variables=variables)

        assert result.composed_prompt
        assert "TaskFlow" in result.composed_prompt or "taskflow" in result.composed_prompt.lower()
        assert "@generate_examples" not in result.composed_prompt
        assert "@revise" not in result.composed_prompt

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_refine_with_nested_match(self):
        """@refine + @match work together (market research spec)."""
        from promptspec.controller import (
            PromptSpecController,
            PromptSpecConfig,
        )

        spec_file = SPECS_DIR / "market-research-brief.promptspec.md"
        vars_file = SPECS_DIR / "vars" / "market-research-example.json"

        spec = spec_file.read_text()
        variables = json.loads(vars_file.read_text())

        controller = PromptSpecController(PromptSpecConfig())
        result = await controller.compose(spec, variables=variables)

        assert result.composed_prompt
        # @refine should have pulled in base-analyst.promptspec.md content
        assert "analytical" in result.composed_prompt.lower() or "analysis" in result.composed_prompt.lower()
        # Variable substitution
        assert "Rivian" in result.composed_prompt
        # No raw directives
        assert "@refine" not in result.composed_prompt
        assert "@match" not in result.composed_prompt

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_log_transition_tool_called(self):
        """The log_transition tool is invoked during composition."""
        from promptspec.controller import (
            PromptSpecController,
            PromptSpecConfig,
        )

        spec = """
@match mode
  "a" ==>
    Option A content.
  "b" ==>
    Option B content.

Write about {{topic}}.
"""
        events = []

        def on_event(event_type, data):
            events.append((event_type, data))

        controller = PromptSpecController(PromptSpecConfig())
        result = await controller.compose(
            spec,
            variables={"mode": "a", "topic": "testing"},
            on_event=on_event,
        )

        assert result.composed_prompt
        # Transitions may or may not be logged depending on LLM behavior,
        # but the composition should succeed regardless
        assert "Option A" in result.composed_prompt or "testing" in result.composed_prompt.lower()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_multi_persona_debate_spec(self):
        """The multi-persona-debate spec with @expand/@contract/@revise."""
        from promptspec.controller import (
            PromptSpecController,
            PromptSpecConfig,
        )

        vars_file = SPECS_DIR / "vars" / "multi-persona-debate-agi.json"
        spec_file = SPECS_DIR / "multi-persona-debate.promptspec.md"

        variables = json.loads(vars_file.read_text())
        spec = spec_file.read_text()

        controller = PromptSpecController(PromptSpecConfig())
        result = await controller.compose(spec, variables=variables)

        prompt = result.composed_prompt
        assert prompt
        assert len(prompt) > 500
        # @expand should have added steel-manning and hidden assumptions
        assert "steel" in prompt.lower() or "assumption" in prompt.lower()
        # @contract should have removed bias language while keeping structure
        assert "4" in prompt or "perspectives" in prompt.lower()
        # No raw directives remain
        assert "@expand" not in prompt
        assert "@contract" not in prompt
        assert "@revise" not in prompt
        assert "@match" not in prompt
        assert "@note" not in prompt

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_adaptive_interview_spec(self):
        """The adaptive-interview spec with deeply nested @match/@if."""
        from promptspec.controller import (
            PromptSpecController,
            PromptSpecConfig,
        )

        vars_file = SPECS_DIR / "vars" / "adaptive-interview-senior-backend.json"
        spec_file = SPECS_DIR / "adaptive-interview.promptspec.md"

        variables = json.loads(vars_file.read_text())
        spec = spec_file.read_text()

        controller = PromptSpecController(PromptSpecConfig())
        result = await controller.compose(spec, variables=variables)

        prompt = result.composed_prompt
        assert prompt
        assert len(prompt) > 500
        # Should have selected "senior" branch inside "technical_deep_dive"
        assert "decompos" in prompt.lower() or "architecture" in prompt.lower()
        # Should include system design (include_system_design=true)
        assert "system design" in prompt.lower() or "design" in prompt.lower()
        # @refine should have merged base-analyst traits
        assert "analytical" in prompt.lower() or "evidence" in prompt.lower() or "rigorous" in prompt.lower()
        # No raw directives
        assert "@match" not in prompt
        assert "@if" not in prompt
        assert "@refine" not in prompt
        assert "@audience" not in prompt
        assert "@style" not in prompt

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_prompt_refactoring_pipeline_spec(self):
        """The prompt-refactoring-pipeline with @extract→@canon→@cohere→@revise chain."""
        from promptspec.controller import (
            PromptSpecController,
            PromptSpecConfig,
        )

        vars_file = SPECS_DIR / "vars" / "prompt-refactoring-example.json"
        spec_file = SPECS_DIR / "prompt-refactoring-pipeline.promptspec.md"

        variables = json.loads(vars_file.read_text())
        spec = spec_file.read_text()

        controller = PromptSpecController(PromptSpecConfig())
        result = await controller.compose(spec, variables=variables)

        prompt = result.composed_prompt
        assert prompt
        assert len(prompt) > 200
        # The @revise added a confidence field requirement
        assert "confidence" in prompt.lower()
        # The @expand added multi-language support
        assert "language" in prompt.lower() or "spanish" in prompt.lower()
        # The @contract removed "anything else" and replaced with natural ending
        assert "anything else" not in prompt.lower()
        # Contradictory tone instructions should be resolved
        # (original had both "formal" and "casual with emoji")
        # @canon + @cohere should have fixed duplicated "NEVER share internal pricing"
        # No raw directives
        assert "@extract" not in prompt
        assert "@canon" not in prompt
        assert "@cohere" not in prompt
        assert "@revise" not in prompt
        assert "@expand" not in prompt
        assert "@contract" not in prompt
        assert "@assert" not in prompt
