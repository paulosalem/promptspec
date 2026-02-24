// PromptSpec — VS Code extension
//
// Features:
//   • Visual decorations (borders, backgrounds, variable pills)
//   • Completions for directives, parameters, variables, file paths
//   • Hover documentation for directives, variables, strategies
//   • Diagnostics (unknown directives, unclosed {{, missing files)
//   • Go-to-definition for @refine file references
//   • Document symbols (Outline view & breadcrumbs)
//   • Smart folding for directive blocks

const vscode = require("vscode");
const { PromptSpecCompletionProvider, TRIGGER_CHARACTERS } = require("./completions");
const { PromptSpecHoverProvider } = require("./hovers");
const { createDiagnosticsProvider } = require("./diagnostics");
const { PromptSpecDefinitionProvider } = require("./definitions");
const { PromptSpecDocumentSymbolProvider } = require("./symbols");
const { PromptSpecFoldingRangeProvider } = require("./folding");

// ── Decoration types ────────────────────────────────────────────

function createDecorations() {
  const execute = vscode.window.createTextEditorDecorationType({
    isWholeLine: true,
    borderWidth: "0 0 0 3px",
    borderStyle: "solid",
    borderColor: "#FFD700",
    backgroundColor: "rgba(255, 215, 0, 0.07)",
    overviewRulerColor: "#FFD700",
    overviewRulerLane: vscode.OverviewRulerLane.Left,
    before: {
      contentText: " ",
      width: "6px",
    },
  });

  const executeParam = vscode.window.createTextEditorDecorationType({
    isWholeLine: true,
    borderWidth: "0 0 0 3px",
    borderStyle: "solid",
    borderColor: "rgba(255, 215, 0, 0.3)",
    backgroundColor: "rgba(255, 215, 0, 0.03)",
    before: {
      contentText: " ",
      width: "6px",
    },
  });

  const prompt = vscode.window.createTextEditorDecorationType({
    isWholeLine: true,
    borderWidth: "0 0 0 3px",
    borderStyle: "solid",
    borderColor: "#00BFFF",
    backgroundColor: "rgba(0, 191, 255, 0.07)",
    overviewRulerColor: "#00BFFF",
    overviewRulerLane: vscode.OverviewRulerLane.Left,
    before: {
      contentText: " ",
      width: "6px",
    },
  });

  const tool = vscode.window.createTextEditorDecorationType({
    isWholeLine: true,
    borderWidth: "0 0 0 3px",
    borderStyle: "solid",
    borderColor: "#00CED1",
    backgroundColor: "rgba(0, 206, 209, 0.05)",
    before: { contentText: " ", width: "6px" },
  });

  const controlFlow = vscode.window.createTextEditorDecorationType({
    isWholeLine: true,
    borderWidth: "0 0 0 2px",
    borderStyle: "solid",
    borderColor: "#FF79C6",
    before: { contentText: " ", width: "6px" },
  });

  const matchCase = vscode.window.createTextEditorDecorationType({
    isWholeLine: true,
    borderWidth: "0 0 0 2px",
    borderStyle: "solid",
    borderColor: "#B34040",
    backgroundColor: "rgba(179, 64, 64, 0.04)",
    before: { contentText: " ", width: "6px" },
  });

  const noteBlock = vscode.window.createTextEditorDecorationType({
    isWholeLine: true,
    borderWidth: "0 0 0 1px",
    borderStyle: "dotted",
    borderColor: "#6272A4",
    backgroundColor: "rgba(98, 114, 164, 0.06)",
    opacity: "0.7",
    before: { contentText: " ", width: "6px" },
  });

  const variable = vscode.window.createTextEditorDecorationType({
    backgroundColor: "rgba(255, 184, 108, 0.12)",
    borderRadius: "3px",
  });

  return { execute, executeParam, prompt, tool, controlFlow, matchCase, noteBlock, variable };
}

// ── Regex patterns ──────────────────────────────────────────────

const RE_EXECUTE = /^\s*@execute\b/;
const RE_EXECUTE_PARAM = /^\s{2,}\w+:\s*.+/; // indented key: value after @execute
const RE_PROMPT = /^\s*@prompt\b/;
const RE_TOOL = /^\s*@tool\b/;
const RE_CONTROL = /^\s*@(?:match|if|else)\b/;
const RE_MATCH_CASE = /^\s*(?:"[^"]*"|_)\s*==>/;
const RE_NOTE_START = /^\s*@note\s*$/;
const RE_VARIABLE = /\{\{[^}]+\}\}/g;

// ── Update decorations ─────────────────────────────────────────

