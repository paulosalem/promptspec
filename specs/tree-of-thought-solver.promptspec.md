# Tree of Thought Solver

@note
  Tree of Thoughts (Yao et al., 2023) generalizes Chain-of-Thought by
  decomposing reasoning into incremental thought steps and exploring
  multiple paths via tree search. At each depth, the model generates
  candidate next-steps, evaluates each intermediate state as "sure",
  "maybe", or "impossible", and prunes dead ends before going deeper.

  This is the full BFS (beam search) implementation: at each depth level,
  branching_factor candidates are generated per state, evaluated, and
  the top beam_width states are kept for the next level. After max_depth
  levels, the best reasoning path is synthesized into a final answer.

  Also supports DFS (depth-first with backtracking) via search_type: dfs.

  Note: This strategy is significantly more expensive than the simplified
  variant (~90 LLM calls vs ~5). Use simplified-tree-of-thought for
  cost-sensitive applications.

  References:
  - Yao et al. (2023). "Tree of Thoughts: Deliberate Problem Solving
    with Large Language Models." NeurIPS 2023. arXiv:2305.10601

@execute tree-of-thought
  max_depth: 3
  branching_factor: 3
  beam_width: 3
  search_type: bfs

You are a rigorous problem solver. Break down the problem into
incremental reasoning steps, evaluate each intermediate state,
and find the most sound reasoning path.

Problem: {{problem}}

@prompt thought_step
  Current reasoning so far:

  {{state}}

  Provide the NEXT single reasoning step. Show one calculation or
  logical deduction that advances toward the solution. Be specific
  and show your work.

@prompt evaluate_step
  Evaluate this partial reasoning:

  {{state}}

  Consider:
  1. Are all calculations so far correct?
  2. Is this line of reasoning likely to reach the correct answer?
  3. Are there any contradictions or errors?

  Respond with exactly one word: "sure" (definitely correct so far),
  "maybe" (plausible but uncertain), or "impossible" (contains an error
  or contradiction that cannot lead to a correct answer).

@prompt synthesize
  Here is the best reasoning path found:

  {{best_path}}

  Based on this reasoning, state the final answer clearly. If the
  reasoning is incomplete, complete the remaining steps and provide
  the answer.

  End with:

  ANSWER: [number]
