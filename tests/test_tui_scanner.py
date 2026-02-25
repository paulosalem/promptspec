"""Tests for promptspec.tui.scanner — spec metadata extraction."""

import pytest
from promptspec.tui.scanner import scan_spec, SpecInput, SpecMetadata


# ═══════════════════════════════════════════════════════════════════
# Minimal spec fixtures
# ═══════════════════════════════════════════════════════════════════

SPEC_SIMPLE = """\
# My Spec

A simple spec for testing.

Hello {{name}}, welcome to {{place}}.
"""

SPEC_MULTILINE_VARS = """\
# Writer

Write about {{topic}}.

Here is the {{description}} of what we need.

The {{body}} goes here.
"""

SPEC_MATCH = """\
# Matcher

@match language
  "python" ==> Use Python style.
  "typescript" ==> Use TypeScript style.
  "rust" ==> Use Rust style.
  _ ==> Use generic style.

Write {{topic}} code.
"""

SPEC_IF = """\
# Conditional

@if include_tests
  Also generate unit tests.

@if verbose_output
  Include detailed explanations.

Analyze {{project_name}}.
"""

SPEC_EMBED_FILE_VAR = """\
# Embed Test

@embed file: {{input_file}}

Process the text above.
"""

SPEC_EMBED_STATIC = """\
# Embed Static

@embed file: samples/data.txt

@embed file: docs/readme.md

Process both files.
"""

SPEC_EXECUTE = """\
# Strategy Spec

@execute reflection
  max_iterations: 3
  temperature: 0.7

@prompt generate
Generate something about {{topic}}.

@prompt critique
Critique the above.

@prompt revise
Revise based on critique.
"""

SPEC_TOOLS = """\
# Tool Spec

@tool web_search
@tool calculator

@if use_database
  @tool sql_query

Solve {{problem}}.
"""

SPEC_ASSERT = """\
# Validated Spec

@assert severity: error The response must include citations.
@assert severity: warning The response should be under 500 words.

Write about {{topic}}.
"""

SPEC_NOTE_NEAR_VAR = """\
# With Notes

@note
  The focus should describe what characteristics to look for.

What is the {{focus}} of this analysis?

@note
  Choose a language from the supported list.

Code in {{language}}.
"""

SPEC_REFINE = """\
# Refined Spec

@refine base-analyst.promptspec.md

@refine {{custom_base}}

Analyze {{topic}}.
"""

SPEC_SUMMARIZE_FILE = """\
# Summarizer

@summarize file: {{source_doc}}

Summarize the above.
"""

SPEC_COLLABORATIVE = """\
# Collaborative Writer

@execute collaborative
  max_rounds: 5

@prompt generate
Write about {{topic}} in {{tone}} tone.

@prompt continue
The user edited the content.
Original: {{original_content}}
Edited: {{edited_content}}
Continue.
"""

SPEC_COMPRESS_EXTRACT = """\
# Multi-directive

@compress file: {{compress_input}}

@extract file: {{extract_input}}

Process.
"""

SPEC_COMPLEX = """\
# Complex Spec

A real-world-like spec with many features.

@refine base-analyst.promptspec.md

@execute reflection
  max_iterations: 2

@prompt generate
@prompt critique
@prompt revise

@tool web_search

@match output_format
  "json" ==> Produce JSON output.
  "markdown" ==> Produce Markdown output.
  _ ==> Produce plain text.

@if include_citations
  Always include citations.

@embed file: samples/data.txt

@note
  Describe what you want analyzed.

Analyze {{topic}} with focus on {{description}}.

@assert severity: error Must include at least 3 examples.
"""


# ═══════════════════════════════════════════════════════════════════
# Tests
# ═══════════════════════════════════════════════════════════════════

