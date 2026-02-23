@note
  This spec demonstrates a content-processing pipeline: @extract
  pulls key information, @summarize condenses it, and @compress
  forces extreme brevity. The @structural_constraints ensure
  consistent article format across a knowledge base.

@structural_constraints
  Every article must follow this structure:
  1. Title (H1)
  2. TL;DR (one paragraph, max 3 sentences)
  3. Overview (2–3 paragraphs of context)
  4. Key Concepts (H2 sections, one per concept)
  5. Practical Examples (at least 2)
  6. Common Pitfalls (bulleted list)
  7. Related Topics (links or references)
  8. Changelog (when this article was last updated)

Write a knowledge base article about **{{topic}}** for an internal
engineering team.

@extract "key_concepts"
  From the topic "{{topic}}", identify the 3–5 most important
  concepts that an engineer must understand. For each concept:
  - Define it precisely (no jargon without explanation)
  - Explain why it matters in practice
  - Provide a concrete code or architecture example

@if include_comparison
  ## Technology Comparison

  @summarize
    Compare {{topic}} against its main alternatives:
    {{#alternatives}}
    - **{{.}}**
    {{/alternatives}}

    For each alternative, evaluate:
    1. Performance characteristics (latency, throughput, resource usage)
    2. Developer experience (learning curve, tooling, documentation)
    3. Ecosystem maturity (community size, library support, enterprise adoption)
    4. When to choose it over {{topic}}

@if include_migration_guide
  ## Migration Guide

  @compress
    Provide a step-by-step migration guide for teams moving from
    {{migration_from}} to {{topic}}. Cover:
    - Pre-migration checklist and risk assessment
    - Data migration strategy
    - API compatibility and breaking changes
    - Rollback plan
    - Validation and smoke tests
    - Expected timeline for a team of 4–6 engineers

@output_format "markdown"
  Use GitHub-Flavored Markdown with:
  - Fenced code blocks with language identifiers
  - Tables for comparison data
  - Admonition blocks (> **Note:** ...) for important callouts
  - Anchor links in the Related Topics section
