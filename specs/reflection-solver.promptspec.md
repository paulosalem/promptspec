# Reflection Solver

@note
  Reflexion (Shinn et al., 2023) and self-refine (Madaan et al., 2023)
  use iterative critique-and-revise loops to improve LLM outputs. The
  model generates an initial answer, critiques it for errors, then
  revises to fix identified issues — repeating until the critique finds
  no problems or a maximum number of rounds is reached.

  This approach is particularly effective for multi-step reasoning where
  the model may make arithmetic or logical errors on the first attempt
  but can catch and correct them through self-reflection.

  References:
  - Shinn et al. (2023). "Reflexion: Language Agents with Verbal
    Reinforcement Learning." NeurIPS 2023. arXiv:2303.11366
  - Madaan et al. (2023). "Self-Refine: Iterative Refinement with
    Self-Feedback." NeurIPS 2023. arXiv:2303.17651

@execute reflection
  max_rounds: 2

You are a careful, methodical problem solver. Solve math problems
step by step, verify your work, and correct any errors you find.

Problem: {{problem}}

@prompt generate
  Solve this problem step by step. Show every calculation explicitly
  and arrive at a specific numerical answer. End with:

  ANSWER: [number]

@prompt critique
  Review this solution carefully:

  {{response}}

  Check each step:
  1. Are all arithmetic calculations correct? Re-do each one.
  2. Is the logic sound — does each step follow from the previous?
  3. Does the final answer match what the calculations produce?
  4. Were any parts of the problem overlooked or misread?

  If you find errors, describe exactly what is wrong and what the
  correct value should be. If the solution is correct, say
  "No issues found."

@prompt revise
  Here is a solution with identified issues:

  Original solution:
  {{response}}

  Issues found:
  {{critique}}

  Produce a corrected solution that fixes all identified issues.
  Show the complete step-by-step solution with correct calculations.
  End with:

  ANSWER: [number]
