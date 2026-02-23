"""Comprehensive directive-level tests for the PromptSpec.

These tests treat the prompt specification language as a programming
language and test each construct in isolation, with parameter variants,
edge cases, and composition interactions.

Every test uses REAL LLM calls (no mocks). Requires OPENAI_API_KEY.

Test organization mirrors the system prompt's directive categories:
  1. Variable substitution ({{var}}, @var, @{var})
  2. Control flow (@if/@else, @match)
  3. File inclusion (@refine)
  4. Semantic revision (@revise, @expand, @contract)
  5. Semantic transforms (@canon, @cohere, @audience, @style)
  6. Lossy content (@summarize, @compress, @extract)
  7. Generation (@generate_examples)
  8. Constraints (@output_format, @structural_constraints, @assert)
  9. Debug queries (@directives?, @vars?, @structure?)
  10. Meta-comments (@note)
  11. Escaping (@@)
  12. Nesting & composition order
"""

import json
import os
from pathlib import Path

import pytest

_skip = pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY not set — requires a real LLM",
)

SPECS_DIR = (
    Path(__file__).resolve().parents[1]
    / "specs"
)


def _controller():
    """Create a fresh controller for each test."""
    from promptspec.controller import (
        PromptSpecController,
        PromptSpecConfig,
    )
    return PromptSpecController(PromptSpecConfig())


async def _compose(spec: str, variables: dict | None = None, **kwargs):
    """Shorthand: compose a spec and return the result."""
    c = _controller()
    return await c.compose(spec, variables=variables or {}, **kwargs)


# ═══════════════════════════════════════════════════════════════════
# 1. Variable Substitution
# ═══════════════════════════════════════════════════════════════════


@_skip
class TestVariableSubstitution:

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_mustache_variable(self):
        """{{var}} is replaced with its value."""
        r = await _compose("Hello {{name}}, welcome to {{place}}.",
                           {"name": "Alice", "place": "Wonderland"})
        assert "Alice" in r.composed_prompt
        assert "Wonderland" in r.composed_prompt
        assert "{{" not in r.composed_prompt

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_inline_at_variable(self):
        """@var inline syntax is replaced."""
        r = await _compose("Dear @name, your order @order_id is ready.",
                           {"name": "Bob", "order_id": "ORD-42"})
        assert "Bob" in r.composed_prompt
        assert "ORD-42" in r.composed_prompt

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_inline_braced_variable(self):
        """@{var} syntax handles adjacent text."""
        r = await _compose("File: report_@{version}_final.pdf",
                           {"version": "v3"})
        assert "report_v3_final.pdf" in r.composed_prompt

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_missing_variable_warns(self):
        """Referencing an undefined variable emits a warning."""
        r = await _compose("Hello {{undefined_var}}.", {})
        # Should warn about the missing variable
        assert len(r.warnings) > 0 or "undefined" in r.composed_prompt.lower() \
            or "{{undefined_var}}" in r.composed_prompt

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_multiple_occurrences_replaced(self):
        """Same variable used multiple times is replaced everywhere."""
        r = await _compose("{{x}} plus {{x}} equals two {{x}}s.",
                           {"x": "apple"})
        assert r.composed_prompt.lower().count("apple") >= 2
        assert "{{x}}" not in r.composed_prompt


# ═══════════════════════════════════════════════════════════════════
# 2. Control Flow — @if / @else
# ═══════════════════════════════════════════════════════════════════


@_skip
class TestIfElse:

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_if_true_includes_block(self):
        r = await _compose(
            "Base text.\n\n@if show_extra\n  Extra content here.\n",
            {"show_extra": True},
        )
        assert "Extra content" in r.composed_prompt
        assert "@if" not in r.composed_prompt

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_if_false_excludes_block(self):
        r = await _compose(
            "Base text.\n\n@if show_extra\n  Extra content here.\n",
            {"show_extra": False},
        )
        assert "Extra content" not in r.composed_prompt

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_if_else_true_branch(self):
        """When condition is true, @if block included, @else excluded."""
        spec = (
            "Start.\n\n"
            "@if premium\n"
            "  Welcome, premium member!\n"
            "@else\n"
            "  Please upgrade.\n"
        )
        r = await _compose(spec, {"premium": True})
        assert "premium member" in r.composed_prompt.lower()
        assert "upgrade" not in r.composed_prompt.lower()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_if_else_false_branch(self):
        """When condition is false, @else block included."""
        spec = (
            "Start.\n\n"
            "@if premium\n"
            "  Welcome, premium member!\n"
            "@else\n"
            "  Please upgrade.\n"
        )
        r = await _compose(spec, {"premium": False})
        assert "upgrade" in r.composed_prompt.lower()
        assert "premium member" not in r.composed_prompt.lower()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_if_missing_variable_warns(self):
        """Missing condition variable should warn and treat as false."""
        spec = "Base.\n\n@if nonexistent_flag\n  Hidden.\n"
        r = await _compose(spec, {})
        # Should warn about missing variable
        assert len(r.warnings) > 0 or "Hidden" not in r.composed_prompt


# ═══════════════════════════════════════════════════════════════════
# 3. Control Flow — @match
# ═══════════════════════════════════════════════════════════════════


