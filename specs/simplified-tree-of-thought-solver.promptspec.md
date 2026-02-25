# Simplified Tree of Thought Solver

@note
  Simplified variant of Tree of Thoughts (Yao et al., 2023). Generates N
  complete independent solutions in parallel, evaluates them together,
  and synthesizes the best answer. This is a "generate → evaluate →
  synthesize" pattern — simpler and cheaper than the full BFS/DFS tree
  search, but captures the core benefit of diverse parallel exploration
  with self-evaluation.

  For the full algorithm with step-level BFS/DFS search, see
  tree-of-thought-solver.promptspec.md.

  References:
  - Yao et al. (2023). "Tree of Thoughts: Deliberate Problem Solving
    with Large Language Models." NeurIPS 2023. arXiv:2305.10601

@execute simplified-tree-of-thought
  branching_factor: 3

You are a rigorous problem solver. Explore multiple reasoning paths,
evaluate which is most sound, and deliver the best answer.

Problem: {{problem}}

@prompt generate
  Solve this problem step by step, showing your calculations and logic
  clearly. Work through each step carefully and arrive at a concrete
  final answer.

@prompt evaluate
  Here are several candidate solutions:

  {{candidates}}

  For each path, verify the reasoning step by step:
  1. Are the calculations correct at every step?
  2. Are all constraints and conditions of the problem respected?
  3. Does the final answer logically follow from the steps?

  After checking each path, state which path (or paths) reached the
  correct answer and briefly explain any errors found in the others.
  If multiple paths agree on the same answer, note that as additional
  evidence of correctness.

@prompt synthesize
  Based on this analysis:

  {{best_approach}}

  Produce the final, verified answer. State the answer clearly and
  concisely, then provide a clean step-by-step solution that a reader
  can follow.
