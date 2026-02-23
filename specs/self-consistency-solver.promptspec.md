# Self-Consistency Math Solver

@execute self-consistency
  samples: 5
  aggregation: majority-vote

@refine chain-of-thought.promptspec.md

You are a precise mathematical problem solver. Solve the following problem
step by step, showing all work clearly.

## Problem

{{problem}}

@output_format enforce: strict
  Provide your answer in this format:
  1. **Working**: Show each step of your calculation
  2. **Answer**: State the final answer clearly on its own line, prefixed with "ANSWER: "