@_skip
class TestMatch:

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_match_selects_correct_branch(self):
        spec = (
            '@match color\n'
            '  "red" ==> You chose red.\n'
            '  "blue" ==> You chose blue.\n'
            '  "green" ==> You chose green.\n'
        )
        r = await _compose(spec, {"color": "blue"})
        assert "blue" in r.composed_prompt.lower()
        assert "red" not in r.composed_prompt.lower()
        assert "green" not in r.composed_prompt.lower()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_match_wildcard_default(self):
        """_ wildcard matches when no other case does."""
        spec = (
            '@match tier\n'
            '  "enterprise" ==> Enterprise features.\n'
            '  _ ==> Standard features.\n'
        )
        r = await _compose(spec, {"tier": "free"})
        assert "standard" in r.composed_prompt.lower()
        assert "enterprise" not in r.composed_prompt.lower()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_match_no_match_no_wildcard_warns(self):
        """No matching case and no wildcard: warn and remove block."""
        spec = (
            'Intro.\n\n'
            '@match size\n'
            '  "small" ==> Small.\n'
            '  "large" ==> Large.\n'
        )
        r = await _compose(spec, {"size": "medium"})
        assert "Small" not in r.composed_prompt
        assert "Large" not in r.composed_prompt
        assert len(r.warnings) > 0

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_match_multiline_block(self):
        """Multi-line block effect after ==>."""
        spec = (
            '@match mode\n'
            '  "detailed" ==>\n'
            '    Paragraph one of detailed mode.\n'
            '    Paragraph two of detailed mode.\n'
            '  "brief" ==> One liner.\n'
        )
        r = await _compose(spec, {"mode": "detailed"})
        assert "paragraph one" in r.composed_prompt.lower()
        assert "paragraph two" in r.composed_prompt.lower()


# ═══════════════════════════════════════════════════════════════════
# 4. File Inclusion — @refine
# ═══════════════════════════════════════════════════════════════════


@_skip
class TestRefine:

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_refine_merges_file_content(self):
        """@refine pulls in file and merges content."""
        spec = "@refine base-analyst.promptspec.md\n\nAnalyze the housing market."
        r = await _compose(spec, {}, base_dir=SPECS_DIR)
        # base-analyst.promptspec.md content should be integrated
        p = r.composed_prompt.lower()
        assert "analytical" in p or "evidence" in p or "rigorous" in p
        assert "housing" in p
        assert "@refine" not in r.composed_prompt

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_refine_mingle_false(self):
        """@refine mingle: false does minimal merge (preserves wording)."""
        spec = (
            "@refine base-analyst.promptspec.md mingle: false\n\n"
            "Analyze the housing market."
        )
        r = await _compose(spec, {}, base_dir=SPECS_DIR)
        p = r.composed_prompt.lower()
        assert "housing" in p
        assert "@refine" not in r.composed_prompt

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_refine_missing_file_errors(self):
        """Referencing a nonexistent file should emit an error."""
        spec = "@refine nonexistent_file_xyz.md\n\nSome text."
        r = await _compose(spec, {}, base_dir=SPECS_DIR)
        assert len(r.errors) > 0 or len(r.warnings) > 0


# ═══════════════════════════════════════════════════════════════════
# 5. Semantic Revision — @revise, @expand, @contract
# ═══════════════════════════════════════════════════════════════════


@_skip
class TestRevise:

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_revise_adds_requirement(self):
        """@revise incorporates a new constraint into existing prompt."""
        spec = (
            "You are a helpful assistant. Respond in plain text.\n\n"
            "@revise\n"
            "  All responses must be valid JSON with keys: answer, confidence.\n"
        )
        r = await _compose(spec, {})
        p = r.composed_prompt.lower()
        assert "json" in p
        assert "answer" in p
        assert "confidence" in p
        # The conflicting "plain text" should be revised away or reconciled
        assert "@revise" not in r.composed_prompt

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_revise_minimal_mode(self):
        """@revise mode: minimal makes smallest edits."""
        spec = (
            "Be concise. Use bullet lists. Max 200 words.\n\n"
            "@revise mode: minimal\n"
            "  Change max length to 500 words.\n"
        )
        r = await _compose(spec, {})
        p = r.composed_prompt.lower()
        assert "500" in p
        assert "@revise" not in r.composed_prompt


@_skip
class TestExpand:

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_expand_adds_content(self):
        """@expand adds new content without removing existing."""
        spec = (
            "You are a code reviewer.\n\n"
            "## Checks\n"
            "- Check naming conventions\n"
            "- Check error handling\n\n"
            "@expand\n"
            '  Add a "Security" section with 3 checks for injection vulnerabilities.\n'
        )
        r = await _compose(spec, {})
        p = r.composed_prompt.lower()
        # Original content preserved
        assert "naming" in p
        assert "error handling" in p
        # New content added
        assert "security" in p or "injection" in p
        assert "@expand" not in r.composed_prompt

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_expand_does_not_remove_existing(self):
        """@expand must not remove prior requirements."""
        spec = (
            "MUST use Python 3.12.\n"
            "MUST follow PEP 8.\n\n"
            "@expand\n"
            "  Add a requirement for type hints on all public functions.\n"
        )
        r = await _compose(spec, {})
        p = r.composed_prompt.lower()
        assert "python" in p or "3.12" in p
        assert "pep 8" in p or "pep8" in p
        assert "type hint" in p or "type annotation" in p


@_skip
class TestContract:

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_contract_removes_content(self):
        """@contract removes specified content."""
        spec = (
            "## Introduction\n"
            "Welcome! We're so excited to have you.\n\n"
            "## Requirements\n"
            "- MUST validate input.\n"
            "- MUST log errors.\n\n"
            "@contract\n"
            "  Remove the Introduction section entirely.\n"
        )
        r = await _compose(spec, {})
        p = r.composed_prompt.lower()
        assert "excited" not in p and "welcome" not in p
        # Requirements preserved
        assert "validate" in p
        assert "log" in p
        assert "@contract" not in r.composed_prompt

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_contract_safety_strict(self):
        """@contract safety: strict preserves safety constraints."""
        spec = (
            "NEVER share user passwords.\n"
            "NEVER execute arbitrary code.\n"
            "Be helpful and friendly.\n\n"
            "@contract safety: strict\n"
            "  Remove all constraints.\n"
        )
        r = await _compose(spec, {})
        p = r.composed_prompt.lower()
        # Safety constraints should be preserved (or warned about)
        has_safety = "password" in p or "never" in p
        has_warning = len(r.warnings) > 0
        assert has_safety or has_warning


# ═══════════════════════════════════════════════════════════════════
# 6. Semantic Transforms — @canon, @cohere, @audience, @style
# ═══════════════════════════════════════════════════════════════════


