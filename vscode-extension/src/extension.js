// PromptSpec — VS Code decoration provider
//
// Adds visual embellishments to .promptspec.md files:
//   • @execute lines  — gold left border + subtle background
//   • @prompt blocks   — blue left border + subtle background
//   • @tool lines      — teal left border
//   • @match / @if     — pink left border
//   • match cases (==>) — green left accent
//   • @note blocks     — dimmed background + dotted border
//   • {{variables}}    — subtle orange background pill

const vscode = require("vscode");

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
    borderColor: "#50FA7B",
    backgroundColor: "rgba(80, 250, 123, 0.04)",
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
  const decs = createDecorations();

  // Decorate active editor on startup
  if (vscode.window.activeTextEditor) {
    updateDecorations(vscode.window.activeTextEditor, decs);
  }

  // Re-decorate when switching editors
  context.subscriptions.push(
    vscode.window.onDidChangeActiveTextEditor((editor) => {
      if (editor) updateDecorations(editor, decs);
    })
  );

  // Re-decorate on document changes (debounced)
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

  // Clean up decoration types on deactivate
  context.subscriptions.push(
    ...Object.values(decs)
  );
}

function deactivate() {}

module.exports = { activate, deactivate };
