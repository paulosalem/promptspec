# Copilot Instructions — PromptSpec

## Project Overview

PromptSpec is a prompt specification language and toolchain for composing, executing, and benchmarking LLM prompting strategies. It includes:
- `src/promptspec/` — Core library (controller, parser, composition)
- `specs/` — PromptSpec files (`.promptspec.md`) for various strategies
- `scripts/benchmark_strategies.py` — Benchmark runner using lm-eval
- `vscode-extension/` — VS Code language support
- Depends on `ellements` (sibling repo) for LLM client and execution strategies

## Architecture Rules

### Benchmark Runner — Event Loop Management

- **NEVER create one event loop per sample for strategy execution.** This was the root cause of cascading "Connection error" failures after ~12-15 samples. Accumulated aiohttp sessions in destroyed loops exhaust sockets/FDs.
- **Strategy path**: All samples run through a SINGLE event loop with `asyncio.Semaphore` for concurrency control. See `_run_all_strategy()` in `benchmark_strategies.py`.
- **Single-call path**: Uses `ThreadPoolExecutor` with sync `litellm.completion()` — no event loop needed.
- **Always clean up loops**: `shutdown_asyncgens()` → cancel pending → `loop.close()` → `gc.collect()`.

### PromptSpec Composition

- **Root text cascading**: Text before the first `@prompt` (prefix) and after the last `@prompt` (suffix) is automatically prepended/appended to each named sub-prompt. The `@execute` block is stripped from the prefix. Other directives (`@refine`, `@output_format`, etc.) are preserved.
- **`@note` blocks** are stripped during composition — they're for prompt engineers, not the LLM.
- **`@refine` compatibility**: A spec with `@execute` can still be used as a `@refine` target. The parent spec's `@execute` takes precedence.

### Spec File Conventions

- **One spec per strategy**: Don't create separate "baseline" and "reusable" versions. A single spec serves both roles (standalone + `@refine` target).
- **Specs must align with literature**: Each spec should have a `@note` block citing the original paper. Prompts should reflect the canonical technique, not arbitrary variants.
- **`{{problem}}`**: Always include the problem placeholder in specs that need per-sample substitution.

### Strategy Integration

- Strategies come from the `ellements` library (`ellements.patterns.*`)
- The `@execute` directive maps to strategy types: `single-call`, `self-consistency`, `tree-of-thought`, `simplified-tree-of-thought`, `reflection`
- `tree-of-thought` = full BFS/DFS algorithm (canonical Yao et al. 2023, expensive ~90 calls/problem)
- `simplified-tree-of-thought` = generate→evaluate→synthesize (~5 calls/problem, used in benchmark demos)
- Strategy configs (branching_factor, samples, temperature, max_depth, beam_width, search_type) go in the `@execute` block as indented key-value params

## Critical Patterns

### Concurrency in Benchmarks

```python
# BAD — one loop per sample, connections leak
for sample in samples:
    loop = asyncio.new_event_loop()
    result = loop.run_until_complete(strategy.execute(...))
    loop.close()

# GOOD — single loop, semaphore concurrency
async def _run_all():
    sem = asyncio.Semaphore(2)
    async def process(idx, req):
        async with sem:
            return await strategy.execute(...)
    return await asyncio.gather(*[process(i, r) for i, r in enumerate(requests)])

loop = asyncio.new_event_loop()
results = loop.run_until_complete(_run_all())
```

### LiteLLM LoggingWorker Reset

When switching from composition phase (uses `asyncio.run()`) to benchmark phase (new event loops), disable the LiteLLM async logging worker to prevent stale Queue errors:

```python
import litellm.litellm_core_utils.logging_worker as _lw
_lw.LoggingWorker.start = lambda self: None
_lw.LoggingWorker.enqueue = lambda self, *a, **kw: None
```

## Test Commands

```bash
# Full test suite
python -m pytest tests/ -q

# Expected: ~94 passed, ~105 skipped (skips are integration tests needing API keys)
```

## Key Files

- `src/promptspec/controller.py` — Composition engine, root text cascading (`_extract_root_text`, `_cascade_root_context`)
- `scripts/benchmark_strategies.py` — Benchmark runner (single event loop for strategies)
- `specs/chain-of-thought.promptspec.md` — CoT spec (also serves as @refine target)
- `specs/self-consistency-solver.promptspec.md` — SC spec
- `specs/tree-of-thought-solver.promptspec.md` — ToT spec (parallel independent paths)
- `demo-benchmark.sh` — Demo script for running benchmarks
