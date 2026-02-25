#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────
# PromptSpec — Collaborative Editing Demo
#
# Draft an investment strategy with human-in-the-loop co-editing.
# The LLM generates a draft → you edit it → the LLM refines → repeat.
#
# Usage:
#   ./demo-collaborative.sh                  # interactive CLI mode
#   ./demo-collaborative.sh --editor         # opens $EDITOR each round
#   ./demo-collaborative.sh --non-interactive  # auto-approve (CI / dry-run)
#
# Requires: OPENAI_API_KEY set, promptspec installed (pip install -e '.[all,dev]')
# ──────────────────────────────────────────────────────────────────
set -euo pipefail

BOLD="\033[1m"
DIM="\033[2m"
GREEN="\033[32m"
YELLOW="\033[33m"
MAGENTA="\033[35m"
RESET="\033[0m"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

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
echo -e "${BOLD}${GREEN}║      🤝 Collaborative Editing Demo — Investment Strategy    ║${RESET}"
echo -e "${BOLD}${GREEN}║                                                              ║${RESET}"
echo -e "${BOLD}${GREEN}║  The LLM drafts → you edit → the LLM refines → repeat.      ║${RESET}"
echo -e "${BOLD}${GREEN}║  Up to 4 rounds of human-AI co-editing.                      ║${RESET}"
echo -e "${BOLD}${GREEN}╚══════════════════════════════════════════════════════════════╝${RESET}"
echo ""

echo -e "${DIM}  Scenario: A 35-year-old software engineer planning early retirement${RESET}"
echo -e "${DIM}  Goal:     $2M portfolio via low-cost index funds over 20 years${RESET}"
echo ""

# ── Run ──────────────────────────────────────────────────────────

python scripts/demo_collaborative.py "$@"