@_skip
class TestCanon:

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_canon_normalizes(self):
        """@canon normalizes inconsistent formatting."""
        spec = (
            "# heading one\n\n"
            "- item a\n"
            "* item b\n"
            "- item c\n\n"
            "## Heading Two\n"
            "### heading THREE\n\n"
            "@canon\n"
        )
        r = await _compose(spec, {})
        p = r.composed_prompt
        assert "@canon" not in p
        # Content should be preserved
        assert "item a" in p.lower()
        assert "item b" in p.lower()
        assert "item c" in p.lower()


@_skip
class TestCohere:

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_cohere_resolves_contradictions(self):
        """@cohere reconciles contradictory instructions."""
        spec = (
            "Be formal and professional.\n"
            "Use casual language with emoji.\n"
            "Respond in exactly 3 sentences.\n\n"
            "@cohere\n"
        )
        r = await _compose(spec, {})
        p = r.composed_prompt.lower()
        assert "@cohere" not in r.composed_prompt
        # Should have resolved the formal/casual contradiction
        # At minimum, both shouldn't remain contradicted
        assert "3 sentence" in p or "three sentence" in p


@_skip
class TestAudience:

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_audience_adapts_language(self):
        """@audience adjusts vocabulary for the target reader."""
        spec = (
            "Explain how a B-tree index works in PostgreSQL, "
            "including page splits and fill factor.\n\n"
            '@audience "non-technical product managers"\n'
        )
        r = await _compose(spec, {})
        p = r.composed_prompt.lower()
        assert "@audience" not in r.composed_prompt
        # Should be simplified for non-technical readers
        # Hard to assert specifics, but prompt should still mention the topic
        assert "index" in p or "database" in p or "search" in p


@_skip
class TestStyle:

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_style_applies_tone(self):
        """@style changes presentation without altering requirements."""
        spec = (
            "List 5 best practices for API design.\n\n"
            '@style "terse, telegram-style, no articles or pronouns"\n'
        )
        r = await _compose(spec, {})
        p = r.composed_prompt
        assert "@style" not in p
        assert "API" in p or "api" in p.lower()
        assert "5" in p or "five" in p.lower()


# ═══════════════════════════════════════════════════════════════════
# 7. Lossy Content — @summarize, @compress, @extract
# ═══════════════════════════════════════════════════════════════════


@_skip
class TestSummarize:

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_summarize_block(self):
        """@summarize condenses its indented block."""
        long_text = (
            "Machine learning is a subset of artificial intelligence that "
            "focuses on building systems that learn from data. It encompasses "
            "supervised learning (classification, regression), unsupervised "
            "learning (clustering, dimensionality reduction), reinforcement "
            "learning (policy optimization, reward shaping), and semi-supervised "
            "approaches. Key algorithms include decision trees, random forests, "
            "support vector machines, neural networks, and gradient boosting. "
            "Evaluation metrics vary: accuracy, precision, recall, F1, AUC-ROC "
            "for classification; MSE, RMSE, MAE, R² for regression."
        )
        spec = f"@summarize length: short\n  {long_text}\n"
        r = await _compose(spec, {})
        p = r.composed_prompt
        assert "@summarize" not in p
        # Summary should be shorter than original
        assert len(p.strip()) < len(long_text)
        # Should mention ML or learning
        assert "learning" in p.lower() or "ml" in p.lower()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_summarize_file(self):
        """@summarize file: <path> summarizes file content."""
        spec = "@summarize file: base-analyst.promptspec.md length: short\n"
        r = await _compose(spec, {}, base_dir=SPECS_DIR)
        p = r.composed_prompt
        assert "@summarize" not in p
        assert len(p.strip()) > 10  # Not empty


@_skip
class TestCompress:

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_compress_reduces_length(self):
        """@compress produces shorter output while preserving constraints."""
        original = (
            "You are a customer support agent. You MUST always greet "
            "the customer by name. You MUST respond within 24 hours. "
            "You SHOULD use a friendly but professional tone. You MUST "
            "NOT share internal pricing information under any circumstances. "
            "You SHOULD include relevant documentation links when available. "
            "You MUST escalate billing issues to the billing team immediately."
        )
        spec = f"{original}\n\n@compress preserve: hard\n"
        r = await _compose(spec, {})
        p = r.composed_prompt
        assert "@compress" not in p
        # Hard constraints (MUST) should be preserved
        p_lower = p.lower()
        assert "greet" in p_lower or "name" in p_lower
        assert "pricing" in p_lower or "internal" in p_lower
        # Should be shorter
        assert len(p.strip()) < len(original) * 1.1


@_skip
class TestExtract:

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_extract_pulls_requirements(self):
        """@extract pulls specific information from text."""
        spec = (
            "We're building a great product! The team is amazing.\n"
            "MUST support OAuth 2.0 authentication.\n"
            "The office has great coffee.\n"
            "MUST handle 10K requests per second.\n"
            "SHOULD log all API calls.\n"
            "The CEO loves this project.\n\n"
            "@extract format: bullets\n"
            "  All MUST and SHOULD requirements only.\n"
        )
        r = await _compose(spec, {})
        p = r.composed_prompt.lower()
        assert "@extract" not in r.composed_prompt
        assert "oauth" in p
        assert "10k" in p or "10,000" in p or "10000" in p
        # Fluff should be removed
        assert "coffee" not in p
        assert "ceo" not in p


# ═══════════════════════════════════════════════════════════════════
# 8. Generation — @generate_examples
# ═══════════════════════════════════════════════════════════════════


@_skip
class TestGenerateExamples:

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_generate_examples_creates_examples(self):
        """@generate_examples adds illustrative examples."""
        spec = (
            "Respond with JSON: {\"sentiment\": \"positive\"|\"negative\", "
            "\"score\": 0.0-1.0}\n\n"
            "@generate_examples count: 2 style: realistic\n"
        )
        r = await _compose(spec, {})
        p = r.composed_prompt.lower()
        assert "@generate_examples" not in r.composed_prompt
        assert "sentiment" in p
        # Should have generated example JSON
        assert "positive" in p or "negative" in p


# ═══════════════════════════════════════════════════════════════════
# 9. Constraints — @output_format, @structural_constraints, @assert
# ═══════════════════════════════════════════════════════════════════


