@note
  This spec demonstrates the most distinctive capability of our system:
  treating prompts AS CODE that can be refactored. No template engine
  can do what happens here — we take a messy, organically-grown prompt,
  and apply a pipeline of semantic transformations that UNDERSTAND the
  meaning of the text:

  1. @extract pulls out the hard requirements (like extracting an interface)
  2. @canon normalizes inconsistent formatting (like a code formatter)
  3. @cohere resolves cross-references and contradictions (like a linter)
  4. @revise adds a new requirement while maintaining consistency
  5. @expand adds missing sections without breaking existing ones
  6. @contract removes deprecated parts surgically
  7. @assert validates the result (like a type checker)

  This is "prompt refactoring" — the same discipline as code refactoring,
  but applied to natural-language constraint sets.

@note
  The messy prompt below simulates what happens after months of ad-hoc
  edits by multiple team members. It has inconsistent formatting,
  contradictory instructions, redundant sections, and missing pieces.
  The directive pipeline below it refactors it into a clean, consistent,
  correct prompt — automatically.

{{raw_prompt}}

@extract format: bullets
  All hard requirements (MUST, SHOULD, ALWAYS, NEVER) and all
  output format constraints. Preserve the exact obligation level
  (MUST vs SHOULD).

@canon headings: normalize lists: normalize terminology: normalize

@cohere aggressiveness: medium

@revise mode: editorial
  {{revision_instruction}}

@if add_section
  @expand mode: editorial placement: integrate
    {{new_section_content}}

@if remove_section
  @contract mode: editorial
    {{contraction_instruction}}

@structural_constraints strict: true
  Required sections in order:
  1. Role and Identity
  2. Core Requirements
  3. Constraints and Prohibitions
  4. Output Format
  5. Examples (if any)
  6. Edge Cases

@assert severity: error The prompt contains no contradictory instructions.
@assert severity: warning The prompt specifies what to do when input is ambiguous.
@assert severity: warning Every MUST requirement has a clear success criterion.

@output_format enforce: strict
  The refactored prompt must be ready to use as-is with an LLM.
  No meta-commentary, no "here's what I changed" notes — just
  the clean, final prompt.
