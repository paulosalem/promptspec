# Chain of Thought Baseline

@note
  Zero-shot Chain-of-Thought prompting. Rather than providing few-shot
  exemplars with reasoning traces (Wei et al., 2022), this spec uses
  explicit step-by-step instructions in the style of Kojima et al. (2022),
  who showed that simply eliciting intermediate reasoning steps from the
  model ("Let's think step by step") significantly improves accuracy on
  arithmetic, commonsense, and symbolic reasoning tasks.

  References:
  - Wei et al. (2022). "Chain-of-Thought Prompting Elicits Reasoning in
    Large Language Models." NeurIPS 2022. arXiv:2201.11903
  - Kojima et al. (2022). "Large Language Models are Zero-Shot Reasoners."
    NeurIPS 2022. arXiv:2205.11916

@execute single-call

Think step by step. Before answering, reason through the problem
carefully. Never jump to a conclusion without showing your work.

## Problem

{{problem}}

## Instructions

Work through the problem one logical step at a time:
- State what you are calculating and why at each step.
- Show the arithmetic or reasoning clearly.
- After completing all steps, state your final answer on its own line,
  prefixed with "ANSWER: ".
