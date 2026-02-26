"""Tests for the spec catalog indexer."""

from __future__ import annotations

from pathlib import Path

import pytest

from promptspec.discovery.catalog import (
    SpecEntry,
    _content_hash,
    _extract_title,
    index_spec,
    scan_directories,
)

SIMPLE_SPEC = """\
# My Test Spec

You are a helpful assistant.

Analyze {{topic}} for {{audience}}.

@match depth
  "quick" ==> Be brief.
  "deep" ==> Be thorough.
"""

SPEC_WITH_EXECUTE = """\
# Tree Solver

@execute tree-of-thought
  max_depth: 3

Solve {{problem}}.

@tool search_web
  Search the web.
  - query: string (required)
"""

SPEC_NO_HEADING = """\
You are a simple prompt with no heading.

Help with {{task}}.
"""


class TestExtractTitle:
    def test_normal_heading(self):
        assert _extract_title("# Hello World\nBody") == "Hello World"

    def test_no_heading(self):
        assert _extract_title("Just text\nMore text") == ""

    def test_skips_non_h1(self):
        assert _extract_title("## Not H1\n# Real Title") == "Real Title"


class TestContentHash:
    def test_deterministic(self):
        h1 = _content_hash("hello")
        h2 = _content_hash("hello")
        assert h1 == h2

    def test_different_content(self):
        assert _content_hash("a") != _content_hash("b")

    def test_returns_hex(self):
        h = _content_hash("test")
        assert len(h) == 64  # sha256 hex


class TestIndexSpec:
    def test_simple_spec(self, tmp_path):
        p = tmp_path / "test.promptspec.md"
        p.write_text(SIMPLE_SPEC)
        entry = index_spec(p)
        assert entry.title == "My Test Spec"
        assert "topic" in entry.variables
        assert "audience" in entry.variables
        assert entry.execution_strategy is None
        assert not entry.has_tools
        assert entry.content_hash

    def test_spec_with_execute_and_tools(self, tmp_path):
        p = tmp_path / "solver.promptspec.md"
        p.write_text(SPEC_WITH_EXECUTE)
        entry = index_spec(p)
        assert entry.title == "Tree Solver"
        assert entry.has_tools
        assert "problem" in entry.variables

    def test_no_heading_uses_stem(self, tmp_path):
        p = tmp_path / "bare.promptspec.md"
        p.write_text(SPEC_NO_HEADING)
        entry = index_spec(p)
        assert entry.title == "bare"

    def test_short_name(self, tmp_path):
        p = tmp_path / "my-spec.promptspec.md"
        p.write_text(SIMPLE_SPEC)
        entry = index_spec(p)
        assert entry.short_name == "my-spec"

    def test_filename(self, tmp_path):
        p = tmp_path / "test.promptspec.md"
        p.write_text(SIMPLE_SPEC)
        entry = index_spec(p)
        assert entry.filename == "test.promptspec.md"


class TestScanDirectories:
    def test_finds_specs_recursively(self, tmp_path):
        (tmp_path / "a.promptspec.md").write_text(SIMPLE_SPEC)
        sub = tmp_path / "sub"
        sub.mkdir()
        (sub / "b.promptspec.md").write_text(SPEC_WITH_EXECUTE)
        entries = scan_directories([tmp_path])
        assert len(entries) == 2
        names = {e.filename for e in entries}
        assert "a.promptspec.md" in names
        assert "b.promptspec.md" in names

    def test_skips_non_spec_files(self, tmp_path):
        (tmp_path / "readme.md").write_text("# Not a spec")
        (tmp_path / "test.promptspec.md").write_text(SIMPLE_SPEC)
        entries = scan_directories([tmp_path])
        assert len(entries) == 1

    def test_deduplicates(self, tmp_path):
        (tmp_path / "a.promptspec.md").write_text(SIMPLE_SPEC)
        entries = scan_directories([tmp_path, tmp_path])
        assert len(entries) == 1

    def test_skips_missing_dirs(self, tmp_path):
        missing = tmp_path / "nonexistent"
        entries = scan_directories([missing])
        assert entries == []

    def test_skips_unparsable_files(self, tmp_path):
        bad = tmp_path / "bad.promptspec.md"
        bad.write_text("")  # empty but should not crash
        (tmp_path / "good.promptspec.md").write_text(SIMPLE_SPEC)
        entries = scan_directories([tmp_path])
        # At minimum the good one should be there
        assert any(e.filename == "good.promptspec.md" for e in entries)

    def test_multiple_dirs(self, tmp_path):
        d1 = tmp_path / "dir1"
        d2 = tmp_path / "dir2"
        d1.mkdir()
        d2.mkdir()
        (d1 / "a.promptspec.md").write_text(SIMPLE_SPEC)
        (d2 / "b.promptspec.md").write_text(SPEC_WITH_EXECUTE)
        entries = scan_directories([d1, d2])
        assert len(entries) == 2
