#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────
# PromptSpec — Engine Demo
#
# Showcases execution strategies: multi-step LLM orchestration
# beyond a single call.  Each demo compiles a spec AND runs it
# through the corresponding engine (--run).
#
# Usage:
#   cd promptspec
#   ./demo-engines.sh             # run all engine demos
#   ./demo-engines.sh 2           # run only demo #2
#   ./demo-engines.sh --compile   # compile-only (no LLM execution)
#
# Requires: OPENAI_API_KEY set, promptspec installed (pip install -e .)
# ──────────────────────────────────────────────────────────────────
set -euo pipefail

BOLD="\033[1m"
DIM="\033[2m"
CYAN="\033[36m"
GREEN="\033[32m"
YELLOW="\033[33m"
MAGENTA="\033[35m"
RED="\033[31m"
RESET="\033[0m"
RULE="══════════════════════════════════════════════════════════════════════════════"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

demo_num=0
selected="${1:-all}"
compile_only=false

if [[ "${1:-}" == "--compile" ]]; then
  compile_only=true
  selected="all"
fi

# ── Helpers ──────────────────────────────────────────────────────

banner() {
  demo_num=$((demo_num + 1))
  echo ""
  echo -e "${MAGENTA}${RULE}${RESET}"
  echo -e "${BOLD}${MAGENTA}  ENGINE DEMO ${demo_num}: $1${RESET}"
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

run_or_compile() {
  local spec="$1"
  local vars="$2"
  local config="${3:-}"

  if $compile_only; then
    local cmd="promptspec ${spec} --vars-file ${vars} --batch-only --verbose"
    show_cmd "$cmd"
    eval "$cmd"
  else
    local cmd="promptspec ${spec} --vars-file ${vars} --run --verbose"
    if [[ -n "$config" ]]; then
      cmd="$cmd --config ${config}"
    fi
    show_cmd "$cmd"
    eval "$cmd"
  fi
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
echo -e "${BOLD}${GREEN}║      🚀  PromptSpec — Execution Engine Demos               ║${RESET}"
echo -e "${BOLD}${GREEN}║                                                              ║${RESET}"
echo -e "${BOLD}${GREEN}║  Multi-step LLM strategies: Tree of Thought,                ║${RESET}"
echo -e "${BOLD}${GREEN}║  Self-Consistency, and Reflection — all declarative.         ║${RESET}"
echo -e "${BOLD}${GREEN}╚══════════════════════════════════════════════════════════════╝${RESET}"
echo ""

if $compile_only; then
  echo -e "${YELLOW}📋 Compile-only mode: specs will be composed but NOT executed.${RESET}"
  echo -e "${DIM}   Remove --compile to run with LLM execution.${RESET}"
  echo ""
fi

# ═════════════════════════════════════════════════════════════════
# DEMO 1: Tree of Thought — strategic decision making
# ═════════════════════════════════════════════════════════════════

banner "Tree of Thought — Strategic Decision Making"

if should_run; then

explain "  A startup resource-allocation problem solved with Tree of Thought.
  The engine runs 3 stages automatically:

    1. GENERATE — produce 3 diverse candidate strategies
    2. EVALUATE — score each candidate on feasibility, completeness, etc.
    3. SYNTHESIZE — elaborate the winning strategy into a full plan

  Each stage uses a different temperature (0.9 → 0.1 → 0.3) to balance
  creativity in generation with precision in evaluation."

run_or_compile \
  "specs/tree-of-thought-solver.promptspec.md" \
  "specs/vars/tree-of-thought-solver-example.json" \
  "specs/tree-of-thought-solver.promptspec.yaml"

pause

fi

# ═════════════════════════════════════════════════════════════════
# DEMO 2: Self-Consistency — reliable problem solving
# ═════════════════════════════════════════════════════════════════

banner "Self-Consistency — Reliable Answers via Majority Vote"

if should_run; then

explain "  A classic river-crossing puzzle solved with Self-Consistency.
  The engine:

    1. Samples 5 INDEPENDENT solutions at high temperature (0.8)
    2. Collects all answers
    3. Takes a MAJORITY VOTE across the 5 attempts

  This dramatically reduces hallucination on problems with a single
  correct answer. Combined with @refine chain-of-thought.promptspec.md,
  each sample uses step-by-step reasoning."

run_or_compile \
  "specs/self-consistency-solver.promptspec.md" \
  "specs/vars/self-consistency-solver-example.json" \
  "specs/self-consistency-solver.promptspec.yaml"

pause

fi

# ═════════════════════════════════════════════════════════════════
# DEMO 3: Reflection — iterative self-improvement
# ═════════════════════════════════════════════════════════════════

banner "Reflection — Iterative Self-Improvement"

if should_run; then

explain "  A technical writing task improved through self-critique.
  The engine loops up to 3 iterations:

    1. GENERATE — write the initial draft
    2. CRITIQUE — a demanding editor finds specific issues
    3. REVISE  — targeted fixes (not a full rewrite)
    4. → back to CRITIQUE (until 'No issues found' or max iterations)

  Different temperatures per stage: creative drafting (0.7),
  strict critique (0.2), careful revision (0.4).
  The loop STOPS EARLY if the critique finds no issues."

run_or_compile \
  "specs/reflection-writer.promptspec.md" \
  "specs/vars/reflection-writer-example.json" \
  "specs/reflection-writer.promptspec.yaml"

pause

fi

# ═════════════════════════════════════════════════════════════════
# DEMO 4: Compile-then-pipe — engines with JSON output
# ═════════════════════════════════════════════════════════════════

banner "JSON Pipeline — Engine Output for Automation"

if should_run; then

explain "  Engine results as structured JSON — ready for downstream tools.
  This shows how to integrate promptspec --run into CI/CD pipelines,
  evaluation harnesses, or multi-agent orchestrations.

  Example pipeline:
    promptspec spec.md --run --config config.yaml --format json \\
      | jq '.output' | downstream-tool ..."

CMD='promptspec specs/self-consistency-solver.promptspec.md \
  --vars-file specs/vars/self-consistency-solver-example.json \
  --config specs/self-consistency-solver.promptspec.yaml \
  --run --format json --verbose'

if $compile_only; then
  CMD='promptspec specs/self-consistency-solver.promptspec.md \
    --vars-file specs/vars/self-consistency-solver-example.json \
    --format json --batch-only --verbose'
fi

show_cmd "$CMD"
eval "$CMD"

fi

# ═════════════════════════════════════════════════════════════════

echo ""
echo -e "${GREEN}${RULE}${RESET}"
echo -e "${BOLD}${GREEN}  ✓ Engine demos complete!${RESET}"
echo ""
echo -e "${DIM}  Engines demonstrated:"
echo -e "    🌳  tree-of-thought  — branching exploration + evaluation + synthesis"
echo -e "    🎯  self-consistency — parallel sampling + majority vote"
echo -e "    🔄  reflection       — generate → critique → revise loop"
echo ""
echo -e "  Run a single demo:  ./demo-engines.sh 2"
echo -e "  Compile only:       ./demo-engines.sh --compile"
echo -e "  Full composition:   ./demo.sh"
echo -e "  All specs:          ls specs/"
echo -e "  Engine docs:        cat README.md${RESET}"
echo ""
