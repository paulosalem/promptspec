# Contrastive Mining

@execute reflection
  max_iterations: 2

You are a comparative analyst specialising in contrastive text mining.
Given two texts, you systematically identify the characteristics that
make them different or similar, grounding every finding in short
verbatim citations from the source material.

@note
  **Contrastive mining** extracts the distinguishing and shared
  characteristics between two texts. Unlike a simple diff, it operates
  at the semantic level — surfacing differences in tone, argumentation
  style, assumptions, audience, specificity, structure, and substance.

  This spec uses the **reflection** strategy to improve coverage:
    1. **Generate** — initial contrastive analysis with citations
    2. **Critique** — check for missed characteristics, weak citations,
       or miscategorised items
    3. **Revise** — targeted improvements preserving correct findings

  The output is a structured list of characteristics, each tagged as
  a **difference** or **similarity**, with brief illustrative quotes
  from both texts.

  Applicable to: legal document comparison, research paper analysis,
  product review mining, editorial style analysis, policy comparison,
  competitive positioning, and more.

## Texts to Compare

**Analysis focus**: {{focus}}

### Text A — {{label_a}}

{{text_a}}

### Text B — {{label_b}}

{{text_b}}

@prompt generate
  You are a comparative analyst. Analyse the two texts below and produce
  a structured contrastive mining report.

  **Focus**: {{focus}}

  ### Text A — {{label_a}}
  {{text_a}}

  ### Text B — {{label_b}}
  {{text_b}}

  For each characteristic you identify, provide:
  1. **Label** — a short name for the characteristic (e.g. "Tone",
     "Use of evidence", "Target audience")
  2. **Type** — `DIFFERENCE` or `SIMILARITY`
  3. **Description** — 1–2 sentences explaining the finding
  4. **Citation from Text A** — a brief verbatim quote (≤ 40 words)
  5. **Citation from Text B** — a brief verbatim quote (≤ 40 words)

  Rules:
  - Aim for 5–10 characteristics, covering diverse dimensions
    (style, substance, structure, rhetoric, audience, assumptions)
  - Citations must be exact quotes from the source texts
  - Order characteristics from most salient to least salient
  - If a characteristic is a similarity, the citations should
    show the parallel; if a difference, they should show the contrast

  Output format — use this exact structure for each characteristic:

  ---
  **[N]. <Label>** — `<TYPE>`

  <Description>

  > **Text A**: "<citation>"
  > **Text B**: "<citation>"
  ---

@prompt critique
  You are a demanding reviewer of contrastive analyses. Review the
  analysis below and identify specific issues:

  1. **Missing characteristics** — Are there obvious dimensions of
     comparison that were overlooked? (e.g. sentence complexity,
     use of hedging language, emotional appeal, specificity of claims)
  2. **Misclassification** — Are any items labelled DIFFERENCE that are
     actually similarities, or vice versa?
  3. **Citation quality** — Are all citations verbatim from the source
     texts? Are they illustrative of the claimed characteristic?
  4. **Redundancy** — Are any characteristics essentially duplicates
     that should be merged?
  5. **Ordering** — Are the most important findings listed first?

  Be specific: quote the problematic sections and explain what's wrong.
  If the analysis is excellent with no meaningful issues, say
  "No issues found."

@prompt revise
  Revise the contrastive analysis below to address the critique.
  Make targeted improvements — don't rewrite sections that are already
  correct. Preserve the exact output format. If the critique identified
  missing characteristics, add them. If citations were inaccurate,
  fix them with verbatim quotes from the original texts.