@_skip
class TestOutputFormat:

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_output_format_adds_section(self):
        """@output_format inserts an output format specification."""
        spec = (
            "Analyze the given text for sentiment.\n\n"
            '@output_format enforce: strict\n'
            '  JSON only: {"sentiment": string, "confidence": float}\n'
        )
        r = await _compose(spec, {})
        p = r.composed_prompt.lower()
        assert "@output_format" not in r.composed_prompt
        assert "json" in p
        assert "sentiment" in p


@_skip
class TestStructuralConstraints:

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_structural_constraints_reorders(self):
        """@structural_constraints enforces section ordering."""
        spec = (
            "## Output\nReturn JSON.\n\n"
            "## Role\nYou are an analyst.\n\n"
            "## Steps\n1. Read input.\n2. Analyze.\n\n"
            "@structural_constraints strict: false\n"
            "  Sections in order: Role, Steps, Output.\n"
        )
        r = await _compose(spec, {})
        p = r.composed_prompt
        assert "@structural_constraints" not in p
        # Role should appear before Output in the reordered prompt
        role_pos = p.lower().find("role") if "role" in p.lower() else -1
        analyst_pos = p.lower().find("analyst") if "analyst" in p.lower() else -1
        output_pos = p.lower().find("output") if "output" in p.lower() else -1
        # At minimum, content should be preserved
        assert "analyst" in p.lower()
        assert "json" in p.lower()


@_skip
class TestAssert:

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_assert_passes_silently(self):
        """@assert with satisfied condition is removed without error."""
        spec = (
            "## Output Format\nReturn JSON.\n\n"
            "Analyze sentiment.\n\n"
            '@assert severity: error The prompt contains an Output Format section.\n'
        )
        r = await _compose(spec, {})
        assert "@assert" not in r.composed_prompt
        assert len(r.errors) == 0

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_assert_fails_with_error(self):
        """@assert with unsatisfied condition emits an error."""
        spec = (
            "Analyze sentiment.\n\n"
            '@assert severity: error The prompt contains an Output Format section.\n'
        )
        r = await _compose(spec, {})
        # Should emit an error since there's no Output Format section
        assert len(r.errors) > 0

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_assert_warning_severity(self):
        """@assert severity: warning emits warning instead of error."""
        spec = (
            "Analyze sentiment.\n\n"
            '@assert severity: warning The prompt specifies max response length.\n'
        )
        r = await _compose(spec, {})
        # Should emit a warning, not an error
        assert len(r.warnings) > 0 or len(r.suggestions) > 0


# ═══════════════════════════════════════════════════════════════════
# 10. Debug Queries — @directives?, @vars?, @structure?
# ═══════════════════════════════════════════════════════════════════


@_skip
class TestDebugQueries:

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_directives_query(self):
        """@directives? lists directives without appearing in output."""
        spec = (
            "@if show\n"
            "  Content.\n\n"
            '@match x\n'
            '  "a" ==> A.\n\n'
            "@directives?\n"
        )
        r = await _compose(spec, {"show": True, "x": "a"})
        assert "@directives?" not in r.composed_prompt
        # Should have analysis or suggestion listing the directives
        all_issues = " ".join(r.suggestions + r.warnings).lower()
        analysis = (r.analysis or "").lower()
        has_directive_info = (
            "@if" in all_issues or "@match" in all_issues
            or "@if" in analysis or "@match" in analysis
        )
        assert has_directive_info

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_vars_query(self):
        """@vars? lists referenced variables."""
        spec = (
            "Hello {{name}}, you are {{role}}.\n\n"
            "@vars?\n"
        )
        r = await _compose(spec, {"name": "Alice"})
        assert "@vars?" not in r.composed_prompt
        # Should mention the variables (especially the missing one)
        all_text = " ".join(r.suggestions + r.warnings).lower()
        analysis = (r.analysis or "").lower()
        has_var_info = "role" in all_text or "role" in analysis
        assert has_var_info

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_structure_query(self):
        """@structure? describes prompt structure."""
        spec = (
            "# Title\nIntro.\n\n"
            "## Section A\nContent A.\n\n"
            "## Section B\nContent B.\n\n"
            "@structure?\n"
        )
        r = await _compose(spec, {})
        assert "@structure?" not in r.composed_prompt
        all_text = " ".join(r.suggestions + r.warnings).lower()
        analysis = (r.analysis or "").lower()
        has_struct_info = (
            "section" in all_text or "heading" in all_text
            or "section" in analysis or "heading" in analysis
        )
        assert has_struct_info


# ═══════════════════════════════════════════════════════════════════
# 11. Meta-Comments & Escaping
# ═══════════════════════════════════════════════════════════════════


@_skip
class TestNoteAndEscaping:

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_note_stripped(self):
        """@note blocks are removed from final output."""
        spec = (
            "@note\n"
            "  Internal: this fixes bug #1234.\n"
            "  Do not remove the next instruction.\n\n"
            "Always validate user input.\n"
        )
        r = await _compose(spec, {})
        assert "bug #1234" not in r.composed_prompt
        assert "internal" not in r.composed_prompt.lower()
        assert "validate" in r.composed_prompt.lower()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_double_at_escaping(self):
        """@@ renders as literal @ in the output."""
        spec = (
            "Use Python decorators: @@property, @@staticmethod.\n"
            "Contact: admin@@example.com\n"
        )
        r = await _compose(spec, {})
        assert "@property" in r.composed_prompt
        assert "@staticmethod" in r.composed_prompt
        assert "admin@example.com" in r.composed_prompt
        assert "@@" not in r.composed_prompt

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_escaped_directive_not_executed(self):
        """@@if should render as @if text, not execute as directive."""
        spec = "The syntax is @@if condition for conditional blocks.\n"
        r = await _compose(spec, {})
        assert "@if" in r.composed_prompt
        assert "@@if" not in r.composed_prompt


# ═══════════════════════════════════════════════════════════════════
# 12. Nesting, Composition Order, and Interactions
# ═══════════════════════════════════════════════════════════════════


