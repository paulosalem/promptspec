Write a technical tutorial about **{{topic}}**.

@match audience
  "beginner" ==>
    **Target audience: beginners with no prior experience.**

    - Explain every concept from first principles before using it.
    - Use real-world analogies to build intuition (e.g., "a REST API is like a restaurant menu — you pick items, the kitchen prepares them").
    - Show every step explicitly — do not skip "obvious" steps.
    - Provide the exact commands to install dependencies and set up the environment.

  "intermediate" ==>
    **Target audience: developers with working knowledge of the fundamentals.**

    - Skip basic setup unless it differs from the standard approach.
    - Focus on practical patterns, trade-offs, and "why" behind design decisions.
    - Compare alternative approaches (e.g., "You could use X here, but Y is better because…").
    - Include at least one production-ready code example.

  "advanced" ==>
    **Target audience: experienced developers seeking deep expertise.**

    - Focus on edge cases, performance characteristics, and architectural patterns.
    - Discuss internals and implementation details where relevant.
    - Include benchmarks or complexity analysis where applicable.
    - Address common misconceptions held even by experienced practitioners.

@note
  The @@ escaping below is critical. Tutorial content about Python
  decorators and Java annotations must render literal @ symbols in the
  final output, not trigger prompt composition directives.

## Code Examples

When writing code examples, follow these conventions:

- Python decorators use the standard syntax: @@property, @@staticmethod, @@classmethod, @@dataclass
- Java/Kotlin annotations use: @@Override, @@Inject, @@Autowired, @@RestController
- Email addresses in examples should use: user@@example.com

Every code block must:
1. Be complete and runnable (no "..." or "# rest of code here")
2. Include necessary imports
3. Show expected output in a comment or separate output block

@if include_exercises
  ## Practice Exercises

  Include 3 progressively harder exercises at the end of the tutorial:

  **Exercise 1 (Warm-up):** A straightforward application of the core concept.
  Estimated time: 10 minutes.

  **Exercise 2 (Applied):** Combines multiple concepts from the tutorial.
  Requires the reader to make design decisions.
  Estimated time: 20 minutes.

  **Exercise 3 (Challenge):** An open-ended problem that extends beyond the
  tutorial content. Encourages the reader to research and experiment.
  Estimated time: 30–45 minutes.

  For each exercise, provide:
  - A clear problem statement
  - Expected input/output examples
  - Hints (collapsed/hidden if the output format supports it)
  - A reference solution

Output the tutorial in **{{output_format}}** format.
