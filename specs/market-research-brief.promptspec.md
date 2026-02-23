@refine base-analyst.promptspec.md

@note
  This spec builds a market research brief on top of the base analyst
  persona. The @refine merges analytical rigor with domain-specific
  research structure. Variables control scope and depth.

Conduct a comprehensive market research analysis for **{{company}}**
operating in the **{{industry}}** industry.

Your analysis must cover:
- Current market size and projected growth (CAGR where available)
- Key demand drivers and headwinds
- Regulatory environment and upcoming policy changes
- Target customer segments and unmet needs

@match report_depth
  "executive" ==>
    Deliver a concise executive summary (no more than 500 words).
    Lead with the single most important finding, followed by 3–5
    bullet-point recommendations. Attach a one-paragraph risk
    assessment at the end.
  "detailed" ==>
    Deliver a multi-section report with the following structure:

    ### Market Overview
    Size, growth trajectory (5-year historical + forecast), and
    key inflection points.

    ### Customer Segmentation
    Identify at least 3 distinct customer segments. For each,
    describe demographics, buying behavior, and willingness to pay.

    ### Regulatory Landscape
    Current regulations, pending legislation, and compliance
    requirements that affect market entry or expansion.

    ### SWOT Analysis
    Strengths, weaknesses, opportunities, and threats — each
    supported by at least one data point or citation.

    ### Strategic Recommendations
    Prioritized list of 3–5 actions with expected impact and
    implementation difficulty (high / medium / low).

@if include_competitors
  ## Competitive Landscape

  Identify the top 5 direct competitors to {{company}} in the
  {{industry}} market. For each competitor, analyze:

  1. Market share (estimate if exact data unavailable)
  2. Core value proposition and differentiation
  3. Recent strategic moves (M&A, product launches, partnerships)
  4. Key vulnerabilities that {{company}} could exploit

  Conclude with a positioning map plotting competitors on two axes:
  **price** (low → premium) and **innovation** (incremental → disruptive).

Focus your analysis on the next **{{time_horizon}}**.
