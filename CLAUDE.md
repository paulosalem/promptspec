# CLAUDE.md — PromptSpec

## Project Overview

PromptSpec is a prompt specification language for composing, executing, and benchmarking LLM prompting strategies. Core at `src/promptspec/`. Depends on sibling `ellements` repo for LLM client and execution strategies.

## Critical Engineering Lessons

### Event Loop & Connection Exhaustion (MUST READ)

**Problem**: The benchmark runner originally created a new `asyncio` event loop per sample. After ~12-15 samples, accumulated aiohttp sessions (in TIME_WAIT TCP state) from destroyed loops exhausted sockets/FDs, causing cascading "Connection error" failures that looked like API issues but were actually local resource exhaustion.

**Root cause chain**:
1. Each sample → new event loop → new aiohttp sessions for litellm
2. Loop destroyed, but TCP connections linger in TIME_WAIT (~60s)
3. After ~12 samples × 5 calls/sample = ~60 connections, socket limit hit
4. All subsequent connections fail → retry loops make it worse (more connections)

**Solution**: Single event loop for all strategy samples. `asyncio.Semaphore` for concurrency control. See `_run_all_strategy()` in `scripts/benchmark_strategies.py`.

### LiteLLM LoggingWorker Across Event Loops

LiteLLM's async LoggingWorker creates an `asyncio.Queue` bound to the first event loop. Composition phase uses `asyncio.run()` which creates and destroys a loop. The benchmark phase then creates new loops, causing "Queue is bound to a different event loop" errors.

**Fix**: Monkey-patch the worker between phases:
```python
import litellm.litellm_core_utils.logging_worker as _lw
_lw.LoggingWorker.start = lambda self: None
```

### Strategy Retry Architecture

The ellements `BaseStrategy._call_llm()` retries individual failed LLM calls. This is crucial because:
- ToT has 5 LLM calls (3 generate + evaluate + synthesize)
- Without per-call retry: 1 failed call → entire pipeline fails → benchmark retries ALL 5 calls
- With per-call retry: 1 failed call → retried 3x with backoff → pipeline continues

The benchmark runner has its OWN retry loop (5 attempts) as a safety net, but the engine-level retry handles ~95% of transient failures.

## Key Files

- `src/promptspec/controller.py` — Composition engine
  - `_extract_root_text()` — Extracts prefix/suffix for cascading
  - `_cascade_root_context()` — Injects root text into sub-prompts
  - `compose()` — Main composition entry point
- `scripts/benchmark_strategies.py` — Benchmark runner
  - `_run_all_strategy()` — Single-loop strategy execution
  - `_process_one_async()` — Per-sample async processor with retry
  - `create_benchmark_model()` — lm-eval adapter factory
- `specs/*.promptspec.md` — Strategy specifications

## Spec Files

| File | Strategy | Notes |
|------|----------|-------|
| `chain-of-thought.promptspec.md` | single-call | Also used as `@refine` target by SC. `@note` citing Wei et al. 2022 / Kojima et al. 2022 |
| `self-consistency-solver.promptspec.md` | self-consistency | `@note` cites Wang et al. 2022. Output format: number only |
| `tree-of-thought-solver.promptspec.md` | tree-of-thought | Full BFS/DFS algorithm (Yao et al. 2023). Step-level thought decomposition + intermediate evaluation. Expensive (~90 calls/problem) |
| `simplified-tree-of-thought-solver.promptspec.md` | simplified-tree-of-thought | Generate → evaluate → synthesize with complete solutions. Cheap (~5 calls/problem). Used in benchmark demos |
| `reflection-solver.promptspec.md` | reflection | Generate → critique → revise loop. `@note` cites Shinn et al. 2023 / Madaan et al. 2023 |

## Test Commands

```bash
python -m pytest tests/ -q    # ~96 passed, ~105 skipped
```
