#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────
# PromptSpec — Interactive Demo
#
# Showcases the power of LLM-driven prompt composition directives.
# Each demo runs a real composition and displays the result.
#
# Usage:
#   cd promptspec
#   ./demo.sh            # run all demos
#   ./demo.sh 3          # run only demo #3
#
# Requires: OPENAI_API_KEY set, promptspec installed
# ──────────────────────────────────────────────────────────────────
set -euo pipefail

BOLD="\033[1m"
DIM="\033[2m"
CYAN="\033[36m"
GREEN="\033[32m"
YELLOW="\033[33m"
MAGENTA="\033[35m"
RESET="\033[0m"
RULE="══════════════════════════════════════════════════════════════════════════════"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

demo_num=0
selected="${1:-all}"

# ── Helpers ──────────────────────────────────────────────────────

banner() {
  demo_num=$((demo_num + 1))
  echo ""
  echo -e "${MAGENTA}${RULE}${RESET}"
  echo -e "${BOLD}${MAGENTA}  DEMO ${demo_num}: $1${RESET}"
  echo -e "${MAGENTA}${RULE}${RESET}"
  echo ""
}

explain() {
  echo -e "${DIM}$1${RESET}"
  echo ""
}

show_cmd() {
  echo -e "  ${CYAN}\$ $1${RESET}"
  echo ""
}

pause() {
  if [[ "$selected" == "all" ]]; then
    echo ""
    echo -e "${DIM}  Press Enter to continue...${RESET}"
    read -r
  fi
}

should_run() {
  [[ "$selected" == "all" || "$selected" == "$demo_num" ]]
}

# ── Pre-flight checks ───────────────────────────────────────────

if [[ -z "${OPENAI_API_KEY:-}" ]]; then
  echo -e "${YELLOW}⚠  OPENAI_API_KEY not set. Export it first:${RESET}"
  echo "   export OPENAI_API_KEY=sk-..."
  exit 1
fi

if ! command -v promptspec &>/dev/null; then
  echo -e "${YELLOW}⚠  promptspec not found. Install with:${RESET}"
  echo "   pip install -e '.[all,dev]'"
  exit 1
fi

echo ""
echo -e "${BOLD}${GREEN}╔══════════════════════════════════════════════════════════════╗${RESET}"
echo -e "${BOLD}${GREEN}║          🎼  PromptSpec — Live Demo                    ║${RESET}"
echo -e "${BOLD}${GREEN}║                                                              ║${RESET}"
echo -e "${BOLD}${GREEN}║   An LLM-powered macro system for prompt engineering.        ║${RESET}"
echo -e "${BOLD}${GREEN}║   Watch directives compose, transform, and refactor prompts. ║${RESET}"
echo -e "${BOLD}${GREEN}╚══════════════════════════════════════════════════════════════╝${RESET}"
echo ""

# ═════════════════════════════════════════════════════════════════
# DEMO 1: The basics — @refine, @match, @if, variables
# ═════════════════════════════════════════════════════════════════

banner "The Basics — @refine, @match, @if, variables"

if should_run; then

explain "  A market research brief that:
    • @refine merges a base analyst persona from a separate file
    • @match selects a 'detailed' report structure (not 'executive')
    • @if conditionally includes a competitive landscape section
    • {{variables}} inject company name, industry, and time horizon"

CMD='promptspec specs/market-research-brief.promptspec.md \
  --vars-file specs/vars/market-research-example.json \
  --batch-only --verbose'

show_cmd "$CMD"
eval "$CMD"
pause

fi

# ═════════════════════════════════════════════════════════════════
# DEMO 2: @@ escaping — literal @ in output
# ═════════════════════════════════════════════════════════════════

banner "Escaping — Literal @ Symbols in Output"

if should_run; then

explain "  A tutorial generator where code examples contain Python decorators
  (@@property → @property) and email addresses (user@@example.com).
  The @@ escape prevents these from being interpreted as directives."

CMD='promptspec specs/tutorial-generator.promptspec.md \
  --vars-file specs/vars/tutorial-fastapi.json \
  --batch-only --verbose'

show_cmd "$CMD"
eval "$CMD"
pause

fi

# ═════════════════════════════════════════════════════════════════
# DEMO 3: Nested @summarize inside @match
# ═════════════════════════════════════════════════════════════════

banner "Nested Directives — @summarize Inside @match"

if should_run; then

explain "  A consulting proposal where the 'transformation' branch contains
  a @summarize that condenses a detailed roadmap. Inside-out evaluation:
  the LLM first summarizes the roadmap, then integrates the summary
  into the selected @match branch.

  Also uses: @refine, @audience, @style, @assert, @output_format"

CMD='promptspec specs/consulting-proposal.promptspec.md \
  --vars-file specs/vars/consulting-proposal-example.json \
  --batch-only --verbose'

show_cmd "$CMD"
eval "$CMD"
pause

fi

# ═════════════════════════════════════════════════════════════════
# DEMO 4: Content pipeline — @extract → @summarize → @compress
# ═════════════════════════════════════════════════════════════════

banner "Content Pipeline — @extract → @summarize → @compress"

if should_run; then

