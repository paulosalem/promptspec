# Tree of Thought Solver

@execute tree-of-thought
  branching_factor: 3
  max_depth: 2

You are a rigorous problem solver. Explore multiple reasoning paths,
evaluate which is most sound, and deliver the best answer.

## Problem

Solve the following: {{problem}}

@prompt generate
  Solve the problem above using {{branching_factor}} independent reasoning
  paths. For each path, work through the problem step by step from scratch,
  showing your calculations and logic clearly.

  Label each path (Path 1, Path 2, Path 3, etc.) and arrive at a concrete
  final answer at the end of each one. Take genuinely different angles —
  vary the order of operations, groupings, or intermediate steps so the
  paths are not trivial rewordings of each other.

@prompt evaluate
  Here are several candidate solutions to the same problem:

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
