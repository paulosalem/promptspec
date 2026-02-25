"""Spec scanner — extract structured metadata from a .promptspec.md file.

Parses the spec text using **regex only** (no LLM call) to discover:
  - ``{{variables}}`` — text / multiline inputs
  - ``@match var`` cases — select dropdowns
  - ``@if var`` flags — boolean toggles
  - ``@embed file: {{var}}`` (and @refine, @summarize, @compress, @extract) — file inputs
  - ``@execute`` strategy — execution metadata
  - ``@prompt name`` — named prompts
  - ``@tool name`` — tool declarations
  - ``@assert`` — validation hints
  - ``@note`` near variables — help text

This module is intentionally LLM-free so it can run instantly for TUI form
generation, IDE integration, spec linting, and pre-flight checks.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional


# ═══════════════════════════════════════════════════════════════════
# Data classes
# ═══════════════════════════════════════════════════════════════════

@dataclass
class SpecInput:
    """A single user-facing input discovered in a spec."""

    name: str
    input_type: str  # "text", "multiline", "select", "boolean", "file"
    options: Optional[List[str]] = None
    default: Optional[str] = None
    description: Optional[str] = None
    file_hint: Optional[str] = None
    source_directive: Optional[str] = None  # which directive produced this


@dataclass
class SpecMetadata:
    """Structured metadata extracted from a .promptspec.md file."""

    title: str = ""
    description: str = ""
    inputs: List[SpecInput] = field(default_factory=list)
    execution: Optional[dict] = None
    prompt_names: List[str] = field(default_factory=list)
    tool_names: List[str] = field(default_factory=list)
    refine_files: List[str] = field(default_factory=list)
    embed_files: List[str] = field(default_factory=list)
    assertions: List[str] = field(default_factory=list)
    has_notes: bool = False


# ═══════════════════════════════════════════════════════════════════
# Regex patterns
# ═══════════════════════════════════════════════════════════════════

_MUSTACHE_VAR = re.compile(r"\{\{(\w+)\}\}")
_MATCH_DIRECTIVE = re.compile(r"^[ \t]*@match\s+(\w+)", re.MULTILINE)
_MATCH_CASE = re.compile(r'^[ \t]*"([^"]+)"\s*==>', re.MULTILINE)
_IF_DIRECTIVE = re.compile(r"^[ \t]*@if\s+(\w+)", re.MULTILINE)
_EXECUTE_DIRECTIVE = re.compile(
    r"^[ \t]*@execute\s+(\S+)((?:\n(?:[ \t]+\S.*))*)", re.MULTILINE
)
_PROMPT_DIRECTIVE = re.compile(r"^[ \t]*@prompt\s+(\w+)", re.MULTILINE)
_TOOL_DIRECTIVE = re.compile(r"^[ \t]*@tool\s+(\S+)", re.MULTILINE)
_REFINE_DIRECTIVE = re.compile(r"^[ \t]*@refine\s+(\S+)", re.MULTILINE)
_EMBED_FILE = re.compile(r"^[ \t]*@embed\s+file:\s*(\S+)", re.MULTILINE)
_SUMMARIZE_FILE = re.compile(r"^[ \t]*@summarize\s+file:\s*(\S+)", re.MULTILINE)
_COMPRESS_FILE = re.compile(r"^[ \t]*@compress\s+file:\s*(\S+)", re.MULTILINE)
_EXTRACT_FILE = re.compile(r"^[ \t]*@extract\s+file:\s*(\S+)", re.MULTILINE)
_ASSERT_DIRECTIVE = re.compile(r"^[ \t]*@assert\s+(.*)", re.MULTILINE)
_NOTE_BLOCK = re.compile(r"^[ \t]*@note\s*\n((?:[ \t]+.*\n?)*)", re.MULTILINE)
_HEADING = re.compile(r"^#\s+(.+)", re.MULTILINE)

# File directives that accept file: {{var}} patterns
_FILE_DIRECTIVES = [
    ("@embed", _EMBED_FILE),
    ("@summarize", _SUMMARIZE_FILE),
    ("@compress", _COMPRESS_FILE),
    ("@extract", _EXTRACT_FILE),
]

_RICH_FORMAT_HINT = "Supports: .txt, .md, .pdf, .docx, .pptx, .xlsx, .html"

# Variable names that suggest multiline content
_MULTILINE_HINTS = {
    "description", "text", "content", "body", "prompt", "instructions",
    "message", "context", "details", "summary", "draft", "template",
    "text_a", "text_b", "input_text", "output_text",
}

# Strategy-internal variables injected at runtime (not user inputs)
_INTERNAL_VARS = {
    "edited_content", "original_content",  # collaborative strategy
    "best_path", "state",                  # tree-of-thought strategy
}


# ═══════════════════════════════════════════════════════════════════
# Scanner
# ═══════════════════════════════════════════════════════════════════

def scan_spec(spec_text: str) -> SpecMetadata:
    """Scan a spec and extract structured metadata.

    This is a fast, regex-only pass — no LLM call.  It discovers all
    user-facing inputs and structural metadata needed to build a TUI
    form or perform pre-flight validation.
    """
    meta = SpecMetadata()

    # ── Title (first # heading) ──────────────────────────────────
    heading_match = _HEADING.search(spec_text)
    if heading_match:
        meta.title = heading_match.group(1).strip()

    # ── Description (text before first directive or heading) ─────
    meta.description = _extract_description(spec_text)

    # ── Notes ────────────────────────────────────────────────────
    note_blocks = _NOTE_BLOCK.findall(spec_text)
    meta.has_notes = len(note_blocks) > 0
    # Build a map of variable → nearby note text for help descriptions
    note_hints = _extract_note_hints(spec_text)

    # ── @execute ─────────────────────────────────────────────────
    exec_match = _EXECUTE_DIRECTIVE.search(spec_text)
    if exec_match:
        strategy = exec_match.group(1)
        config_block = exec_match.group(2).strip()
        config = {"type": strategy}
        for line in config_block.splitlines():
            line = line.strip()
            if ":" in line:
                k, _, v = line.partition(":")
                v = v.strip()
                # Try to parse numeric values
                try:
                    v = int(v)
                except (ValueError, TypeError):
                    try:
                        v = float(v)
                    except (ValueError, TypeError):
                        pass
                config[k.strip()] = v
        meta.execution = config

    # ── @prompt ──────────────────────────────────────────────────
    meta.prompt_names = list(dict.fromkeys(_PROMPT_DIRECTIVE.findall(spec_text)))

    # ── @tool ────────────────────────────────────────────────────
    meta.tool_names = list(dict.fromkeys(_TOOL_DIRECTIVE.findall(spec_text)))

    # ── @assert ──────────────────────────────────────────────────
    meta.assertions = _ASSERT_DIRECTIVE.findall(spec_text)

    # ── @refine (static file deps) ──────────────────────────────
    for path in _REFINE_DIRECTIVE.findall(spec_text):
        if not _is_variable(path):
            meta.refine_files.append(path)

    # ── Collect all inputs ───────────────────────────────────────
    seen_names: set[str] = set()
    inputs: List[SpecInput] = []

    # 1. @match variables → select dropdowns
    for m in _MATCH_DIRECTIVE.finditer(spec_text):
        var_name = m.group(1)
        if var_name in seen_names:
            continue
        seen_names.add(var_name)
        # Extract case values from the block following the @match
        cases = _extract_match_cases(spec_text, m.end())
        inputs.append(SpecInput(
            name=var_name,
            input_type="select",
            options=cases,
            description=note_hints.get(var_name),
            source_directive="@match",
        ))

    # 2. @if variables → boolean toggles
    for m in _IF_DIRECTIVE.finditer(spec_text):
        var_name = m.group(1)
        if var_name in seen_names:
            continue
        seen_names.add(var_name)
        inputs.append(SpecInput(
            name=var_name,
            input_type="boolean",
            default="false",
            description=note_hints.get(var_name),
            source_directive="@if",
        ))

    # 3. File directives with {{var}} → file pickers
    for directive_name, pattern in _FILE_DIRECTIVES:
        for m in pattern.finditer(spec_text):
            path = m.group(1)
            if _is_variable(path):
                var_name = _extract_var_name(path)
                if var_name and var_name not in seen_names:
                    seen_names.add(var_name)
                    inputs.append(SpecInput(
                        name=var_name,
                        input_type="file",
                        file_hint=_RICH_FORMAT_HINT,
                        description=note_hints.get(var_name),
                        source_directive=directive_name,
                    ))
            else:
                # Static file ref → informational
                meta.embed_files.append(path)

    # 4. @refine with {{var}} → file picker
    for m in _REFINE_DIRECTIVE.finditer(spec_text):
        path = m.group(1)
        if _is_variable(path):
            var_name = _extract_var_name(path)
            if var_name and var_name not in seen_names:
                seen_names.add(var_name)
                inputs.append(SpecInput(
                    name=var_name,
                    input_type="file",
                    file_hint="PromptSpec file (.promptspec.md)",
                    description=note_hints.get(var_name),
                    source_directive="@refine",
                ))

    # 5. Remaining {{variables}} → text / multiline inputs
    for m in _MUSTACHE_VAR.finditer(spec_text):
        var_name = m.group(1)
        if var_name in seen_names or var_name in _INTERNAL_VARS:
            continue
        seen_names.add(var_name)
        is_multiline = _is_multiline_hint(var_name)
        inputs.append(SpecInput(
            name=var_name,
            input_type="multiline" if is_multiline else "text",
            description=note_hints.get(var_name),
            source_directive="{{variable}}",
        ))

    meta.inputs = inputs
    return meta


# ═══════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════

def _extract_description(spec_text: str) -> str:
    """Extract free text before the first directive or second heading."""
    lines = spec_text.splitlines()
    desc_lines: list[str] = []
    past_title = False
    for line in lines:
        stripped = line.strip()
        # Skip the title heading
        if not past_title and stripped.startswith("# "):
            past_title = True
            continue
        # Stop at first directive or next heading
        if stripped.startswith("@") or (past_title and stripped.startswith("#")):
            break
        if past_title:
            desc_lines.append(line)
    return "\n".join(desc_lines).strip()


def _extract_match_cases(spec_text: str, start_pos: int) -> List[str]:
    """Extract case values from a @match block starting after the directive."""
    # Look at the text following the @match directive
    remaining = spec_text[start_pos:]
    cases: list[str] = []
    for m in _MATCH_CASE.finditer(remaining):
        cases.append(m.group(1))
        # Stop if we hit another top-level directive
    # Also check for _ wildcard (default case)
    if re.search(r"^[ \t]*_\s*==>", remaining, re.MULTILINE):
        cases.append("_")
    return cases


def _extract_note_hints(spec_text: str) -> dict[str, str]:
    """Map variable names to nearby @note descriptions.

    If a @note block appears within 5 lines before a {{variable}},
    use its text as the variable's description.
    """
    hints: dict[str, str] = {}
    lines = spec_text.splitlines()

    # Find all @note block ranges
    note_ranges: list[tuple[int, int, str]] = []
    i = 0
    while i < len(lines):
        if lines[i].strip().startswith("@note"):
            start = i
            content_lines: list[str] = []
            i += 1
            while i < len(lines) and (lines[i].startswith("  ") or lines[i].strip() == ""):
                if lines[i].strip():
                    content_lines.append(lines[i].strip())
                i += 1
            note_text = " ".join(content_lines)
            note_ranges.append((start, i, note_text))
        else:
            i += 1

    # For each variable, check if a @note ends within 5 lines before it
    for line_idx, line in enumerate(lines):
        for m in _MUSTACHE_VAR.finditer(line):
            var_name = m.group(1)
            if var_name in hints:
                continue
            for note_start, note_end, note_text in note_ranges:
                if 0 <= line_idx - note_end <= 5:
                    hints[var_name] = note_text[:200]  # cap length
                    break

    return hints


def _is_variable(path: str) -> bool:
    """Check if a file path is a {{variable}} reference."""
    return "{{" in path and "}}" in path


def _extract_var_name(path: str) -> Optional[str]:
    """Extract variable name from a {{var}} path."""
    m = _MUSTACHE_VAR.search(path)
    return m.group(1) if m else None


def _is_multiline_hint(var_name: str) -> bool:
    """Heuristic: does the variable name suggest multiline content?"""
    lower = var_name.lower()
    return any(hint in lower for hint in _MULTILINE_HINTS)