explain "  A knowledge base article that chains lossy operations:
    • @extract pulls key concepts from the topic description
    • @summarize condenses a technology comparison section
    • @compress squeezes a migration guide into minimal form
  Each operation UNDERSTANDS the content — not string manipulation.

  Also uses: @if, @structural_constraints, @output_format"

CMD='promptspec specs/knowledge-base-article.promptspec.md \
  --vars-file specs/vars/knowledge-base-article-example.json \
  --batch-only --verbose'

show_cmd "$CMD"
eval "$CMD"
pause

fi

# ═════════════════════════════════════════════════════════════════
# DEMO 5: Triple-nested @match with @compress inside a branch
# ═════════════════════════════════════════════════════════════════

banner "Deep Nesting — @match → @match → @if → @compress"

if should_run; then

explain "  An adaptive interview protocol with TRIPLE nesting:
    • Outer @match selects interview format (technical vs behavioral)
    • Inner @match selects seniority level (junior/senior/staff+)
    • @if gates system design questions within a seniority branch
    • @compress inside the junior branch condenses the rubric
    • @audience at the top reshapes the ENTIRE result for the reader
    • @generate_examples creates a filled scorecard
    • @assert validates no discriminatory questions

  This is impossible with any template engine — each layer is SEMANTIC."

CMD='promptspec specs/adaptive-interview.promptspec.md \
  --vars-file specs/vars/adaptive-interview-senior-backend.json \
  --batch-only --verbose'

show_cmd "$CMD"
eval "$CMD"
pause

fi

# ═════════════════════════════════════════════════════════════════
# DEMO 6: @expand and @contract — semantic grow/shrink
# ═════════════════════════════════════════════════════════════════

banner "AGM-Inspired — @expand, @contract, @revise"

if should_run; then

explain "  A multi-persona debate prompt built with belief-revision operators:
    • @expand adds 'Steel-Manning' and 'Hidden Assumptions' sections
      SEMANTICALLY — not appended, but integrated into the structure
    • @contract removes bias-introducing language at the MEANING level
      while preserving the analytical framework
    • @revise adds historical context while maintaining consistency
    • @match selects dialectical/decision/socratic synthesis style

  Named after Alchourrón-Gärdenfors-Makinson belief revision theory."

CMD='promptspec specs/multi-persona-debate.promptspec.md \
  --vars-file specs/vars/multi-persona-debate-agi.json \
  --batch-only --verbose'

show_cmd "$CMD"
eval "$CMD"
pause

fi

# ═════════════════════════════════════════════════════════════════
# DEMO 7: Prompt Refactoring — treating prompts as code
# ═════════════════════════════════════════════════════════════════

banner "Prompt Refactoring — Treating Prompts as Code"

if should_run; then

explain "  The most distinctive demo: takes a MESSY, contradictory prompt
  (inconsistent tone, duplicate rules, conflicting output formats)
  and runs it through a semantic refactoring pipeline:

    @extract  → pulls out hard requirements (like extracting an interface)
    @canon    → normalizes formatting (like a code formatter)
    @cohere   → resolves contradictions (like a linter with auto-fix)
    @revise   → adds a 'confidence' field to output format
    @expand   → adds multi-language support section
    @contract → replaces deprecated 'anything else?' requirement
    @structural_constraints → enforces section order
    @assert ×3 → validates the result (like a type checker)

  The input has: 'Be formal.' AND 'Be casual with emoji.' — both can't
  survive. Watch what happens."

CMD='promptspec specs/prompt-refactoring-pipeline.promptspec.md \
  --vars-file specs/vars/prompt-refactoring-example.json \
  --batch-only --verbose'

show_cmd "$CMD"
eval "$CMD"
pause

fi

# ═════════════════════════════════════════════════════════════════
# DEMO 8: JSON output — machine-readable for pipelines
# ═════════════════════════════════════════════════════════════════

banner "Machine-Readable Output — JSON for Pipelines"

if should_run; then

explain "  Same code review spec, but output as structured JSON.
  This enables composing promptspec into automated pipelines:
    promptspec ... --format json | jq '.composed_prompt' | llm ..."

CMD='promptspec specs/code-review-checklist.promptspec.md \
  --vars-file specs/vars/code-review-python.json \
  --format json --batch-only'

show_cmd "$CMD"
eval "$CMD"

fi

# ═════════════════════════════════════════════════════════════════

echo ""
echo -e "${GREEN}${RULE}${RESET}"
echo -e "${BOLD}${GREEN}  ✓ Demo complete!${RESET}"
echo ""
echo -e "${DIM}  Specs shown: $(ls specs/*.promptspec.md | wc -l | tr -d ' ') prompt specifications"
echo -e "  Directives used: @refine, @match, @if, @else, @revise, @expand,"
echo -e "    @contract, @summarize, @compress, @extract, @canon, @cohere,"
echo -e "    @audience, @style, @generate_examples, @output_format,"
echo -e "    @structural_constraints, @assert, @note, @@"
echo ""
echo -e "  Run a single demo:  ./demo.sh 3"
echo -e "  See all specs:      ls specs/"
echo -e "  Full docs:          cat README.md${RESET}"
echo ""
