"""LLM-computed metadata cache for spec discovery.

For each spec, the LLM reads the raw text and produces a structured
summary (category, tags, one-line description, difficulty). Results
are cached in ``~/.promptspec/catalog-cache.json`` keyed by file path,
with SHA-256 hash invalidation so only new/changed specs are re-analyzed.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from promptspec.discovery.catalog import SpecEntry
from promptspec.discovery.config import GLOBAL_DIR


CACHE_FILE = GLOBAL_DIR / "catalog-cache.json"

ANALYZE_SYSTEM_PROMPT = """\
You are a metadata analyst for prompt specification files. Given a raw \
.promptspec.md file, produce a JSON object with these fields:

- "summary": A single sentence (max 120 chars) describing what this spec does.
- "category": One of: strategy, analysis, writing, coding, research, agent, \
game, education, data, finance, general.
- "tags": A list of 3-6 lowercase keyword tags.
- "difficulty": One of: beginner, intermediate, advanced.

Respond with ONLY the JSON object, no markdown fences or explanation.
"""


@dataclass
class SpecMetadataEntry:
    """Cached LLM-computed metadata for a single spec."""

    content_hash: str
    title: str
    summary: str = ""
    category: str = "general"
    tags: List[str] = field(default_factory=list)
    difficulty: str = "intermediate"
    variables: List[str] = field(default_factory=list)
    execution_strategy: Optional[str] = None
    has_tools: bool = False
    computed_at: str = ""


def _load_cache() -> Dict[str, Dict[str, Any]]:
    """Load the cache file, returning {} if missing or corrupt."""
    if not CACHE_FILE.is_file():
        return {}
    try:
        return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_cache(cache: Dict[str, Dict[str, Any]]) -> None:
    """Write the cache file, creating the directory if needed."""
    GLOBAL_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.write_text(
        json.dumps(cache, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def _is_cached(cache: Dict[str, Dict[str, Any]], entry: SpecEntry) -> bool:
    """Check if a spec is cached with a matching hash."""
    key = str(entry.path)
    if key not in cache:
        return False
    return cache[key].get("content_hash") == entry.content_hash


async def _analyze_spec(
    entry: SpecEntry,
    model: str = "gpt-4.1",
) -> SpecMetadataEntry:
    """Use the LLM to analyze a raw spec and produce metadata."""
    from ellements.core.clients import LLMClient

    client = LLMClient(model=model, temperature=0.1)

    # Truncate very long specs to save tokens
    raw = entry.raw_text[:8000]
    prompt = f"Analyze this prompt spec file:\n\n```\n{raw}\n```"

    response = await client.complete(
        messages=[
            {"role": "system", "content": ANALYZE_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
    )

    # Parse JSON from response
    text = response.text.strip()
    # Strip markdown fences if present
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        data = {}

    return SpecMetadataEntry(
        content_hash=entry.content_hash,
        title=entry.title,
        summary=data.get("summary", ""),
        category=data.get("category", "general"),
        tags=data.get("tags", []),
        difficulty=data.get("difficulty", "intermediate"),
        variables=entry.variables,
        execution_strategy=entry.execution_strategy,
        has_tools=entry.has_tools,
        computed_at=datetime.now(timezone.utc).isoformat(),
    )


async def ensure_metadata(
    entries: List[SpecEntry],
    model: str = "gpt-4.1",
    on_progress: Optional[Callable[[int, int, str], None]] = None,
) -> Dict[str, SpecMetadataEntry]:
    """Ensure all specs have up-to-date LLM metadata, computing as needed.

    Parameters
    ----------
    entries : list of SpecEntry
        All indexed specs.
    model : str
        LLM model to use for analysis.
    on_progress : callable, optional
        Called with (current, total, spec_title) during analysis.

    Returns
    -------
    dict mapping file path (str) to SpecMetadataEntry
    """
    cache = _load_cache()
    result: Dict[str, SpecMetadataEntry] = {}
    to_analyze: List[SpecEntry] = []

    # Separate cached vs. needing analysis
    for entry in entries:
        key = str(entry.path)
        if _is_cached(cache, entry):
            # Reconstruct from cache
            d = cache[key]
            result[key] = SpecMetadataEntry(
                content_hash=d.get("content_hash", ""),
                title=d.get("title", entry.title),
                summary=d.get("summary", ""),
                category=d.get("category", "general"),
                tags=d.get("tags", []),
                difficulty=d.get("difficulty", "intermediate"),
                variables=d.get("variables", entry.variables),
                execution_strategy=d.get("execution_strategy"),
                has_tools=d.get("has_tools", False),
                computed_at=d.get("computed_at", ""),
            )
        else:
            to_analyze.append(entry)

    # Analyze uncached specs
    if to_analyze:
        for i, entry in enumerate(to_analyze):
            if on_progress:
                on_progress(i + 1, len(to_analyze), entry.title)
            try:
                meta = await _analyze_spec(entry, model=model)
            except Exception:
                # Fallback: basic metadata without LLM
                meta = SpecMetadataEntry(
                    content_hash=entry.content_hash,
                    title=entry.title,
                    variables=entry.variables,
                    execution_strategy=entry.execution_strategy,
                    has_tools=entry.has_tools,
                    computed_at=datetime.now(timezone.utc).isoformat(),
                )
            key = str(entry.path)
            result[key] = meta
            cache[key] = asdict(meta)

        _save_cache(cache)

    return result