class TestScanSpec:
    """Core scan_spec() tests."""

    def test_simple_vars(self):
        meta = scan_spec(SPEC_SIMPLE)
        assert meta.title == "My Spec"
        names = [i.name for i in meta.inputs]
        assert "name" in names
        assert "place" in names
        assert all(i.input_type == "text" for i in meta.inputs)

    def test_multiline_heuristic(self):
        meta = scan_spec(SPEC_MULTILINE_VARS)
        types = {i.name: i.input_type for i in meta.inputs}
        assert types["topic"] == "text"
        assert types["description"] == "multiline"
        assert types["body"] == "multiline"

    def test_match_directive(self):
        meta = scan_spec(SPEC_MATCH)
        lang_input = next(i for i in meta.inputs if i.name == "language")
        assert lang_input.input_type == "select"
        assert "python" in lang_input.options
        assert "typescript" in lang_input.options
        assert "rust" in lang_input.options
        assert "_" in lang_input.options  # wildcard
        assert lang_input.source_directive == "@match"

    def test_if_directive(self):
        meta = scan_spec(SPEC_IF)
        bools = [i for i in meta.inputs if i.input_type == "boolean"]
        names = {i.name for i in bools}
        assert "include_tests" in names
        assert "verbose_output" in names
        assert all(i.source_directive == "@if" for i in bools)

    def test_embed_file_variable(self):
        meta = scan_spec(SPEC_EMBED_FILE_VAR)
        file_input = next(i for i in meta.inputs if i.name == "input_file")
        assert file_input.input_type == "file"
        assert file_input.source_directive == "@embed"
        assert "Supports:" in file_input.file_hint

    def test_embed_static_files(self):
        meta = scan_spec(SPEC_EMBED_STATIC)
        assert "samples/data.txt" in meta.embed_files
        assert "docs/readme.md" in meta.embed_files
        # No file inputs should be created for static paths
        assert len(meta.inputs) == 0

    def test_execute_metadata(self):
        meta = scan_spec(SPEC_EXECUTE)
        assert meta.execution is not None
        assert meta.execution["type"] == "reflection"
        assert meta.execution["max_iterations"] == 3
        assert meta.execution["temperature"] == 0.7

    def test_prompt_names(self):
        meta = scan_spec(SPEC_EXECUTE)
        assert "generate" in meta.prompt_names
        assert "critique" in meta.prompt_names
        assert "revise" in meta.prompt_names

    def test_tool_names(self):
        meta = scan_spec(SPEC_TOOLS)
        assert "web_search" in meta.tool_names
        assert "calculator" in meta.tool_names
        assert "sql_query" in meta.tool_names

    def test_assertions(self):
        meta = scan_spec(SPEC_ASSERT)
        assert len(meta.assertions) == 2
        assert any("citations" in a for a in meta.assertions)

    def test_note_hints(self):
        meta = scan_spec(SPEC_NOTE_NEAR_VAR)
        focus_input = next(i for i in meta.inputs if i.name == "focus")
        assert focus_input.description is not None
        assert "characteristics" in focus_input.description

    def test_refine_static(self):
        meta = scan_spec(SPEC_REFINE)
        assert "base-analyst.promptspec.md" in meta.refine_files

    def test_refine_variable(self):
        meta = scan_spec(SPEC_REFINE)
        file_input = next(i for i in meta.inputs if i.name == "custom_base")
        assert file_input.input_type == "file"
        assert file_input.source_directive == "@refine"

    def test_summarize_file_var(self):
        meta = scan_spec(SPEC_SUMMARIZE_FILE)
        file_input = next(i for i in meta.inputs if i.name == "source_doc")
        assert file_input.input_type == "file"
        assert file_input.source_directive == "@summarize"

    def test_compress_extract_file_vars(self):
        meta = scan_spec(SPEC_COMPRESS_EXTRACT)
        names = {i.name: i for i in meta.inputs}
        assert names["compress_input"].input_type == "file"
        assert names["compress_input"].source_directive == "@compress"
        assert names["extract_input"].input_type == "file"
        assert names["extract_input"].source_directive == "@extract"

    def test_collaborative_filters_internal_vars(self):
        """Internal strategy vars like edited_content/original_content are excluded."""
        meta = scan_spec(SPEC_COLLABORATIVE)
        names = {i.name for i in meta.inputs}
        assert "topic" in names
        assert "tone" in names
        assert "edited_content" not in names
        assert "original_content" not in names

    def test_description_extraction(self):
        meta = scan_spec(SPEC_SIMPLE)
        assert "simple spec" in meta.description.lower()

    def test_has_notes(self):
        meta = scan_spec(SPEC_NOTE_NEAR_VAR)
        assert meta.has_notes is True
        meta2 = scan_spec(SPEC_SIMPLE)
        assert meta2.has_notes is False

    def test_no_duplicate_inputs(self):
        """Each variable name appears at most once in the inputs list."""
        meta = scan_spec(SPEC_COMPLEX)
        names = [i.name for i in meta.inputs]
        assert len(names) == len(set(names))

    def test_complex_spec_coverage(self):
        """A complex spec should discover all input types."""
        meta = scan_spec(SPEC_COMPLEX)
        types = {i.name: i.input_type for i in meta.inputs}
        assert types["output_format"] == "select"
        assert types["include_citations"] == "boolean"
        assert types["topic"] == "text"
        assert types["description"] == "multiline"
        # Metadata
        assert meta.execution["type"] == "reflection"
        assert "generate" in meta.prompt_names
        assert "web_search" in meta.tool_names
        assert "base-analyst.promptspec.md" in meta.refine_files
        assert "samples/data.txt" in meta.embed_files
        assert len(meta.assertions) == 1
        assert meta.has_notes

    def test_empty_spec(self):
        meta = scan_spec("")
        assert meta.title == ""
        assert meta.inputs == []
        assert meta.execution is None

    def test_input_priority_order(self):
        """@match and @if are detected before generic {{vars}} — no duplicates."""
        spec = """\
# Priority

@match mode
  "fast" ==> speed
  "slow" ==> accuracy

@if debug

{{mode}} {{debug}} {{other}}
"""
        meta = scan_spec(spec)
        mode_input = next(i for i in meta.inputs if i.name == "mode")
        debug_input = next(i for i in meta.inputs if i.name == "debug")
        assert mode_input.input_type == "select"
        assert debug_input.input_type == "boolean"
        assert len([i for i in meta.inputs if i.name == "mode"]) == 1
        assert len([i for i in meta.inputs if i.name == "debug"]) == 1


class TestSpecInputDataclass:
    """SpecInput dataclass basics."""

    def test_defaults(self):
        inp = SpecInput(name="x", input_type="text")
        assert inp.options is None
        assert inp.default is None
        assert inp.description is None
        assert inp.file_hint is None
        assert inp.source_directive is None

    def test_full_init(self):
        inp = SpecInput(
            name="lang",
            input_type="select",
            options=["python", "rust"],
            default="python",
            description="Pick a language",
            file_hint=None,
            source_directive="@match",
        )
        assert inp.options == ["python", "rust"]
        assert inp.default == "python"


class TestSpecMetadataDataclass:
    """SpecMetadata dataclass basics."""

    def test_defaults(self):
        meta = SpecMetadata()
        assert meta.title == ""
        assert meta.inputs == []
        assert meta.execution is None
        assert meta.prompt_names == []
        assert meta.tool_names == []
