#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────
#  demo-benchmark.sh — Benchmark PromptSpec strategies on GSM8K
# ──────────────────────────────────────────────────────────────────────────
#
#  Compares three prompting strategies composed with PromptSpec against
#  the GSM8K math benchmark:
#
#    • Chain-of-Thought (single-call baseline)
#    • Self-Consistency (5 samples + majority vote)
#    • Tree of Thought  (generate → evaluate → synthesize)
#
#  Usage:
#    ./demo-benchmark.sh              # Quick demo (10 samples)
#    ./demo-benchmark.sh --limit 50   # Run with 50 samples
#    ./demo-benchmark.sh --full       # Full GSM8K benchmark (~1300 samples)
#    ./demo-benchmark.sh --model openai/gpt-4o  # Use a different model
#
#  Requirements:
#    • OPENAI_API_KEY set in environment
#    • pip install ellements[benchmarking]
#    • pip install -e .   (promptspec installed in editable mode)
#
# ──────────────────────────────────────────────────────────────────────────

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# ── Defaults ──────────────────────────────────────────────────────────────

LIMIT=10
MODEL="openai/gpt-4o-mini"
TASKS="gsm8k"

# ── Parse arguments ──────────────────────────────────────────────────────

while [[ $# -gt 0 ]]; do
  case "$1" in
    --limit|-l)   LIMIT="$2"; shift 2 ;;
    --full)       LIMIT=""; shift ;;
    --model|-m)   MODEL="$2"; shift 2 ;;
    --tasks|-t)   TASKS="$2"; shift 2 ;;
    --help|-h)
      echo "Usage: $0 [--limit N] [--full] [--model MODEL] [--tasks TASK]"
      echo ""
      echo "Options:"
      echo "  --limit N, -l N   Limit to N samples per task (default: 10)"
      echo "  --full            Run full benchmark (no limit)"
      echo "  --model M, -m M   Model to use (default: openai/gpt-4o-mini)"
      echo "  --tasks T, -t T   Benchmark task (default: gsm8k)"
      echo ""
      echo "Example:"
      echo "  $0 --limit 20 --model openai/gpt-4o"
      exit 0
      ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

# ── Preflight checks ────────────────────────────────────────────────────

if [[ -z "${OPENAI_API_KEY:-}" ]]; then
  echo "❌ OPENAI_API_KEY not set. Export it before running:"
  echo "   export OPENAI_API_KEY=sk-..."
  exit 1
fi

if ! python -c "import lm_eval" 2>/dev/null; then
  echo "❌ lm-evaluation-harness not installed. Run:"
  echo "   pip install ellements[benchmarking]"
  exit 1
fi

# ── Build limit flag ─────────────────────────────────────────────────────

LIMIT_FLAG=""
if [[ -n "$LIMIT" ]]; then
  LIMIT_FLAG="--limit $LIMIT"
fi

# ── Banner ───────────────────────────────────────────────────────────────

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  ⚡ PromptSpec Strategy Benchmark Demo                      ║"
echo "║                                                              ║"
echo "║  Comparing prompting strategies on: $TASKS"
echo "║  Model: $MODEL"
if [[ -n "$LIMIT" ]]; then
echo "║  Samples: $LIMIT (use --full for complete benchmark)"
else
echo "║  Samples: FULL benchmark"
fi
echo "║                                                              ║"
echo "║  Strategies:                                                 ║"
echo "║    📝 Chain-of-Thought (single-call baseline)                ║"
echo "║    🎲 Self-Consistency (5 samples + majority vote)           ║"
echo "║    🌳 Tree of Thought  (generate → evaluate → synthesize)   ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# ── Run benchmark ────────────────────────────────────────────────────────

python scripts/benchmark_strategies.py \
  --specs \
    specs/cot-baseline.promptspec.md \
    specs/self-consistency-solver.promptspec.md \
    specs/tree-of-thought-solver.promptspec.md \
  --tasks "$TASKS" \
  --model "$MODEL" \
  $LIMIT_FLAG \
  --output benchmark-results.json

echo ""
echo "📊 Results saved to benchmark-results.json"
echo ""
