// PromptSpec directive catalog — documentation, parameters, snippets
//
// Single source of truth for all directives. Used by completions,
// hovers, diagnostics, and signature help.

const DIRECTIVES = {
  // ── Composition ───────────────────────────────────────────────
  refine: {
    label: "@refine",
    detail: "Include & specialise from another spec file",
    documentation:
      "Merges the content of another `.promptspec.md` file into the current spec. " +
      "The included file's directives are applied, and the current spec can override or extend them.\n\n" +
      "**Parameters:**\n" +
      "- `mingle: true|false` — Whether to interleave content (default: `true`) or append as-is\n\n" +
      "**Example:**\n```\n@refine base-prompt.promptspec.md\n@refine shared/safety.promptspec.md mingle: false\n```",
    snippet: "@refine ${1:file.promptspec.md}",
    params: { mingle: ["true", "false"] },
    category: "Composition",
  },
  expand: {
    label: "@expand",
    detail: "Add new content without removing existing",
    documentation:
      "Injects additional requirements or content into the prompt without altering what's already there.\n\n" +
      "**Parameters:**\n" +
      "- `mode: minimal|editorial` — How aggressively to integrate (default: `minimal`)\n" +
      "- `placement: append|integrate` — Where to put new content\n\n" +
      "**Example:**\n```\n@expand mode: editorial\n  Add a safety considerations section.\n```",
    snippet: "@expand\n  ${1:content to add}",
    params: { mode: ["minimal", "editorial"], placement: ["append", "integrate"] },
    category: "Composition",
  },
  contract: {
    label: "@contract",
    detail: "Remove or weaken existing constraints",
    documentation:
      "Removes or softens requirements in the prompt.\n\n" +
      "**Parameters:**\n" +
      "- `mode: minimal|editorial` — How aggressively to remove\n" +
      "- `safety: strict|allow` — Whether safety-related constraints can be removed (default: `strict`)\n\n" +
      "**Example:**\n```\n@contract safety: allow\n  Remove the length limits.\n```",
    snippet: "@contract\n  ${1:constraint to remove}",
    params: { mode: ["minimal", "editorial"], safety: ["strict", "allow"] },
    category: "Composition",
  },
  revise: {
    label: "@revise",
    detail: "Replace conflicting requirements with new ones",
    documentation:
      "Replaces existing requirements that conflict with the new instruction.\n\n" +
      "**Parameters:**\n" +
      "- `mode: minimal|editorial` — How aggressively to revise\n\n" +
      "**Example:**\n```\n@revise mode: editorial\n  Output must be JSON only, no markdown.\n```",
    snippet: "@revise\n  ${1:replacement instruction}",
    params: { mode: ["minimal", "editorial"] },
    category: "Composition",
  },

  // ── Semantic Transform ────────────────────────────────────────
  canon: {
    label: "@canon",
    detail: "Normalise structure and terminology",
    documentation:
      "Standardises headings, lists, and terminology across the prompt.\n\n" +
      "**Parameters:**\n" +
      "- `headings: keep|normalize`\n" +
      "- `lists: keep|normalize`\n" +
      "- `terminology: keep|normalize`\n\n" +
      "**Example:**\n```\n@canon headings: normalize terminology: normalize\n```",
    snippet: "@canon ${1:headings: normalize}",
    params: { headings: ["keep", "normalize"], lists: ["keep", "normalize"], terminology: ["keep", "normalize"] },
    category: "Semantic Transform",
  },
  cohere: {
    label: "@cohere",
    detail: "Rewrite as a single coherent instruction set",
    documentation:
      "Merges all accumulated content into one clean, non-redundant prompt.\n\n" +
      "**Parameters:**\n" +
      "- `aggressiveness: low|medium|high` — How much to restructure\n\n" +
      "**Example:**\n```\n@cohere aggressiveness: medium\n```",
    snippet: "@cohere ${1:aggressiveness: medium}",
    params: { aggressiveness: ["low", "medium", "high"] },
    category: "Semantic Transform",
  },
  audience: {
    label: "@audience",
    detail: "Adapt prompt for a specific reader profile",
    documentation:
      "Adjusts the prompt's language, detail level, and assumptions for the target audience.\n\n" +
      "**Example:**\n```\n@audience\n  Senior Python engineers familiar with async/await.\n```",
    snippet: "@audience\n  ${1:audience description}",
    params: {},
    category: "Semantic Transform",
  },
  style: {
    label: "@style",
    detail: "Apply tone, voice, and formatting preferences",
    documentation:
      "Sets the stylistic direction for the prompt's output.\n\n" +
      "**Example:**\n```\n@style\n  Concise, direct, and friendly. Use bullet points.\n```",
    snippet: "@style\n  ${1:style description}",
    params: {},
    category: "Semantic Transform",
  },

  // ── Lossy Content ─────────────────────────────────────────────
  summarize: {
    label: "@summarize",
    detail: "Replace content with a summary",
    documentation:
      "Condenses the prompt content into a shorter form.\n\n" +
      "**Parameters:**\n" +
      "- `length: short|medium|long`\n" +
      "- `focus: requirements|rationale|mixed`\n\n" +
      "**Example:**\n```\n@summarize length: short focus: requirements\n```",
    snippet: "@summarize ${1:length: short} ${2:focus: requirements}",
    params: { length: ["short", "medium", "long"], focus: ["requirements", "rationale", "mixed"] },
    category: "Lossy Content",
  },
  compress: {
    label: "@compress",
    detail: "Reduce token footprint while preserving meaning",
    documentation:
      "Aggressively reduces the prompt's size to fit token budgets.\n\n" +
      "**Parameters:**\n" +
      "- `target: tokens|chars` — Unit of measurement\n" +
      "- `budget: <number>` — Target size\n" +
      "- `preserve: hard|balanced` — How strictly to keep key content\n\n" +
      "**Example:**\n```\n@compress target: tokens budget: 800 preserve: balanced\n```",
    snippet: "@compress ${1:target: tokens} ${2:budget: 800}",
    params: { target: ["tokens", "chars"], preserve: ["hard", "balanced"] },
    category: "Lossy Content",
  },
  extract: {
    label: "@extract",
    detail: "Extract a subset into structured form",
    documentation:
      "Pulls out specific information from the prompt into a structured format.\n\n" +
      "**Parameters:**\n" +
      "- `format: bullets|json|yaml|markdown`\n\n" +
      "**Example:**\n```\n@extract format: json\n  All MUST constraints\n```",
    snippet: "@extract ${1:format: json}\n  ${2:what to extract}",
    params: { format: ["bullets", "json", "yaml", "markdown"] },
    category: "Lossy Content",
  },

  // ── Generation ────────────────────────────────────────────────
  generate_examples: {
    label: "@generate_examples",
    detail: "Add illustrative examples to the prompt",
    documentation:
      "Generates example input/output pairs to make the prompt clearer.\n\n" +
      "**Parameters:**\n" +
      "- `count: <number>` — How many examples\n" +
      "- `style: minimal|realistic`\n\n" +
      "**Example:**\n```\n@generate_examples count: 3 style: realistic\n```",
    snippet: "@generate_examples ${1:count: 3} ${2:style: realistic}",
    params: { count: null, style: ["minimal", "realistic"] },
    category: "Generation",
  },

  // ── Constraints ───────────────────────────────────────────────
  output_format: {
    label: "@output_format",
    detail: "Specify the required output format",
    documentation:
      "Ensures the prompt explicitly describes the expected output structure.\n\n" +
      "**Parameters:**\n" +
      "- `enforce: strict|soft` — How strictly to enforce format compliance\n\n" +
      "**Example:**\n```\n@output_format enforce: strict\n  Return JSON: { \"answer\": string, \"sources\": string[] }\n```",
    snippet: "@output_format ${1:enforce: strict}\n  ${2:format description}",
    params: { enforce: ["strict", "soft"] },
    category: "Constraints",
  },
  structural_constraints: {
    label: "@structural_constraints",
    detail: "Reshape prompt to required sections/order",
    documentation:
      "Enforces a specific structure (sections, headings, ordering) on the prompt.\n\n" +
      "**Parameters:**\n" +
      "- `strict: true|false`\n\n" +
      "**Example:**\n```\n@structural_constraints\n  Sections: Goal, Constraints, Output Format\n```",
    snippet: "@structural_constraints\n  ${1:structure description}",
    params: { strict: ["true", "false"] },
    category: "Constraints",
  },
  assert: {
    label: "@assert",
    detail: "Enforce a correctness condition on the prompt",
    documentation:
      "Validates that the composed prompt satisfies a condition. Fails composition if not met.\n\n" +
      "**Parameters:**\n" +
      "- `severity: error|warning` — Whether violation blocks composition\n\n" +
      "**Example:**\n```\n@assert severity: error The prompt must include an output schema.\n@assert severity: warning The prompt should mention error handling.\n```",
    snippet: "@assert ${1:severity: error} ${2:condition}",
    params: { severity: ["error", "warning"] },
    category: "Constraints",
  },

  // ── Control Flow ──────────────────────────────────────────────
  if: {
    label: "@if",
    detail: "Conditional content based on a variable",
    documentation:
      "Includes the indented block only when the variable is truthy.\n\n" +
      "**Example:**\n```\n@if include_safety\n  Always refuse harmful requests.\n@else\n  Be helpful and direct.\n```",
    snippet: "@if ${1:variable_name}\n  ${2:content when true}",
    params: {},
    category: "Control Flow",
  },
  else: {
    label: "@else",
    detail: "Fallback branch for @if",
    documentation:
      "Provides content when the preceding `@if` condition is false.\n\n" +
      "**Example:**\n```\n@if verbose_mode\n  Explain each step in detail.\n@else\n  Be concise.\n```",
    snippet: "@else\n  ${1:fallback content}",
    params: {},
    category: "Control Flow",
  },
  match: {
    label: "@match",
    detail: "Pattern matching on a variable's value",
    documentation:
      "Selects content based on which case matches the variable. Use `_ ==>` as the default/fallback case.\n\n" +
      "**Example:**\n```\n@match user_tier\n  \"free\" ==>\n    Basic features only.\n  \"pro\" ==>\n    All features unlocked.\n  _ ==>\n    Unknown tier.\n```",
    snippet: "@match ${1:variable_name}\n  \"${2:value}\" ==>\n    ${3:content}\n  _ ==>\n    ${4:default content}",
    params: {},
    category: "Control Flow",
  },

  // ── Multi-Prompt & Execution ──────────────────────────────────
  prompt: {
    label: "@prompt",
    detail: "Define a named prompt section",
    documentation:
      "Slices the spec into multiple named prompts for multi-step execution strategies.\n\n" +
      "**Example:**\n```\n@prompt generate\n  Generate 3 candidate approaches.\n\n@prompt evaluate\n  Score each approach on correctness and clarity.\n```",
    snippet: "@prompt ${1:name}\n  ${2:prompt content}",
    params: {},
    category: "Execution",
  },
  execute: {
    label: "@execute",
    detail: "Declare the execution strategy",
    documentation:
      "Specifies how the prompt should be executed by the LLM. This is metadata — " +
      "it does not change the prompt text, but tells the runtime which strategy to use.\n\n" +
      "**Strategies:**\n" +
      "- `single-call` — One LLM call (default)\n" +
      "- `self-consistency` — Multiple samples, majority vote\n" +
      "- `tree-of-thought` — Generate → Evaluate → Synthesise\n" +
      "- `reflection` — Generate → Critique → Revise\n\n" +
      "**Common Parameters:**\n" +
      "- `mode: minimal|full`\n" +
      "- `depth: <number>` — Iteration depth\n" +
      "- `branching_factor: <number>` — Branches for tree-of-thought\n" +
      "- `samples: <number>` — Sample count for self-consistency\n\n" +
      "**Example:**\n```\n@execute tree-of-thought\n  branching_factor: 3\n  depth: 2\n```",
    snippet: "@execute ${1|single-call,self-consistency,tree-of-thought,reflection|}",
    params: { mode: ["minimal", "full"] },
    category: "Execution",
  },

  // ── Tools ─────────────────────────────────────────────────────
  tool: {
    label: "@tool",
    detail: "Define a callable tool/function for the LLM",
    documentation:
      "Declares a function that the LLM can invoke. Parameters are listed as indented items.\n\n" +
      "**Parameter syntax:** `- name: type (required|optional) — description`\n\n" +
      "**Example:**\n```\n@tool search_web\n  Search the web for information.\n  - query: string (required) — The search query\n  - max_results: integer (optional) — Maximum results to return\n```",
    snippet: "@tool ${1:function_name}\n  ${2:Description of the tool.}\n  - ${3:param}: ${4:string} (${5|required,optional|}) — ${6:description}",
    params: {},
    category: "Tools",
  },

  // ── Meta & Debug ──────────────────────────────────────────────
  note: {
    label: "@note",
    detail: "Comment block (stripped before LLM sees the prompt)",
    documentation:
      "A documentation/comment block. Everything indented under `@note` is removed during composition " +
      "and never sent to the LLM.\n\n" +
      "**Example:**\n```\n@note\n  This section was added to fix issue #42.\n  TODO: revisit after v2 launch.\n```",
    snippet: "@note\n  ${1:comment}",
    params: {},
    category: "Meta",
  },
};