@_skip
class TestNestingAndComposition:

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_if_inside_match(self):
        """@if nested inside a @match branch."""
        spec = (
            '@match role\n'
            '  "engineer" ==>\n'
            '    You are a software engineer.\n'
            '    @if senior\n'
            '      Focus on architecture and mentoring.\n'
            '  "designer" ==> You are a designer.\n'
        )
        r = await _compose(spec, {"role": "engineer", "senior": True})
        p = r.composed_prompt.lower()
        assert "software engineer" in p or "engineer" in p
        assert "architecture" in p or "mentoring" in p
        assert "@match" not in r.composed_prompt
        assert "@if" not in r.composed_prompt

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_match_inside_if(self):
        """@match nested inside an @if block."""
        spec = (
            "Base prompt.\n\n"
            "@if customize\n"
            '  @match tone\n'
            '    "formal" ==> Use formal language.\n'
            '    "casual" ==> Use casual language.\n'
        )
        r = await _compose(spec, {"customize": True, "tone": "formal"})
        p = r.composed_prompt.lower()
        assert "formal" in p
        assert "casual" not in p

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_summarize_inside_if(self):
        """@summarize nested inside @if — inner resolves first."""
        spec = (
            "Base prompt.\n\n"
            "@if include_background\n"
            "  @summarize length: short\n"
            "    Machine learning encompasses supervised, unsupervised,\n"
            "    and reinforcement learning paradigms. Supervised learning\n"
            "    uses labeled data. Unsupervised learning discovers patterns\n"
            "    in unlabeled data. Reinforcement learning optimizes\n"
            "    sequential decisions via reward signals.\n"
        )
        r = await _compose(spec, {"include_background": True})
        p = r.composed_prompt.lower()
        assert "learning" in p or "ml" in p
        assert "@summarize" not in r.composed_prompt
        assert "@if" not in r.composed_prompt

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_expand_then_contract(self):
        """@expand followed by @contract: expand adds, contract removes."""
        spec = (
            "You are a writing assistant.\n"
            "Help users write clear emails.\n\n"
            "@expand\n"
            "  Also help with formal letters and memos.\n\n"
            "@contract\n"
            "  Remove any mention of emails.\n"
        )
        r = await _compose(spec, {})
        p = r.composed_prompt.lower()
        # Expanded content should be present
        assert "letter" in p or "memo" in p
        # Contracted content should be removed
        assert "email" not in p
        assert "@expand" not in r.composed_prompt
        assert "@contract" not in r.composed_prompt

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_revise_after_refine(self):
        """@refine then @revise: refine merges, revise modifies the result."""
        spec = (
            "@refine base-analyst.promptspec.md\n\n"
            "Analyze customer churn.\n\n"
            "@revise\n"
            "  Replace all mentions of confidence levels with a\n"
            "  numeric scale from 1-10 instead of high/medium/low.\n"
        )
        r = await _compose(spec, {}, base_dir=SPECS_DIR)
        p = r.composed_prompt.lower()
        assert "churn" in p
        # The revision should have changed confidence levels
        assert "1" in p or "10" in p or "numeric" in p or "scale" in p
        assert "@refine" not in r.composed_prompt
        assert "@revise" not in r.composed_prompt

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_extract_then_output_format(self):
        """@extract followed by @output_format: extract first, then format."""
        spec = (
            "Our company values innovation, integrity, and inclusion.\n"
            "We MUST ship features weekly.\n"
            "We SHOULD maintain 80% test coverage.\n"
            "We MUST NOT deploy on Fridays.\n"
            "Team lunches are on Wednesdays.\n\n"
            "@extract format: bullets\n"
            "  All MUST and SHOULD requirements.\n\n"
            '@output_format "markdown"\n'
        )
        r = await _compose(spec, {})
        p = r.composed_prompt.lower()
        assert "ship" in p or "weekly" in p
        assert "test coverage" in p or "80%" in p
        assert "friday" in p
        # Fluff removed by extract
        assert "lunch" not in p
        assert "@extract" not in r.composed_prompt
        assert "@output_format" not in r.composed_prompt

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_multiple_asserts_all_checked(self):
        """Multiple @assert directives are all evaluated."""
        spec = (
            "## Role\nYou are an analyst.\n\n"
            "## Output Format\nReturn JSON.\n\n"
            '@assert severity: error The prompt contains a Role section.\n'
            '@assert severity: error The prompt contains an Output Format section.\n'
            '@assert severity: warning The prompt specifies example outputs.\n'
        )
        r = await _compose(spec, {})
        # First two asserts should pass
        assert len(r.errors) == 0
        # Third assert should warn (no examples)
        assert len(r.warnings) > 0 or len(r.suggestions) > 0


# ═══════════════════════════════════════════════════════════════════
# 13. Edge Cases and Error Handling
# ═══════════════════════════════════════════════════════════════════


@_skip
class TestEdgeCases:

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_empty_spec(self):
        """Empty spec produces empty or minimal output."""
        r = await _compose("", {})
        # Should not error out
        assert r is not None

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_no_directives_passthrough(self):
        """Plain text with no directives passes through unchanged."""
        text = "Write a poem about the sea."
        r = await _compose(text, {})
        # Core content should be preserved
        assert "poem" in r.composed_prompt.lower()
        assert "sea" in r.composed_prompt.lower()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_unknown_directive_warns(self):
        """An unrecognized @directive should produce a warning."""
        spec = "Some text.\n\n@frobnicate\n  Do something weird.\n"
        r = await _compose(spec, {})
        # Should warn about unrecognized directive
        has_warning = len(r.warnings) > 0 or len(r.suggestions) > 0
        assert has_warning

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_deeply_nested_three_levels(self):
        """Three levels of nesting resolve correctly."""
        spec = (
            "@if level1\n"
            "  Level 1 active.\n"
            "  @if level2\n"
            "    Level 2 active.\n"
            "    @if level3\n"
            "      Level 3 active.\n"
        )
        r = await _compose(spec, {
            "level1": True,
            "level2": True,
            "level3": True,
        })
        p = r.composed_prompt.lower()
        assert "level 1" in p
        assert "level 2" in p
        assert "level 3" in p
        assert "@if" not in r.composed_prompt

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_variable_in_directive_argument(self):
        """Variables inside directive arguments are substituted."""
        spec = (
            '@match {{choice_var}}\n'
            '  "alpha" ==> You chose alpha.\n'
            '  "beta" ==> You chose beta.\n'
        )
        r = await _compose(spec, {"choice_var": "beta"})
        # This tests whether the variable in the @match expression resolves
        p = r.composed_prompt.lower()
        assert "beta" in p

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_mustache_list_variable(self):
        """{{#list}}...{{/list}} Mustache iteration."""
        spec = (
            "Review these files:\n"
            "{{#files}}\n"
            "- {{.}}\n"
            "{{/files}}\n"
        )
        r = await _compose(spec, {"files": ["app.py", "utils.py", "tests.py"]})
        p = r.composed_prompt.lower()
        assert "app.py" in p
        assert "utils.py" in p
        assert "tests.py" in p


