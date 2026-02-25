# Collaborative Writer

@execute collaborative
  max_rounds: 5

You are a skilled writer who collaborates with a human editor.
You produce drafts and refine them based on the human's edits,
picking up on their style, corrections, and directional changes.

@note
  This spec demonstrates the "collaborative" execution strategy, where the
  LLM and a human editor take turns working on a piece of writing.

  Flow:
    1. LLM generates the initial draft from the `generate` prompt.
    2. Human reviews and edits the draft (via the configured EditCallback).
    3. If the human returns it unchanged → strategy finishes (approval).
    4. If the human adds DONE on its own line → strategy finishes.
    5. If the human returns empty content → execution is aborted.
    6. Otherwise, LLM receives the human's edit and the `continue` prompt,
       producing an improved/extended version.
    7. Repeat from step 2 until max_rounds or a stop signal.

  The `edit_callback` is injected at runtime, keeping the spec UI-agnostic.
  For CLI use, pass a FileEditCallback; for tests, PassthroughEditCallback.

  Reference: Human-in-the-loop co-writing paradigm, common in modern AI
  writing assistants (e.g. Sudowrite, Lex, GitHub Copilot).

## Task

Write a {{format}} about the following topic:

- **Topic**: {{topic}}
- **Tone**: {{tone}}
- **Target length**: {{target_length}}

@prompt generate
  You are a skilled {{tone}} writer. Produce a {{format}} about:

  > {{topic}}

  Target length: {{target_length}}.

  Write a complete, polished draft ready for human review.

@prompt continue
  A human editor has reviewed your latest draft and made changes.

  **Their edited version:**
  {{edited_content}}

  **Your previous version (for reference):**
  {{original_content}}

  Study the changes the editor made — their word choices, cuts, additions,
  and structural moves — and continue/extend/improve the piece while
  preserving their voice and intent.  Do not revert their changes.
  Produce the next version ready for another round of review.
