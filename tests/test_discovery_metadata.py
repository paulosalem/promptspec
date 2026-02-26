"""Tests for the LLM metadata cache."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from promptspec.discovery.catalog import SpecEntry
from promptspec.discovery.metadata import (
    SpecMetadataEntry,
    _is_cached,
    _load_cache,
    _save_cache,
    ensure_metadata,
)


def _make_entry(tmp_path: Path, name: str = "test", content: str = "# Test\n") -> SpecEntry:
    from promptspec.discovery.catalog import _content_hash
    return SpecEntry(
        path=tmp_path / f"{name}.promptspec.md",
        title="Test Spec",
        content_hash=_content_hash(content),
        variables=["topic"],
        raw_text=content,
    )


class TestCacheIO:
    def test_load_missing_returns_empty(self, tmp_path, monkeypatch):
        monkeypatch.setattr("promptspec.discovery.metadata.CACHE_FILE", tmp_path / "missing.json")
        assert _load_cache() == {}

    def test_save_and_load(self, tmp_path, monkeypatch):
        cache_file = tmp_path / "cache.json"
        monkeypatch.setattr("promptspec.discovery.metadata.CACHE_FILE", cache_file)
        monkeypatch.setattr("promptspec.discovery.metadata.GLOBAL_DIR", tmp_path)

        data = {"key": {"content_hash": "abc", "title": "T"}}
        _save_cache(data)
        assert cache_file.is_file()
        loaded = _load_cache()
        assert loaded == data

    def test_load_corrupt_returns_empty(self, tmp_path, monkeypatch):
        cache_file = tmp_path / "bad.json"
        cache_file.write_text("NOT JSON!!!")
        monkeypatch.setattr("promptspec.discovery.metadata.CACHE_FILE", cache_file)
        assert _load_cache() == {}


class TestIsCached:
    def test_not_in_cache(self, tmp_path):
        entry = _make_entry(tmp_path)
        assert _is_cached({}, entry) is False

    def test_hash_matches(self, tmp_path):
        entry = _make_entry(tmp_path)
        cache = {str(entry.path): {"content_hash": entry.content_hash}}
        assert _is_cached(cache, entry) is True

    def test_hash_mismatch(self, tmp_path):
        entry = _make_entry(tmp_path)
        cache = {str(entry.path): {"content_hash": "stale_hash"}}
        assert _is_cached(cache, entry) is False


class TestEnsureMetadata:
    @pytest.mark.asyncio
    async def test_all_cached_skips_llm(self, tmp_path, monkeypatch):
        """If all entries are cached, no LLM calls are made."""
        cache_file = tmp_path / "cache.json"
        monkeypatch.setattr("promptspec.discovery.metadata.CACHE_FILE", cache_file)
        monkeypatch.setattr("promptspec.discovery.metadata.GLOBAL_DIR", tmp_path)

        entry = _make_entry(tmp_path)
        cache = {
            str(entry.path): {
                "content_hash": entry.content_hash,
                "title": "Test Spec",
                "summary": "cached summary",
                "category": "general",
                "tags": ["test"],
                "difficulty": "beginner",
                "variables": ["topic"],
                "execution_strategy": None,
                "has_tools": False,
                "computed_at": "2026-01-01T00:00:00Z",
            }
        }
        cache_file.write_text(json.dumps(cache))

        result = await ensure_metadata([entry])
        assert str(entry.path) in result
        assert result[str(entry.path)].summary == "cached summary"

    @pytest.mark.asyncio
    async def test_uncached_calls_llm(self, tmp_path, monkeypatch):
        """Uncached entries trigger LLM analysis."""
        cache_file = tmp_path / "cache.json"
        monkeypatch.setattr("promptspec.discovery.metadata.CACHE_FILE", cache_file)
        monkeypatch.setattr("promptspec.discovery.metadata.GLOBAL_DIR", tmp_path)

        entry = _make_entry(tmp_path)

        async def mock_analyze(e, model="gpt-4.1"):
            return SpecMetadataEntry(
                content_hash=e.content_hash,
                title=e.title,
                summary="A test spec for testing.",
                category="general",
                tags=["test", "demo"],
                difficulty="beginner",
                variables=e.variables,
                has_tools=e.has_tools,
                computed_at="2026-01-01T00:00:00Z",
            )

        with patch("promptspec.discovery.metadata._analyze_spec", side_effect=mock_analyze):
            result = await ensure_metadata([entry])

        meta = result[str(entry.path)]
        assert meta.summary == "A test spec for testing."
        assert meta.category == "general"
        assert "test" in meta.tags
        assert cache_file.is_file()

    @pytest.mark.asyncio
    async def test_llm_failure_falls_back(self, tmp_path, monkeypatch):
        """If LLM fails, basic metadata is still returned."""
        cache_file = tmp_path / "cache.json"
        monkeypatch.setattr("promptspec.discovery.metadata.CACHE_FILE", cache_file)
        monkeypatch.setattr("promptspec.discovery.metadata.GLOBAL_DIR", tmp_path)

        entry = _make_entry(tmp_path)

        with patch("promptspec.discovery.metadata._analyze_spec", side_effect=Exception("API error")):
            result = await ensure_metadata([entry])

        meta = result[str(entry.path)]
        assert meta.title == "Test Spec"
        assert meta.content_hash == entry.content_hash

    @pytest.mark.asyncio
    async def test_progress_callback(self, tmp_path, monkeypatch):
        """on_progress is called for each uncached spec."""
        cache_file = tmp_path / "cache.json"
        monkeypatch.setattr("promptspec.discovery.metadata.CACHE_FILE", cache_file)
        monkeypatch.setattr("promptspec.discovery.metadata.GLOBAL_DIR", tmp_path)

        entries = [_make_entry(tmp_path, f"s{i}") for i in range(3)]
        progress_calls = []

        with patch("promptspec.discovery.metadata._analyze_spec", side_effect=Exception("skip")):
            await ensure_metadata(
                entries,
                on_progress=lambda cur, total, title: progress_calls.append((cur, total)),
            )

        assert len(progress_calls) == 3
        assert progress_calls[0] == (1, 3)
        assert progress_calls[2] == (3, 3)

    @pytest.mark.asyncio
    async def test_hash_invalidation(self, tmp_path, monkeypatch):
        """Changed hash triggers re-analysis."""
        cache_file = tmp_path / "cache.json"
        monkeypatch.setattr("promptspec.discovery.metadata.CACHE_FILE", cache_file)
        monkeypatch.setattr("promptspec.discovery.metadata.GLOBAL_DIR", tmp_path)

        entry = _make_entry(tmp_path)
        cache = {str(entry.path): {"content_hash": "old_hash", "summary": "stale"}}
        cache_file.write_text(json.dumps(cache))

        with patch("promptspec.discovery.metadata._analyze_spec", side_effect=Exception("skip")):
            result = await ensure_metadata([entry])

        meta = result[str(entry.path)]
        assert meta.content_hash == entry.content_hash
        assert meta.summary == ""