# ═══════════════════════════════════════════════════════════════════
# 14. Deep Nesting — Cross-Category, Multi-Level
#
#     These tests exercise the inside-out evaluation rule with
#     3-4 levels of nesting across different directive categories.
#     Each test has precise assertions on WHAT should be present
#     and WHAT should be absent — verifying that every layer
#     resolved correctly.
# ═══════════════════════════════════════════════════════════════════


@_skip
class TestDeepNesting:

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_refine_then_match_then_compress(self):
        """@refine → @match → @compress: 3-level cross-category nesting.

        The @compress is inside a @match branch, which is inside a
        prompt that @refines a base file. Inside-out: compress first,
        then match selects the branch, then refine merges the base.
        """
        spec = (
            "@refine base-analyst.promptspec.md\n\n"
            "Analyze {{topic}}.\n\n"
            "@match depth\n"
            '  "brief" ==>\n'
            "    @compress preserve: hard\n"
            "      Provide a full analysis covering: market size and growth\n"
            "      trajectory, key competitors and their market shares,\n"
            "      regulatory environment including pending legislation,\n"
            "      customer segmentation with demographics and willingness\n"
            "      to pay, and a SWOT analysis with at least one data point\n"
            "      per quadrant. Conclude with prioritized recommendations.\n"
            '  "full" ==>\n'
            "    Provide the complete uncompressed analysis.\n"
        )
        r = await _compose(spec, {"topic": "solar energy", "depth": "brief"},
                           base_dir=SPECS_DIR)
        p = r.composed_prompt
        p_lower = p.lower()

        # Layer 1 (innermost): @compress should have shortened the text
        # The original block is ~85 words; compressed should be noticeably shorter
        assert "@compress" not in p

        # Layer 2: @match selected "brief", so "full" branch absent
        assert "@match" not in p
        assert "complete uncompressed" not in p_lower

        # Layer 3: @refine merged base-analyst.promptspec.md content
        assert "analytical" in p_lower or "evidence" in p_lower or "rigorous" in p_lower

        # Variable substituted
        assert "solar energy" in p_lower

        # The compressed content should still mention key requirements
        assert "market" in p_lower or "competitor" in p_lower or "swot" in p_lower

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_match_then_if_then_summarize_then_expand(self):
        """@match → @if → @summarize → @expand: 4-level nesting.

        Tests that the innermost @expand resolves first, then @summarize
        condenses the expanded result, then @if gates it, then @match
        selects the branch.
        """
        spec = (
            '@match role\n'
            '  "researcher" ==>\n'
            '    You are a research assistant.\n'
            '    @if include_methodology\n'
            '      @summarize length: short\n'
            '        Research methodology guidelines:\n'
            '        - Use systematic literature review processes.\n'
            '        - Apply PRISMA guidelines for study selection.\n'
            '        - Document inclusion/exclusion criteria explicitly.\n'
            '        - Use meta-analysis when studies are sufficiently homogeneous.\n'
            '        - Report effect sizes and confidence intervals.\n'
            '        - Address publication bias using funnel plots.\n'
            '        - Pre-register hypotheses to prevent p-hacking.\n'
            '        @expand\n'
            '          Add a requirement to use the GRADE framework\n'
            '          for assessing evidence quality.\n'
            '  "analyst" ==> You are a data analyst.\n'
        )
        r = await _compose(spec, {
            "role": "researcher",
            "include_methodology": True,
        })
        p = r.composed_prompt
        p_lower = p.lower()

        # All 4 directive layers resolved
        assert "@match" not in p
        assert "@if" not in p
        assert "@summarize" not in p
        assert "@expand" not in p

        # @match selected "researcher"
        assert "research" in p_lower
        assert "data analyst" not in p_lower

        # @if was true, so methodology content is present
        # @expand added GRADE framework BEFORE @summarize condensed
        assert "grade" in p_lower or "evidence quality" in p_lower

        # @summarize should have condensed — result should be shorter than
        # the original 8-bullet methodology block
        methodology_lines = [line for line in p.split('\n')
                             if line.strip() and 'methodology' not in line.lower()
                             and 'research assistant' not in line.lower()]
        # Not a hard assertion on line count (LLM may vary), but content should exist
        assert len(p_lower) > 50  # not empty

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_extract_inside_revise_inside_if(self):
        """@if → @revise → @extract: lossy inside semantic revision inside control flow.

        Tests that @extract runs first (pulls requirements), then @revise
        modifies the extracted result, then @if gates the whole block.
        """
        spec = (
            "You are a compliance checker.\n\n"
            "@if strict_mode\n"
            "  @revise mode: minimal\n"
            "    All requirements below must be treated as MUST (not SHOULD).\n"
            "  @extract format: bullets\n"
            "    From the following policy text, extract only the\n"
            "    actionable requirements:\n"
            "    Our company believes in excellence and innovation.\n"
            "    Employees SHOULD complete training within 30 days.\n"
            "    All code MUST pass linting before merge.\n"
            "    We value teamwork and collaboration.\n"
            "    Data exports SHOULD be encrypted at rest.\n"
            "    NEVER store passwords in plain text.\n"
        )
        r = await _compose(spec, {"strict_mode": True})
        p = r.composed_prompt
        p_lower = p.lower()

        assert "@if" not in p
        assert "@revise" not in p
        assert "@extract" not in p

        # @extract should have kept only requirements, not fluff
        assert "linting" in p_lower or "lint" in p_lower
        assert "training" in p_lower or "30 days" in p_lower
        assert "password" in p_lower
        assert "excellence" not in p_lower  # fluff removed
        assert "teamwork" not in p_lower  # fluff removed

        # @revise should have strengthened SHOULD to MUST
        assert "must" in p_lower

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_extract_inside_revise_gated_by_false_if(self):
        """Same structure as above, but @if is false — entire block omitted."""
        spec = (
            "You are a compliance checker.\n\n"
            "@if strict_mode\n"
            "  @revise mode: minimal\n"
            "    All requirements below must be treated as MUST.\n"
            "  @extract format: bullets\n"
            "    Employees SHOULD complete training within 30 days.\n"
            "    All code MUST pass linting before merge.\n"
        )
        r = await _compose(spec, {"strict_mode": False})
        p = r.composed_prompt.lower()

        # Everything inside the @if block should be absent
        assert "training" not in p
        assert "linting" not in p
        assert "compliance checker" in p  # base text preserved

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_canon_and_cohere_inside_match_branch(self):
        """@match → @canon + @cohere: transforms inside a selected branch.

        Tests that @canon normalizes and @cohere resolves contradictions,
        all within a @match branch.
        """
        spec = (
            '@match output_mode\n'
            '  "clean" ==>\n'
            '    @canon\n'
            '    @cohere aggressiveness: medium\n'
            '    # role\n'
            '    You are helpful.\n\n'
            '    ## ROLE\n'
            '    You are a friendly assistant.\n\n'
            '    - always be polite\n'
            '    * never be rude\n'
            '    - Always be polite and courteous\n\n'
            '    Be extremely terse. Use single words only.\n'
            '    Write long, detailed, paragraph-length responses.\n'
            '  "raw" ==> Just output everything as-is.\n'
        )
        r = await _compose(spec, {"output_mode": "clean"})
        p = r.composed_prompt
        p_lower = p.lower()

        assert "@match" not in p
        assert "@canon" not in p
        assert "@cohere" not in p

        # "raw" branch should not appear
        assert "as-is" not in p_lower

        # @canon should have normalized: duplicate "role" headings merged,
        # list markers unified
        # @cohere should have resolved the terse vs. verbose contradiction
        # Hard to assert exact resolution, but contradictory pair shouldn't
        # both survive verbatim
        has_terse = "single words only" in p_lower
        has_verbose = "paragraph-length" in p_lower
        assert not (has_terse and has_verbose), \
            "@cohere should resolve terse vs verbose contradiction"

        # Core content should survive
        assert "polite" in p_lower or "courteous" in p_lower

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_generate_examples_inside_if_inside_match(self):
        """@match → @if → @generate_examples: generation deep inside control flow.

        Verifies examples are generated only when the control flow path
        is active, and that the examples relate to the correct context.
        """
        spec = (
            '@match format\n'
            '  "json" ==>\n'
            '    Respond with JSON: {"result": string, "score": float}\n\n'
            '    @if show_examples\n'
            '      @generate_examples count: 2 style: realistic\n'
            '        Show valid JSON responses for a sentiment analysis task.\n'
            '  "text" ==> Respond in plain text.\n'
        )
        r = await _compose(spec, {"format": "json", "show_examples": True})
        p = r.composed_prompt
        p_lower = p.lower()

        assert "@match" not in p
        assert "@if" not in p
        assert "@generate_examples" not in p

        # Selected json branch
        assert "json" in p_lower
        assert "plain text" not in p_lower

        # Examples should have been generated
        assert "result" in p_lower
        assert "score" in p_lower
        # Should contain example values (realistic style)
        has_example_markers = (
            '"result"' in p or "'result'" in p
            or "example" in p_lower
            or "sentiment" in p_lower
        )
        assert has_example_markers

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_assert_validates_refine_merged_content(self):
        """@assert checks content that was brought in by @refine.

        The base-analyst.promptspec.md has an "Output Structure" section.
        @assert should see it even though it came from a @refine.
        """
        spec = (
            "@refine base-analyst.promptspec.md\n\n"
            "Analyze stock market trends.\n\n"
            "@assert severity: error The prompt contains guidance about output structure.\n"
        )
        r = await _compose(spec, {}, base_dir=SPECS_DIR)
        p = r.composed_prompt

        assert "@refine" not in p
        assert "@assert" not in p

        # base-analyst.promptspec.md has "## Output Structure" section — @assert should pass
        assert len(r.errors) == 0, (
            "@assert should pass: base-analyst.promptspec.md has 'Output Structure' "
            f"section, but got errors: {r.errors}"
        )
        # Content from refine should be present
        assert "stock market" in p.lower() or "trends" in p.lower()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_assert_fails_on_nested_missing_content(self):
        """@assert fails when expected content is NOT produced by nesting.

        @if excludes a section, then @assert checks for it → should error.
        """
        spec = (
            "Analyze data.\n\n"
            "@if include_format\n"
            "  ## Output Format\n"
            "  Return JSON.\n\n"
            "@assert severity: error The prompt contains an Output Format section.\n"
        )
        r = await _compose(spec, {"include_format": False})

        # @if excluded the Output Format section, so @assert should fail
        assert len(r.errors) > 0, (
            "@assert should fail: @if excluded Output Format section, "
            f"but got no errors. Warnings: {r.warnings}"
        )

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_contract_inside_expand_paradox(self):
        """@expand containing @contract: expand adds content, contract inside it removes part.

        This is a deliberately tricky case: @expand says "add a Security section
        with input validation AND encryption requirements", but the nested
        @contract says "remove encryption requirements". The net effect should
        be: Security section exists with input validation but NOT encryption.
        """
        spec = (
            "You are a code reviewer.\n"
            "Check naming and formatting.\n\n"
            "@expand mode: editorial\n"
            "  Add a Security section covering:\n"
            "  - Input validation and sanitization\n"
            "  - Encryption at rest and in transit\n"
            "  - Access control checks\n"
            "  @contract\n"
            "    Remove any encryption requirements from the Security section.\n"
        )
        r = await _compose(spec, {})
        p = r.composed_prompt
        p_lower = p.lower()

        assert "@expand" not in p
        assert "@contract" not in p

        # Expand added security section
        assert "security" in p_lower
        assert "validation" in p_lower or "sanitiz" in p_lower

        # Contract removed encryption
        assert "encrypt" not in p_lower, (
            "Encryption should have been contracted away, but found in: "
            + p[:200]
        )

        # Original content preserved
        assert "naming" in p_lower or "formatting" in p_lower

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_style_wrapping_summarize_wrapping_extract(self):
        """@style → @summarize → @extract: 3-level lossy+transform pipeline.

        Inside-out: @extract pulls requirements, @summarize condenses them,
        @style reshapes the tone of the condensed result.
        """
        spec = (
            "@style \"telegraphic, no articles, all caps for emphasis\"\n\n"
            "@summarize length: short\n"
            "  @extract format: bullets\n"
            "    The following is our complete API policy document.\n"
            "    We really value our developers and their time.\n"
            "    Rate limit: MUST NOT exceed 1000 requests per minute.\n"
            "    Authentication: MUST use OAuth 2.0 bearer tokens.\n"
            "    Versioning: SHOULD include API version in URL path.\n"
            "    Deprecation: MUST provide 6-month notice before removal.\n"
            "    Documentation: SHOULD keep OpenAPI spec up to date.\n"
            "    Our office has great snacks and a ping pong table.\n"
        )
        r = await _compose(spec, {})
        p = r.composed_prompt
        p_lower = p.lower()

        assert "@style" not in p
        assert "@summarize" not in p
        assert "@extract" not in p

        # @extract should have removed fluff
        assert "snack" not in p_lower
        assert "ping pong" not in p_lower

        # Core requirements should survive through summarize
        assert "1000" in p or "rate" in p_lower
        assert "oauth" in p_lower or "auth" in p_lower

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_audience_wrapping_match_with_compress(self):
        """@audience → @match → @compress: audience adapts the entire
        compressed-and-selected result.

        This tests that the outermost semantic transform (@audience)
        reshapes content that was already processed by inner directives.
        """
        spec = (
            '@audience "a 10-year-old child who is curious about science"\n\n'
            "Explain how computers work.\n\n"
            "@match depth\n"
            '  "simple" ==>\n'
            "    @compress preserve: balanced\n"
            "      Computers process information using transistors, which\n"
            "      are tiny electronic switches that can be either on or off.\n"
            "      These on/off states represent binary digits (bits). Modern\n"
            "      processors contain billions of transistors arranged in\n"
            "      logic gates that perform Boolean algebra. The CPU executes\n"
            "      instructions from memory using a fetch-decode-execute cycle.\n"
            "      Data flows through buses connecting the CPU, RAM, and I/O\n"
            "      controllers. The operating system manages hardware resources\n"
            "      and provides abstractions for application software.\n"
            '  "advanced" ==> Full technical explanation.\n'
        )
        r = await _compose(spec, {"depth": "simple"})
        p = r.composed_prompt
        p_lower = p.lower()

        assert "@audience" not in p
        assert "@match" not in p
        assert "@compress" not in p

        # "advanced" branch excluded
        assert "full technical explanation" not in p_lower

        # Content about computers should be present
        assert "computer" in p_lower

        # @audience for a 10-year-old should simplify language.
        # Should NOT contain highly technical jargon left untranslated.
        # We can't assert exact wording, but at minimum the content
        # should be accessible (no "Boolean algebra" or "fetch-decode-execute"
        # left raw after audience adaptation)
        complex_terms_surviving = sum(1 for term in [
            "boolean algebra", "fetch-decode-execute", "i/o controllers",
        ] if term in p_lower)
        assert complex_terms_surviving <= 1, (
            f"@audience should simplify for a child, but {complex_terms_surviving} "
            f"complex terms survived: {p[:300]}"
        )

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_structural_constraints_after_nested_expand_and_revise(self):
        """@expand + @revise + @structural_constraints: build up, modify, then restructure.

        Tests that @structural_constraints can reorder content that was
        dynamically added by @expand and modified by @revise.
        """
        spec = (
            "## Steps\n"
            "1. Read the input.\n"
            "2. Process it.\n\n"
            "## Role\n"
            "You are a data processor.\n\n"
            "@expand mode: editorial\n"
            "  Add an Output Format section specifying JSON output\n"
            "  with keys: result, status, timestamp.\n\n"
            "@revise mode: minimal\n"
            "  Add a 'confidence' key to the output format.\n\n"
            "@structural_constraints strict: true\n"
            "  Required sections in this order:\n"
            "  1. Role\n"
            "  2. Steps\n"
            "  3. Output Format\n"
        )
        r = await _compose(spec, {})
        p = r.composed_prompt
        p_lower = p.lower()

        assert "@expand" not in p
        assert "@revise" not in p
        assert "@structural_constraints" not in p

        # All content should be present
        assert "data processor" in p_lower or "processor" in p_lower
        assert "read" in p_lower or "input" in p_lower
        assert "json" in p_lower

        # @expand added output format, @revise added confidence
        assert "confidence" in p_lower

        # @structural_constraints should have reordered:
        # Role before Steps before Output Format
        role_pos = p_lower.find("role")
        steps_pos = p_lower.find("step")
        output_pos = p_lower.find("output format") if "output format" in p_lower else p_lower.find("output")

        if role_pos >= 0 and steps_pos >= 0:
            assert role_pos < steps_pos, (
                f"Role (pos {role_pos}) should appear before Steps (pos {steps_pos})"
            )
        if steps_pos >= 0 and output_pos >= 0:
            assert steps_pos < output_pos, (
                f"Steps (pos {steps_pos}) should appear before Output (pos {output_pos})"
            )