// Debug query pseudo-directives
const DEBUG_DIRECTIVES = {
  "directives?": {
    label: "@directives?",
    detail: "Debug: list all recognised directives",
    documentation: "Outputs a list of all directives the composition engine recognises. Useful for debugging.",
    snippet: "@directives?",
    category: "Debug",
  },
  "vars?": {
    label: "@vars?",
    detail: "Debug: list available and missing variables",
    documentation: "Shows which `{{variables}}` are defined and which are still unresolved. Useful for debugging.",
    snippet: "@vars?",
    category: "Debug",
  },
  "structure?": {
    label: "@structure?",
    detail: "Debug: describe the prompt's structure",
    documentation: "Outputs an outline of the prompt's current structure after composition. Useful for debugging.",
    snippet: "@structure?",
    category: "Debug",
  },
};

// Execution strategy names (valid values for @execute)
const EXECUTION_STRATEGIES = ["single-call", "self-consistency", "tree-of-thought", "reflection"];

// Set of all known directive names (for diagnostics)
const ALL_DIRECTIVE_NAMES = new Set([
  ...Object.keys(DIRECTIVES),
  ...Object.keys(DEBUG_DIRECTIVES).map((k) => k.replace("?", "")),
]);

module.exports = { DIRECTIVES, DEBUG_DIRECTIVES, EXECUTION_STRATEGIES, ALL_DIRECTIVE_NAMES };
