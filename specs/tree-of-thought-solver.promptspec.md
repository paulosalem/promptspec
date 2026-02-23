# Tree of Thought Solver

@execution tree-of-thought
  branching_factor: 3
  max_depth: 2

You are a rigorous problem solver. Think carefully, explore multiple paths,
and synthesize the best solution.

## Problem

Solve the following: {{problem}}

@prompt generate
  Generate {{branching_factor}} distinct and creative approaches to solving
  the problem described above. For each approach:
  1. Give it a descriptive name
  2. Describe the strategy in 2-3 sentences
  3. List its key strengths and potential weaknesses

  Be diverse — explore fundamentally different angles, not variations of the
  same idea.

@prompt evaluate
  Given these candidate approaches:

  {{candidates}}

  Evaluate each approach on these criteria (1-10 scale):
  - **Feasibility**: How practical and implementable is this?
  - **Completeness**: Does it fully address the problem?
  - **Creativity**: Does it offer a novel or insightful perspective?
  - **Risk**: How likely is it to succeed? (10 = very likely)

  Provide a brief rationale for each score. Then declare which approach
  scores highest overall and why.

@prompt synthesize
  The winning approach was:

  {{best_approach}}

  Now elaborate this approach into a complete, detailed solution:
  1. Step-by-step implementation plan
  2. Key considerations and edge cases
  3. Expected outcomes and success metrics
  4. Potential challenges and mitigation strategies
