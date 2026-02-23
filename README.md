# PromptSpec

Compose prompts from specification files that use directives (`@refine`, `@if`, `@match`, `@tool`, `@note`), variables (`{{name}}`), and file includes — all processed by an LLM via multi-turn tool calling.

## Purpose

Prompt engineering at scale requires **composable, reusable prompt components**. Instead of copy-pasting prompt fragments, PromptSpec lets you:

- **Refine** a base persona with domain-specific instructions (`@refine base-analyst.promptspec.md`)
- **Branch** on variables (`@match language`, `@if include_exercises`)
- **Define tools** for function-calling agents (`@tool search_web`)
- **Annotate** with meta-comments stripped from final output (`@note`)
- **Parameterize** with variables (`{{company}}`, `{{audience}}`)

The full spec format is defined in [`prompts/writing/prompt-composition-helper.system.md`](src/promptspec/prompts/prompt-composition-helper.system.md).

## Installation

```bash
pip install promptspec
```

Or for development:

```bash
pip install -e ".[dev]"
```

This installs the `promptspec` command globally.

## Live Demo

Run the interactive demo to see all directives in action:

```bash
cd promptspec
./demo.sh          # run all 8 demos (pauses between each)
./demo.sh 3        # run only demo #3
```

The demo walks through progressively more powerful compositions — from basic `@refine` + `@match`, through content pipelines (`@extract` → `@summarize` → `@compress`), to the full prompt-refactoring pipeline that treats a messy prompt as code and refactors it semantically.

## Usage

### Batch Mode (with `--batch-only`)

```bash
# Market research brief with inline variables
promptspec specs/market-research-brief.promptspec.md \
  --var industry="electric vehicles" \
  --var company="Rivian" \
  --var report_depth=detailed \
  --var include_competitors=true \
  --var time_horizon="3 years" \
  --format markdown --batch-only

# Code review checklist with JSON vars file, saved to a file
promptspec specs/code-review-checklist.promptspec.md \
  --vars-file specs/vars/code-review-python.json \
  --format json --output review.json --batch-only

# Read spec from stdin
cat specs/tutorial-generator.promptspec.md | promptspec --stdin \
  --vars-file specs/vars/tutorial-fastapi.json --batch-only
```

### Interactive Mode (default)

```bash
# Launches composition, then prompts for follow-up refinements
promptspec specs/tutorial-generator.promptspec.md \
  --var topic="FastAPI" \
  --var audience=intermediate
```

### Output Formats

- **`--format markdown`** (default) — Human-readable Markdown; non-verbose prints only the prompt
- **`--format json`** — Machine-readable JSON with `composed_prompt`, `tools`, `issues`, and `tool_calls_made`
- **`--format xml`** — Raw XML output from the LLM for further processing
- **`--output report.md`** / **`-o report.md`** — Write to a file instead of stdout

### Tool/Function Calling

Use the `@tool` directive to define tools/functions that the composed prompt's consumer can invoke via LLM function calling. Tool definitions are compiled to OpenAI-compatible JSON Schema — which works universally across all providers via LiteLLM.

```markdown
@tool search_web
  Search the web for information and return relevant results.
  - query: string (required) — The search query
  - max_results: integer default: 5 — Maximum results

@tool get_weather
  Get current weather for a location.
  - location: string (required) — City name or coordinates
  - units: string enum: [celsius, fahrenheit] default: celsius — Units
```

Tools compose naturally with control-flow directives:

```markdown
@if include_web_tools
  @tool search_web
    Search the web for information.
    - query: string (required) — Search query

@match agent_type
  "researcher" ==>
    @tool read_paper
      Read an academic paper.
      - url: string (required) — Paper URL
  "coder" ==>
    @tool run_code
      Execute code in a sandbox.
      - code: string (required) — Code to run
```

In JSON output mode, tool definitions appear in the `tools` array alongside the composed prompt:

```json
{
  "composed_prompt": "You are a research assistant...",
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "search_web",
        "description": "Search the web for information.",
        "parameters": {
          "type": "object",
          "properties": {
            "query": { "type": "string", "description": "The search query" }
          },
          "required": ["query"]
        }
      }
    }
  ]
}
```

See [`specs/react-agent.promptspec.md`](specs/react-agent.promptspec.md) for a full example.

### Help

```bash
promptspec --help
```

## Example Specs

The `specs/` directory contains ready-to-use prompt specifications:

| Spec | Directives Used | Description |
|------|----------------|-------------|
| `base-analyst.promptspec.md` | _(none — base persona)_ | Reusable analytical persona for `@refine` |
| `chain-of-thought.promptspec.md` | _(none — reasoning strategy)_ | Reusable chain-of-thought reasoning for `@refine` |
| `react-agent.promptspec.md` | `@refine`, `@tool`, `@if`, `@match`, `@output_format` | ReAct research agent with tool definitions (search, read, calculate) |
| `market-research-brief.promptspec.md` | `@refine`, `@match`, `@if`, `@note` | Market research report with depth/competitor toggles |
| `code-review-checklist.promptspec.md` | `@refine`, `@match`, `@if`, `@note` | Language-specific code review with security audit |
| `tutorial-generator.promptspec.md` | `@match`, `@if`, `@@` escaping | Technical tutorial with audience-level adaptation |
| `consulting-proposal.promptspec.md` | `@refine`, `@audience`, `@style`, `@match`, `@summarize`, `@assert`, `@output_format` | Management consulting proposal with nested directives |
| `knowledge-base-article.promptspec.md` | `@extract`, `@summarize`, `@compress`, `@if`, `@structural_constraints`, `@output_format` | Internal knowledge base article with content pipeline |
| `api-docs-generator.promptspec.md` | `@generate_examples`, `@revise`, `@structural_constraints`, `@output_format` | API reference docs with auto-generated examples |
| **`multi-persona-debate.promptspec.md`** | `@expand`, `@contract`, `@revise`, `@match`, `@if`, `@audience`, `@output_format` | **Showcase**: dynamically grows/shrinks a debate prompt semantically — impossible with string templates |
| **`adaptive-interview.promptspec.md`** | `@refine`, `@audience`, `@style`, `@match`×2 nested, `@if`×3, `@compress`, `@expand`, `@generate_examples`, `@assert` | **Showcase**: deeply nested adaptive structure where outer transforms reshape inner results |
| **`prompt-refactoring-pipeline.promptspec.md`** | `@extract`, `@canon`, `@cohere`, `@revise`, `@expand`, `@contract`, `@structural_constraints`, `@assert`×3, `@output_format` | **Showcase**: treats a messy prompt as code and refactors it through a semantic pipeline |

Variable files in `specs/vars/` provide ready-made inputs for each spec.

### Running the New Specs

```bash
# Consulting proposal (transformation scope)
promptspec specs/consulting-proposal.promptspec.md \
  --vars-file specs/vars/consulting-proposal-example.json \
  --batch-only --verbose

# Knowledge base article (Kafka + migration guide)
promptspec specs/knowledge-base-article.promptspec.md \
  --vars-file specs/vars/knowledge-base-article-example.json \
  --batch-only --verbose

# API docs generator (TaskFlow API)
promptspec specs/api-docs-generator.promptspec.md \
  --vars-file specs/vars/api-docs-generator-example.json \
  --format markdown --batch-only --verbose
```

### Showcase Specs — What Only an LLM-Powered Macro System Can Do

These specs demonstrate capabilities impossible with traditional template engines:

```bash
# Multi-persona debate: @expand adds perspectives semantically,
# @contract removes bias at the meaning level, @revise adds
# synthesis requirements while maintaining consistency
promptspec specs/multi-persona-debate.promptspec.md \
  --vars-file specs/vars/multi-persona-debate-agi.json \
  --batch-only --verbose

# Adaptive interview: triple-nested @match (format → seniority → design),
# where @compress INSIDE a branch intelligently condenses content,
# and @audience at the top reshapes the ENTIRE result for the reader
promptspec specs/adaptive-interview.promptspec.md \
  --vars-file specs/vars/adaptive-interview-senior-backend.json \
  --batch-only --verbose

# Prompt refactoring pipeline: takes a messy, contradictory prompt
# and runs it through @extract → @canon → @cohere → @revise →
# @expand → @contract → @assert — treating prompts as code
promptspec specs/prompt-refactoring-pipeline.promptspec.md \
  --vars-file specs/vars/prompt-refactoring-example.json \
  --batch-only --verbose
```

## VSCode Extension

A syntax highlighting extension for `.promptspec.md` files is included in [`vscode-extension/`](vscode-extension/). It provides:

- Directive, variable, match-case, and escape highlighting
- Two color themes (PromptSpec Dark and PromptSpec Light)

**Quick install:**

```bash
ln -s "$(pwd)/vscode-extension" ~/.vscode/extensions/promptspec
```

Then reload VSCode. See [`vscode-extension/README.md`](vscode-extension/README.md) for details.

## Architecture

```
promptspec/
├── pyproject.toml          # Package configuration & dependencies
├── demo.sh                 # Interactive showcase of all directives
├── src/promptspec/         # Python package
│   ├── app.py              # CLI entry point (batch + interactive modes)
│   ├── controller.py       # PromptSpecController — drives the LLM loop
│   └── prompts/            # System prompt shipped with the package
├── specs/                  # Example prompt specifications
│   ├── base-analyst.promptspec.md
│   ├── market-research-brief.promptspec.md
│   ├── code-review-checklist.promptspec.md
│   ├── tutorial-generator.promptspec.md
│   ├── consulting-proposal.promptspec.md
│   ├── knowledge-base-article.promptspec.md
│   ├── api-docs-generator.promptspec.md
│   ├── multi-persona-debate.promptspec.md       # Showcase: semantic expand/contract
│   ├── adaptive-interview.promptspec.md         # Showcase: deep nesting + transforms
│   ├── prompt-refactoring-pipeline.promptspec.md # Showcase: prompt-as-code refactoring
│   ├── react-agent.promptspec.md                # Showcase: @tool directive with ReAct agent
│   └── vars/               # JSON variable files
├── tests/                  # Test suite
└── vscode-extension/       # Syntax highlighting for .promptspec.md files
```

The controller uses `LLMClient.complete_with_tools()` — a lightweight multi-turn tool-calling loop built on LiteLLM (no OpenAI Agents SDK dependency). The LLM reads the prompt spec, calls `read_file` when encountering `@refine <file>`, and calls `log_transition` to record composition steps. Directives are evaluated inside-out (innermost first) in a single LLM pass.

### Prompt Logging

Enable LLM call logging for debugging:

```bash
promptspec specs/market-research-brief.promptspec.md \
  --vars-file specs/vars/market-research-example.json \
  --batch-only --verbose
```

Set `log_dir` on `LLMClient` to write Markdown and/or JSONL logs of every LLM call to disk.
