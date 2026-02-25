#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────
# PromptSpec — Interactive TUI Demo
#
# Launches the Textual-based TUI for a spec file, letting you fill
# in variables with a rich form, see a live preview, and
# compose/run the prompt — all from a gorgeous terminal UI.
#
# Usage:
#   ./demo-tui.sh                         # code-review spec + example vars
#   ./demo-tui.sh specs/chain-of-thought.promptspec.md
#   ./demo-tui.sh specs/contrastive-mining.promptspec.md --vars-file specs/vars/contrastive-mining-example.json
#
# Requires: pip install -e '.[ui]'   (installs textual)
# ──────────────────────────────────────────────────────────────────
set -euo pipefail

BOLD="\033[1m"
DIM="\033[2m"
GREEN="\033[32m"
CYAN="\033[36m"
YELLOW="\033[33m"
MAGENTA="\033[35m"
RESET="\033[0m"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# ── Pre-flight checks ───────────────────────────────────────────

if ! python -c "import textual" 2>/dev/null; then
  echo -e "${YELLOW}⚠  Textual not found. Install the [ui] extra:${RESET}"
  echo "   pip install -e '.[ui]'"
  exit 1
fi

if ! command -v promptspec &>/dev/null; then
  echo -e "${YELLOW}⚠  promptspec not found. Install with:${RESET}"
  echo "   pip install -e '.[all]'"
  exit 1
fi

# ── Defaults ─────────────────────────────────────────────────────

DEFAULT_SPEC="specs/code-review-checklist.promptspec.md"
DEFAULT_VARS=""

# ── Banner ───────────────────────────────────────────────────────

echo ""
echo -e "${BOLD}${MAGENTA}╔══════════════════════════════════════════════════════════════╗${RESET}"
echo -e "${BOLD}${MAGENTA}║         🖥️  PromptSpec TUI Demo                              ║${RESET}"
echo -e "${BOLD}${MAGENTA}║                                                              ║${RESET}"
echo -e "${BOLD}${MAGENTA}║  Fill in inputs → live preview → compose or run the prompt.  ║${RESET}"
echo -e "${BOLD}${MAGENTA}║  Ctrl+P = Compose  •  Ctrl+R = Run  •  Ctrl+C = Quit        ║${RESET}"
echo -e "${BOLD}${MAGENTA}╚══════════════════════════════════════════════════════════════╝${RESET}"
echo ""

# ── Parse args ───────────────────────────────────────────────────

SPEC="${1:-$DEFAULT_SPEC}"
shift 2>/dev/null || true

if [[ ! -f "$SPEC" ]]; then
  echo -e "${YELLOW}⚠  Spec file not found: ${CYAN}${SPEC}${RESET}"
  exit 1
fi

echo -e "${DIM}  Spec:  ${CYAN}${SPEC}${RESET}"

# Auto-detect vars file: specs/vars/<name>-example.json
SPEC_BASE="$(basename "$SPEC" .promptspec.md)"
AUTO_VARS="specs/vars/${SPEC_BASE}-example.json"
VARS_ARGS=""

if [[ "$*" == *"--vars-file"* ]]; then
  VARS_ARGS="$@"
elif [[ -f "$AUTO_VARS" ]]; then
  echo -e "${DIM}  Vars:  ${CYAN}${AUTO_VARS}${DIM} (auto-detected)${RESET}"
  VARS_ARGS="--vars-file $AUTO_VARS"
fi

echo ""

# ── Launch TUI ───────────────────────────────────────────────────

exec promptspec "$SPEC" --ui $VARS_ARGS "$@"