function updateDecorations(editor, decs) {
  if (!editor || editor.document.languageId !== "promptspec") return;

  const doc = editor.document;
  const executeRanges = [];
  const executeParamRanges = [];
  const promptRanges = [];
  const toolRanges = [];
  const controlRanges = [];
  const matchCaseRanges = [];
  const noteRanges = [];
  const variableRanges = [];

  let inNote = false;
  let noteIndent = 0;
  let lastWasExecute = false;

  for (let i = 0; i < doc.lineCount; i++) {
    const line = doc.lineAt(i);
    const text = line.text;
    const range = line.range;

    // Track @note blocks
    if (RE_NOTE_START.test(text)) {
      inNote = true;
      noteIndent = text.search(/\S/);
      noteRanges.push(range);
      lastWasExecute = false;
      continue;
    }
    if (inNote) {
      // Note block continues while indented deeper or blank
      const nonWs = text.search(/\S/);
      if (text.trim() === "" || nonWs > noteIndent) {
        noteRanges.push(range);
        continue;
      }
      inNote = false;
    }

    // @execute line and its indented params
    if (RE_EXECUTE.test(text)) {
      executeRanges.push(range);
      lastWasExecute = true;
    } else if (lastWasExecute && RE_EXECUTE_PARAM.test(text)) {
      executeParamRanges.push(range);
    } else {
      lastWasExecute = false;

      if (RE_PROMPT.test(text)) {
        promptRanges.push(range);
      } else if (RE_TOOL.test(text)) {
        toolRanges.push(range);
      } else if (RE_CONTROL.test(text)) {
        controlRanges.push(range);
      } else if (RE_MATCH_CASE.test(text)) {
        matchCaseRanges.push(range);
      }
    }

    // {{variables}} on any line
    let m;
    RE_VARIABLE.lastIndex = 0;
    while ((m = RE_VARIABLE.exec(text)) !== null) {
      const start = new vscode.Position(i, m.index);
      const end = new vscode.Position(i, m.index + m[0].length);
      variableRanges.push(new vscode.Range(start, end));
    }
  }

  editor.setDecorations(decs.execute, executeRanges);
  editor.setDecorations(decs.executeParam, executeParamRanges);
  editor.setDecorations(decs.prompt, promptRanges);
  editor.setDecorations(decs.tool, toolRanges);
  editor.setDecorations(decs.controlFlow, controlRanges);
  editor.setDecorations(decs.matchCase, matchCaseRanges);
  editor.setDecorations(decs.noteBlock, noteRanges);
  editor.setDecorations(decs.variable, variableRanges);
}

// ── Lifecycle ───────────────────────────────────────────────────

/** @param {vscode.ExtensionContext} context */
function activate(context) {
  const selector = { language: "promptspec", scheme: "file" };
  const decs = createDecorations();

  // ── Decorations ────────────────────────────────────────────
  if (vscode.window.activeTextEditor) {
    updateDecorations(vscode.window.activeTextEditor, decs);
  }

  context.subscriptions.push(
    vscode.window.onDidChangeActiveTextEditor((editor) => {
      if (editor) updateDecorations(editor, decs);
    })
  );

  let timeout;
  context.subscriptions.push(
    vscode.workspace.onDidChangeTextDocument((event) => {
      const editor = vscode.window.activeTextEditor;
      if (editor && event.document === editor.document) {
        clearTimeout(timeout);
        timeout = setTimeout(() => updateDecorations(editor, decs), 150);
      }
    })
  );

  context.subscriptions.push(...Object.values(decs));

  // ── Completions ────────────────────────────────────────────
  context.subscriptions.push(
    vscode.languages.registerCompletionItemProvider(
      selector,
      new PromptSpecCompletionProvider(),
      ...TRIGGER_CHARACTERS
    )
  );

  // ── Hovers ─────────────────────────────────────────────────
  context.subscriptions.push(
    vscode.languages.registerHoverProvider(selector, new PromptSpecHoverProvider())
  );

  // ── Diagnostics ────────────────────────────────────────────
  createDiagnosticsProvider(context);

  // ── Go-to-definition ──────────────────────────────────────
  context.subscriptions.push(
    vscode.languages.registerDefinitionProvider(selector, new PromptSpecDefinitionProvider())
  );

  // ── Document symbols (Outline) ────────────────────────────
  context.subscriptions.push(
    vscode.languages.registerDocumentSymbolProvider(selector, new PromptSpecDocumentSymbolProvider())
  );

  // ── Folding ────────────────────────────────────────────────
  context.subscriptions.push(
    vscode.languages.registerFoldingRangeProvider(selector, new PromptSpecFoldingRangeProvider())
  );
}

function deactivate() {}

module.exports = { activate, deactivate };
