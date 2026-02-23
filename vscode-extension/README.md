# PromptSpec — VSCode Syntax Highlighting

Syntax highlighting for [PromptSpec](../README.md) specification files (`.promptspec.md`).

## Features

- **Directive highlighting** — `@refine`, `@if`, `@else`, `@match`, `@revise`, `@expand`, `@contract`, `@canon`, `@cohere`, `@audience`, `@style`, `@summarize`, `@compress`, `@extract`, `@generate_examples`, `@output_format`, `@structural_constraints`, `@assert`, `@note`
- **Variable highlighting** — `{{name}}`, `{{#section}}`/`{{/section}}`, `{{.}}`, `@{name}`
- **Match case syntax** — `"value" ==>` and `_ ==>` (wildcard)
- **Escape sequences** — `@@property` rendered as dimmed (literal `@` in output)
- **Note blocks** — `@note` + indented body shown as comments
- **Debug queries** — `@directives?`, `@vars?`, `@structure?`
- **Directive arguments** — `key: value` pairs with type-aware coloring (booleans, numbers, strings)
- **File paths** — underlined after `@refine`
- **Markdown base** — headings, bold, italic, code blocks, links, lists
- **Two themes** — PromptSpec Dark and PromptSpec Light with branded colors

## Installation

### From Source (Development)

1. Copy or symlink this directory into your VSCode extensions folder:

   ```bash
   # macOS / Linux
   ln -s "$(pwd)" ~/.vscode/extensions/promptspec

   # Windows (PowerShell, run as admin)
   New-Item -ItemType SymbolicLink -Path "$env:USERPROFILE\.vscode\extensions\promptspec" -Target (Get-Location)
   ```

2. Reload VSCode (`Cmd+Shift+P` → "Developer: Reload Window")

3. Open any `.promptspec.md` file — syntax highlighting activates automatically

### Theme Activation

1. `Cmd+K Cmd+T` (or `Ctrl+K Ctrl+T`)
2. Select **PromptSpec Dark** or **PromptSpec Light**

## File Extension

PromptSpec files use the `.promptspec.md` extension. This keeps them recognizable as Markdown while enabling dedicated syntax highlighting.

```
specs/
├── base-analyst.promptspec.md
├── market-research-brief.promptspec.md
├── tutorial-generator.promptspec.md
└── vars/
    └── market-research-example.json
```

## Syntax Quick Reference

```markdown
@refine base-analyst.promptspec.md          # Include + merge external spec

@note                                        # Engineer comment (stripped from output)
  This is not included in the final prompt.

@match report_depth                          # Pattern matching
  "executive" ==>
    Executive summary content.
  "detailed" ==>
    Detailed report content.
  _ ==>
    Default fallback.

@if include_competitors                      # Conditional branch
  Competitor analysis goes here.
@else
  Skip competitors.

@revise mode: minimal                        # Semantic revision
  New requirement to integrate.

@audience "senior engineers"                 # Adapt for reader profile
@style "authoritative, data-driven"          # Apply presentation constraints

{{company}} operates in {{industry}}.        # Mustache variables
The code_@{version}_final is ready.          # Inline variable (braced)

@@property @@Override user@@example.com      # Escaped @ (literal in output)

@directives?                                 # Debug: list directives
@vars?                                       # Debug: list variables
```

## Color Palette

### Dark Theme (Dracula-inspired, vivid neon)

| Element | Color | Hex |
|---------|-------|-----|
| Directives (`@keyword`) | **Hot Pink** | `#FF79C6` |
| Variables (`{{name}}`) | **Bright Orange** | `#FFB86C` |
| Match cases (`"value"`) | **Neon Green** | `#50FA7B` |
| Match arrow (`==>`) | **Red** | `#FF5555` |
| File paths | **Cyan** | `#8BE9FD` |
| Strings (`"..."`) | **Yellow-Green** | `#F1FA8C` |
| Key names (`key:`) | **Cyan italic** | `#8BE9FD` |
| Key values | **Purple** | `#BD93F9` |
| Booleans / numbers | **Purple** | `#BD93F9` |
| `{{ }}` punctuation | **Purple** | `#BD93F9` |
| `#` / `/` operators | **Red bold** | `#FF5555` |
| Notes / `@@` escapes | **Dim gray** | `#6272A4` |
| Debug queries | **Yellow bold** | `#F1FA8C` |
| Headings | **Purple bold** | `#BD93F9` |
| Inline code | **Green** | `#50FA7B` |
| List markers | **Pink** | `#FF79C6` |

### Light Theme (Material-inspired, rich contrast)

| Element | Color | Hex |
|---------|-------|-----|
| Directives (`@keyword`) | **Vivid Purple** | `#AF00DB` |
| Variables (`{{name}}`) | **Burnt Orange** | `#D16900` |
| Match cases (`"value"`) | **Forest Green** | `#098658` |
| Match arrow (`==>`) | **Red** | `#E51400` |
| File paths | **Blue** | `#0070C1` |
| Strings (`"..."`) | **Green** | `#098658` |
| Key names (`key:`) | **Blue italic** | `#0070C1` |
| Key values | **Purple** | `#AF00DB` |
| Booleans / numbers | **Purple** | `#AF00DB` |
| `{{ }}` punctuation | **Purple** | `#AF00DB` |
| `#` / `/` operators | **Red bold** | `#E51400` |
| Notes / `@@` escapes | **Gray** | `#A0A1A7` |
| Debug queries | **Orange bold** | `#D16900` |
| Headings | **Blue bold** | `#0070C1` |
| Inline code | **Green** | `#098658` |
| List markers | **Purple** | `#AF00DB` |
