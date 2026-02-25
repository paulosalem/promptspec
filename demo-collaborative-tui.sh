#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────
# PromptSpec — Collaborative Editing TUI Demo
#
# Launches the golden TUI for a collaborative spec. The LLM drafts
# text, then a rich TextArea modal pops up for you to review, edit,
# approve, or abort — all inside the terminal.
#
# Usage:
#   ./demo-collaborative-tui.sh                                 # investment strategy (default)
#   ./demo-collaborative-tui.sh specs/collaborative-writer.promptspec.md
#
# Requires:
#   pip install -e '.[ui]'          (installs textual)
#   export OPENAI_API_KEY=sk-...    (or another LLM provider key)
# ──────────────────────────────────────────────────────────────────
set -euo pipefail

BOLD="\033[1m"
DIM="\033[2m"
GOLD="\033[33m"
CYAN="\033[36m"
YELLOW="\033[33m"
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

if [[ -z "${OPENAI_API_KEY:-}" ]]; then
  echo -e "${YELLOW}⚠  OPENAI_API_KEY not set. Export it first:${RESET}"
  echo "   export OPENAI_API_KEY=sk-..."
  exit 1
fi

# ── Defaults ─────────────────────────────────────────────────────

DEFAULT_SPEC="specs/collaborative-investment-strategy.promptspec.md"

# ── Banner ───────────────────────────────────────────────────────

echo ""
echo -e "${BOLD}${GOLD}╔══════════════════════════════════════════════════════════════╗${RESET}"
echo -e "${BOLD}${GOLD}║      🤝 Collaborative Editing — TUI Demo                     ║${RESET}"
echo -e "${BOLD}${GOLD}║                                                              ║${RESET}"
echo -e "${BOLD}${GOLD}║  Fill inputs → Run → LLM drafts → Edit in TextArea → Repeat  ║${RESET}"
echo -e "${BOLD}${GOLD}║                                                              ║${RESET}"
echo -e "${BOLD}${GOLD}║  In the edit modal:                                          ║${RESET}"
echo -e "${BOLD}${GOLD}║    ✓ Approve  — accept text as-is                            ║${RESET}"
echo -e "${BOLD}${GOLD}║    ✏ Submit   — send your edits back to the LLM              ║${RESET}"
echo -e "${BOLD}${GOLD}║    🏁 Done    — signal you're finished collaborating          ║${RESET}"
echo -e "${BOLD}${GOLD}║    ✗ Abort    — cancel the collaboration                     ║${RESET}"
echo -e "${BOLD}${GOLD}╚══════════════════════════════════════════════════════════════╝${RESET}"
echo ""

# ── Parse args ───────────────────────────────────────────────────

SPEC="${1:-$DEFAULT_SPEC}"
shift 2>/dev/null || true

if [[ ! -f "$SPEC" ]]; then
  echo -e "${YELLOW}⚠  Spec file not found: ${CYAN}${SPEC}${RESET}"
  exit 1
fi

echo -e "${DIM}  Spec:  ${CYAN}${SPEC}${RESET}"

# Auto-detect vars file
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
echo -e "${DIM}  Ctrl+P = Compose  •  Ctrl+R = Run  •  Ctrl+C = Quit${RESET}"
echo ""

# ── Launch TUI ───────────────────────────────────────────────────

exec promptspec "$SPEC" --ui $VARS_ARGS "$@"
