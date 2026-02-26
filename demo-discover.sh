#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────
# PromptSpec — Discovery Mode Demo
#
# Launches the interactive spec discovery chat where you describe
# what you need and the AI helps you find the right spec.
#
# Usage:
#   ./demo-discover.sh                    # default (uses ./specs/)
#   ./demo-discover.sh --specs-dir ~/my-specs/  # add extra dir
#
# Requires: pip install -e '.[ui]'
# ──────────────────────────────────────────────────────────────────
set -euo pipefail

BOLD="\033[1m"
DIM="\033[2m"
CYAN="\033[36m"
MAGENTA="\033[35m"
RESET="\033[0m"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

if ! command -v promptspec &>/dev/null; then
  echo -e "${MAGENTA}✗ 'promptspec' CLI not found. Install with:${RESET}"
  echo -e "  ${DIM}pip install -e '.[ui]'${RESET}"
  exit 1
fi

echo ""
echo -e "${BOLD}${MAGENTA}╔══════════════════════════════════════════════════════════════╗${RESET}"
echo -e "${BOLD}${MAGENTA}║        ⚡ PromptSpec Discovery                               ║${RESET}"
echo -e "${BOLD}${MAGENTA}║                                                              ║${RESET}"
echo -e "${BOLD}${MAGENTA}║  Describe what you need and the AI will find the right spec  ║${RESET}"
echo -e "${BOLD}${MAGENTA}║  for you, then launch it in the interactive TUI.             ║${RESET}"
echo -e "${BOLD}${MAGENTA}╚══════════════════════════════════════════════════════════════╝${RESET}"
echo ""
echo -e "${DIM}  Environment:${RESET}"
promptspec --env 2>&1 | sed 's/^/  /'
echo ""

exec promptspec --discover "$@"
