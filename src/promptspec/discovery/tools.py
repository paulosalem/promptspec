"""Discovery tool definitions and executor.

Follows ellements conventions: tools defined as OpenAI function-calling
dicts, executed via an async ``tool_executor(name, args) → str`` callback.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from promptspec.discovery.catalog import SpecEntry
from promptspec.discovery.metadata import SpecMetadataEntry


class SpecSelected(Exception):
    """Raised by select_spec to signal the chat loop should exit."""

    def __init__(self, spec_path: str) -> None:
        self.spec_path = spec_path
        super().__init__(f"Spec selected: {spec_path}")


# ── Tool definitions (OpenAI function-calling format) ──────────────

DISCOVERY_TOOLS: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "search_catalog",
            "description": (
                "Search the spec library by keyword. Returns matching specs "
                "with title, summary, tags, and variable list. "
                "Pass query='*' or query='' to list ALL available specs."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": (
                            "Search keywords or natural-language query. "
                            "Use '*' or '' to list all specs."
                        ),
                    },
                    "category": {
                        "type": "string",
                        "description": "Optional category filter (e.g. strategy, writing, coding).",
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_spec",
            "description": (
                "Read the full raw content of a specific spec file. "
                "Use this to understand a spec in detail before recommending it."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "spec_id": {
                        "type": "string",
                        "description": "The spec filename (e.g. crisis-strategy-analyzer.promptspec.md).",
                    },
                },
                "required": ["spec_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "select_spec",
            "description": (
                "Select a spec for the user to fill in and run. "
                "This ends the discovery conversation and launches the spec "
                "in the interactive TUI. Only call this when the user has "
                "confirmed they want to use a specific spec."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "spec_id": {
                        "type": "string",
                        "description": "The spec filename to launch.",
                    },
                },
                "required": ["spec_id"],
            },
        },
    },
]


# ── Tool executor factory ──────────────────────────────────────────

def create_tool_executor(
    entries: List[SpecEntry],
    metadata: Dict[str, SpecMetadataEntry],
):
    """Create a tool_executor callback for the discovery tools.

    Returns an async function ``(name, args) → str`` following
    the ellements convention.
    """
    # Build lookup tables
    by_filename: Dict[str, SpecEntry] = {}
    for e in entries:
        by_filename[e.filename] = e
        by_filename[e.short_name] = e

    async def tool_executor(name: str, args: Dict[str, Any]) -> str:
        if name == "search_catalog":
            return _search_catalog(entries, metadata, args)
        elif name == "read_spec":
            return _read_spec(by_filename, args)
        elif name == "select_spec":
            return _select_spec(by_filename, args)
        else:
            return f"Unknown tool: {name}"

    return tool_executor


def _search_catalog(
    entries: List[SpecEntry],
    metadata: Dict[str, SpecMetadataEntry],
    args: Dict[str, Any],
) -> str:
    """Fuzzy search over specs using query keywords.

    Special cases:
    - query='*' or query='' → list all specs (up to 25)
    - Broad/generic queries that match nothing → fall back to listing all
    """
    query = args.get("query", "").strip().lower()
    category_filter = args.get("category", "").strip().lower()

    list_all = query in ("", "*", "all", "list", "all specs", "list all")

    if list_all and not category_filter:
        # Return all specs (capped)
        return _format_results(entries, metadata, max_results=25)

    keywords = query.split() if not list_all else []

    scored: list[tuple[int, SpecEntry, Optional[SpecMetadataEntry]]] = []

    for entry in entries:
        key = str(entry.path)
        meta = metadata.get(key)

        # Build searchable text
        parts = [entry.title.lower(), entry.short_name.lower()]
        if meta:
            parts.extend([meta.summary.lower(), meta.category.lower()])
            parts.extend(t.lower() for t in meta.tags)
        parts.extend(v.lower() for v in entry.variables)

        searchable = " ".join(parts)

        # Category filter
        if category_filter and meta:
            if category_filter not in meta.category.lower():
                continue
        elif category_filter and not meta:
            continue

        # If listing all (with category filter), include everything that passed
        if list_all:
            scored.append((1, entry, meta))
            continue

        # Score: count keyword hits
        score = sum(1 for kw in keywords if kw in searchable)
        if score > 0:
            scored.append((score, entry, meta))

    # Sort by score descending
    scored.sort(key=lambda x: -x[0])
    top = scored[:25]

    if not top:
        # Fall back: return all specs so the user can browse
        return _format_results(entries, metadata, max_results=15,
                               header="No exact matches — here's what's available:")

    return _format_scored_results(top)


def _format_results(
    entries: List[SpecEntry],
    metadata: Dict[str, SpecMetadataEntry],
    max_results: int = 25,
    header: Optional[str] = None,
) -> str:
    """Format a list of spec entries as JSON."""
    results = []
    for entry in entries[:max_results]:
        key = str(entry.path)
        meta = metadata.get(key)
        item = {
            "filename": entry.filename,
            "title": entry.title,
        }
        if meta and meta.summary:
            item["summary"] = meta.summary
        if meta and meta.category:
            item["category"] = meta.category
        if meta and meta.tags:
            item["tags"] = meta.tags
        if entry.variables:
            item["variables"] = entry.variables
        results.append(item)

    out = json.dumps(results, indent=2, ensure_ascii=False)
    if header:
        out = header + "\n" + out
    return f"{len(entries)} specs available ({len(results)} shown):\n{out}"


def _format_scored_results(
    scored: list[tuple[int, SpecEntry, Optional[SpecMetadataEntry]]],
) -> str:
    """Format scored search results as JSON."""
    results = []
    for _, entry, meta in scored:
        item = {
            "filename": entry.filename,
            "title": entry.title,
            "variables": entry.variables,
        }
        if meta:
            item["summary"] = meta.summary
            item["category"] = meta.category
            item["tags"] = meta.tags
        if entry.execution_strategy:
            item["execution_strategy"] = entry.execution_strategy
        if entry.has_tools:
            item["has_tools"] = True
        results.append(item)

    return json.dumps(results, indent=2, ensure_ascii=False)


def _read_spec(
    by_filename: Dict[str, SpecEntry],
    args: Dict[str, Any],
) -> str:
    """Return the full raw content of a spec."""
    spec_id = args.get("spec_id", "")
    entry = by_filename.get(spec_id)
    if not entry:
        return f"Spec '{spec_id}' not found. Available: {', '.join(sorted(by_filename.keys()))}"
    return entry.raw_text


def _select_spec(
    by_filename: Dict[str, SpecEntry],
    args: Dict[str, Any],
) -> str:
    """Signal spec selection — raises SpecSelected to exit the chat loop."""
    spec_id = args.get("spec_id", "")
    entry = by_filename.get(spec_id)
    if not entry:
        return f"Spec '{spec_id}' not found. Available: {', '.join(sorted(by_filename.keys()))}"
    raise SpecSelected(str(entry.path))
