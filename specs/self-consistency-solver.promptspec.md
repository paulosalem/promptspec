# Self-Consistency Math Solver

@note
  Self-Consistency (Wang et al., 2022) improves Chain-of-Thought
  prompting by sampling multiple diverse reasoning paths at high
  temperature and selecting the most consistent answer via majority
  vote. The key insight is that complex problems admit multiple valid
  reasoning approaches, and the correct answer is more likely to
  emerge across independent paths than from a single greedy decode.
  The original paper reports +17.9% on GSM8K over standard CoT.

  This spec uses @refine to inherit the CoT baseline prompt, then
  runs it 5 times independently with majority voting.

  References:
  - Wang et al. (2022). "Self-Consistency Improves Chain of Thought
    Reasoning in Language Models." ICLR 2023. arXiv:2203.11171

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
  2. **Answer**: State the final numerical answer clearly on its own line,
     prefixed with "ANSWER: " (number only, no units or explanation)
