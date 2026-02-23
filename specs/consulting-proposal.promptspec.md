@refine base-analyst.promptspec.md

@audience "{{audience_type}}"
  Tailor the language, depth, and examples in this proposal to the
  specified audience.

@style "authoritative, structured, data-driven"

@note
  This consulting proposal spec demonstrates a realistic pipeline:
  @refine pulls in the analyst persona, @audience and @style shape
  the tone, @output_format constrains the deliverable, @match
  selects the engagement scope, and @assert validates quality.

You are preparing a management consulting proposal for **{{client_name}}**,
a {{client_industry}} company seeking to **{{engagement_goal}}**.

## Engagement Context

{{client_name}} is facing the following challenges:
{{#challenges}}
- {{.}}
{{/challenges}}

The engagement timeline is **{{timeline}}** and the expected budget
range is **{{budget_range}}**.

@match engagement_scope
  "diagnostic" ==>
    ### Deliverable: Diagnostic Assessment

    Produce a 2-week diagnostic that:
    1. Maps current-state processes across {{focus_areas}}
    2. Identifies the top 5 pain points by impact severity
    3. Estimates the cost of inaction for each (annualized $)
    4. Recommends whether a full transformation engagement is warranted

    Format: Executive slide deck (10–15 slides) + data appendix.

  "transformation" ==>
    ### Deliverable: Transformation Roadmap

    @summarize
      Design a phased transformation roadmap covering:
      - Phase 1 (Quick Wins, 0–3 months): Low-effort, high-impact changes
        that build momentum and stakeholder confidence.
      - Phase 2 (Foundation, 3–9 months): Infrastructure, process redesign,
        and capability building required for sustainable change.
      - Phase 3 (Scale, 9–18 months): Full rollout, change management, and
        performance measurement against KPIs.

      For each phase, specify:
      - Workstreams and ownership
      - Dependencies and critical path
      - Investment required vs. expected ROI
      - Risk factors and mitigation strategies

    @assert "The proposal must include quantified ROI estimates for each phase."
    @assert "Risk mitigation strategies must be specific and actionable."

  "strategy" ==>
    ### Deliverable: Strategic Options Paper

    Present 3 mutually exclusive strategic options for achieving
    **{{engagement_goal}}**. For each option:

    1. **Thesis**: One-sentence strategic hypothesis
    2. **Evidence**: Supporting data points and market signals
    3. **Financial model**: Revenue impact, cost structure, payback period
    4. **Risks**: Probability-weighted risk assessment
    5. **Recommendation**: Go / No-Go with conditions

    Conclude with a clear recommendation of the preferred option,
    supported by a decision matrix scoring each on feasibility,
    impact, speed, and risk.

@output_format "markdown"
  Use professional consulting report formatting with clear section
  numbering, executive summary up front, and appendices for
  supporting data.

Focus on delivering actionable, evidence-based recommendations that
{{client_name}} can begin executing within **{{timeline}}**.
