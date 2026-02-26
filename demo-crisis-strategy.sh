#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────
# PromptSpec — Crisis Strategy Analyzer Demo
#
# Showcases the crisis-strategy-analyzer spec, which identifies
# realistic strategic options for a problem/threat, estimates each
# strategy's probability of success, and recommends a course of
# action — informed by Liddell Hart's indirect approach principles.
#
# Usage:
#   ./demo-crisis-strategy.sh                          # Google AI threat (default)
#   ./demo-crisis-strategy.sh earthquake               # Earthquake scenario
#   ./demo-crisis-strategy.sh --ui                     # Interactive TUI mode
#   ./demo-crisis-strategy.sh earthquake --ui          # TUI with earthquake scenario
#
# Requires: pip install -e '.[ui]'   (for --ui mode)
# ──────────────────────────────────────────────────────────────────
set -euo pipefail

BOLD="\033[1m"
DIM="\033[2m"
GREEN="\033[32m"
CYAN="\033[36m"
YELLOW="\033[33m"
MAGENTA="\033[35m"
RED="\033[31m"
RESET="\033[0m"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

SPEC="specs/crisis-strategy-analyzer.promptspec.md"

# ── Pre-flight checks ───────────────────────────────────────────

if ! command -v promptspec &>/dev/null; then
  echo -e "${RED}✗ 'promptspec' CLI not found. Install with:${RESET}"
  echo -e "  ${DIM}pip install -e '.[ui]'${RESET}"
  exit 1
fi

if [[ ! -f "$SPEC" ]]; then
  echo -e "${RED}✗ Spec not found: ${SPEC}${RESET}"
  exit 1
fi

# ── Parse arguments ──────────────────────────────────────────────

SCENARIO="google"
UI_FLAG=""
EXTRA_ARGS=""

for arg in "$@"; do
  case "$arg" in
    earthquake)  SCENARIO="earthquake" ;;
    google)      SCENARIO="google" ;;
    --ui)        UI_FLAG="--ui" ;;
    *)           EXTRA_ARGS="$EXTRA_ARGS $arg" ;;
  esac
done

# Map scenario to vars file
case "$SCENARIO" in
  google)
    VARS_FILE="specs/vars/crisis-strategy-google-ai-threat.json"
    SCENARIO_LABEL="Google threatened by AI startups"
    ;;
  earthquake)
    VARS_FILE="specs/vars/crisis-strategy-earthquake.json"
    SCENARIO_LABEL="Major earthquake disrupts manufacturing"
    ;;
esac

if [[ ! -f "$VARS_FILE" ]]; then
  echo -e "${RED}✗ Vars file not found: ${VARS_FILE}${RESET}"
  exit 1
fi

# ── Banner ───────────────────────────────────────────────────────

echo ""
echo -e "${BOLD}${MAGENTA}╔══════════════════════════════════════════════════════════════╗${RESET}"
echo -e "${BOLD}${MAGENTA}║        ⚔️   Crisis Strategy Analyzer                         ║${RESET}"
echo -e "${BOLD}${MAGENTA}║                                                              ║${RESET}"
echo -e "${BOLD}${MAGENTA}║  Identifies strategic options, estimates success probability, ║${RESET}"
echo -e "${BOLD}${MAGENTA}║  and recommends a course of action using Liddell Hart's       ║${RESET}"
echo -e "${BOLD}${MAGENTA}║  indirect approach principles.                                ║${RESET}"
echo -e "${BOLD}${MAGENTA}╚══════════════════════════════════════════════════════════════╝${RESET}"
echo ""
echo -e "  ${DIM}Spec:      ${CYAN}${SPEC}${RESET}"
echo -e "  ${DIM}Scenario:  ${GREEN}${SCENARIO_LABEL}${RESET}"
echo -e "  ${DIM}Vars:      ${CYAN}${VARS_FILE}${RESET}"
echo -e "  ${DIM}Mode:      ${YELLOW}${UI_FLAG:-CLI}${RESET}"
echo ""

# ── Launch ───────────────────────────────────────────────────────

if [[ -n "$UI_FLAG" ]]; then
  echo -e "${DIM}Launching TUI… (Ctrl+R to run, Ctrl+C to quit)${RESET}"
  echo ""
  exec promptspec "$SPEC" --ui --vars-file "$VARS_FILE" $EXTRA_ARGS
else
  echo -e "${DIM}Running analysis…${RESET}"
  echo ""
  exec promptspec "$SPEC" --vars-file "$VARS_FILE" $EXTRA_ARGS
fi
