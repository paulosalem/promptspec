"""Tests for root text extraction and prefix/suffix cascading."""

import pytest
from promptspec.controller import _extract_root_text, _cascade_root_context


class TestExtractRootText:
    """Tests for _extract_root_text()."""

    def test_basic_prefix_extraction(self):
        spec = (
            "# My Solver\n"
            "\n"
            "@execute tree-of-thought\n"
            "  branching_factor: 3\n"
            "\n"
            "You are a problem solver.\n"
            "Problem: {{problem}}\n"
            "\n"
            "@prompt generate\n"
            "  Solve step by step.\n"
        )
        prefix, suffix = _extract_root_text(spec)
        assert "You are a problem solver." in prefix
        assert "Problem: {{problem}}" in prefix
        assert "# My Solver" in prefix
        assert "@execute" not in prefix
        assert "branching_factor" not in prefix
        assert suffix == ""

    def test_execute_block_stripped(self):
        spec = (
            "@execute self-consistency\n"
            "  samples: 5\n"
            "  aggregation: majority-vote\n"
            "\n"
            "Context text here.\n"
            "\n"
            "@prompt default\n"
            "  Do something.\n"
        )
        prefix, suffix = _extract_root_text(spec)
        assert "Context text here." in prefix
        assert "@execute" not in prefix
        assert "samples" not in prefix
        assert "aggregation" not in prefix

    def test_suffix_after_last_prompt(self):
        spec = (
            "@execute single-call\n"
            "\n"
            "Root text.\n"
            "\n"
            "@prompt generate\n"
            "  Generate something.\n"
            "\n"
            "@prompt evaluate\n"
            "  Evaluate it.\n"
            "\n"
            "@output_format enforce: strict\n"
            "  Always end with ANSWER: X\n"
        )
        prefix, suffix = _extract_root_text(spec)
        assert "Root text." in prefix
        assert "@output_format enforce: strict" in suffix
        assert "Always end with ANSWER: X" in suffix

    def test_no_prompt_directives(self):
        spec = (
            "@execute single-call\n"
            "\n"
            "Just a simple spec with no @prompt.\n"
        )
        prefix, suffix = _extract_root_text(spec)
        assert prefix == ""
        assert suffix == ""

    def test_empty_root_text(self):
        spec = (
            "@prompt generate\n"
            "  Do something.\n"
        )
        prefix, suffix = _extract_root_text(spec)
        assert prefix == ""

    def test_preserves_other_directives(self):
        spec = (
            "@execute tree-of-thought\n"
            "  branching_factor: 3\n"
            "\n"
            "@refine base-prompt.md\n"
            "\n"
            "You are a solver.\n"
            "\n"
            "@prompt generate\n"
            "  Solve it.\n"
        )
        prefix, suffix = _extract_root_text(spec)
        assert "@refine base-prompt.md" in prefix
        assert "You are a solver." in prefix
        assert "@execute" not in prefix

    def test_preserves_markdown_headers(self):
        spec = (
            "# Title\n"
            "\n"
            "@execute reflection\n"
            "  max_rounds: 2\n"
            "\n"
            "## Task\n"
            "\n"
            "Do the task: {{task}}\n"
            "\n"
            "@prompt generate\n"
            "  Write it.\n"
        )
        prefix, suffix = _extract_root_text(spec)
        assert "# Title" in prefix
        assert "## Task" in prefix
        assert "Do the task: {{task}}" in prefix

    def test_multiple_prompts_suffix(self):
        """Suffix is only text after the LAST @prompt block."""
        spec = (
            "Root.\n"
            "\n"
            "@prompt generate\n"
            "  Gen.\n"
            "\n"
            "@prompt evaluate\n"
            "  Eval.\n"
            "\n"
            "@prompt synthesize\n"
            "  Synth.\n"
            "\n"
            "Final instruction.\n"
        )
        prefix, suffix = _extract_root_text(spec)
        assert "Root." in prefix
        assert "Final instruction." in suffix

    def test_variables_preserved_as_placeholders(self):
        spec = (
            "@execute tree-of-thought\n"
            "\n"
            "Solve: {{problem}}\n"
            "For audience: {{audience}}\n"
            "\n"
            "@prompt generate\n"
            "  Do it.\n"
        )
        prefix, suffix = _extract_root_text(spec)
        assert "{{problem}}" in prefix
        assert "{{audience}}" in prefix


class TestCascadeRootContext:
    """Tests for _cascade_root_context()."""

    def test_prefix_prepended(self):
        prompts = {
            "generate": "Solve step by step.",
            "evaluate": "Check the answer.",
        }
        result = _cascade_root_context(prompts, "You are a solver.", "")
        assert result["generate"].startswith("You are a solver.")
        assert "Solve step by step." in result["generate"]
        assert result["evaluate"].startswith("You are a solver.")
        assert "Check the answer." in result["evaluate"]

    def test_suffix_appended(self):
        prompts = {
            "generate": "Solve it.",
            "evaluate": "Check it.",
        }
        result = _cascade_root_context(prompts, "", "ANSWER: X")
        assert result["generate"].endswith("ANSWER: X")
        assert result["evaluate"].endswith("ANSWER: X")

    def test_prefix_and_suffix(self):
        prompts = {"generate": "Middle content."}
        result = _cascade_root_context(prompts, "PREFIX", "SUFFIX")
        assert result["generate"] == "PREFIX\n\nMiddle content.\n\nSUFFIX"

    def test_empty_root_noop(self):
        prompts = {"generate": "Original."}
        result = _cascade_root_context(prompts, "", "")
        assert result == prompts

    def test_single_call_default_key_skipped(self):
        """Single-call specs with only 'default' key are not cascaded."""
        prompts = {"default": "Full prompt here."}
        result = _cascade_root_context(prompts, "Root text.", "Suffix.")
        assert result == prompts

    def test_multiple_keys_all_cascaded(self):
        prompts = {
            "generate": "Gen.",
            "evaluate": "Eval.",
            "synthesize": "Synth.",
        }
        result = _cascade_root_context(prompts, "Context.", "")
        for key in prompts:
            assert result[key].startswith("Context.")

    def test_system_key_also_cascaded(self):
        """Even a 'system' key gets prefix/suffix if present."""
        prompts = {
            "system": "You are a bot.",
            "generate": "Gen.",
        }
        result = _cascade_root_context(prompts, "Root.", "")
        assert result["system"].startswith("Root.")
        assert result["generate"].startswith("Root.")
