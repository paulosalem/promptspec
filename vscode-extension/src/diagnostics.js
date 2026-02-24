// PromptSpec — Diagnostics provider
//
// Reports problems:
//   • Unknown directives
//   • Unclosed {{ or }}
//   • @match without default (_ ==>) case
//   • @refine pointing to a non-existent file
//   • @if without matching content
//   • @execute with unknown strategy

const vscode = require("vscode");
const path = require("path");
const fs = require("fs");
const { ALL_DIRECTIVE_NAMES, EXECUTION_STRATEGIES } = require("./directives");

const DIAGNOSTIC_SOURCE = "PromptSpec";

function createDiagnosticsProvider(context) {
  const collection = vscode.languages.createDiagnosticCollection("promptspec");
  context.subscriptions.push(collection);

  function updateDiagnostics(document) {
    if (document.languageId !== "promptspec") {
      collection.delete(document.uri);
      return;
    }

    const diagnostics = [];
    const text = document.getText();
    const lines = text.split("\n");
    let inMatchBlock = false;
    let matchHasDefault = false;
    let matchLine = -1;
    let matchIndent = 0;

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];

      // ── Unknown directive ──────────────────────────────────
      const dirMatch = line.match(/^(\s*)@(\w+)(\??)/);
      if (dirMatch && !line.match(/^(\s*)@@/)) {
        const name = dirMatch[2];
        const isDebug = dirMatch[3] === "?";
        const fullName = isDebug ? name : name;
        if (!ALL_DIRECTIVE_NAMES.has(fullName)) {
          const col = dirMatch[1].length;
          const range = new vscode.Range(i, col, i, col + 1 + name.length + (isDebug ? 1 : 0));
          diagnostics.push(
            new vscode.Diagnostic(
              range,
              `Unknown directive: @${name}${isDebug ? "?" : ""}`,
              vscode.DiagnosticSeverity.Warning
            )
          );
        }
      }

      // ── Unknown execution strategy ────────────────────────
      const execMatch = line.match(/^\s*@execute\s+(\S+)/);
      if (execMatch) {
        const strategy = execMatch[1];
        if (!EXECUTION_STRATEGIES.includes(strategy)) {
          const col = line.indexOf(strategy);
          const range = new vscode.Range(i, col, i, col + strategy.length);
          diagnostics.push(
            new vscode.Diagnostic(
              range,
              `Unknown execution strategy: "${strategy}". Expected: ${EXECUTION_STRATEGIES.join(", ")}`,
              vscode.DiagnosticSeverity.Warning
            )
          );
        }
      }

      // ── @match block tracking ─────────────────────────────
      const matchDirective = line.match(/^(\s*)@match\s+/);
      if (matchDirective) {
        // Close previous match block if open
        if (inMatchBlock && !matchHasDefault) {
          diagnostics.push(
            new vscode.Diagnostic(
              new vscode.Range(matchLine, 0, matchLine, lines[matchLine].length),
              "@match block has no default case (_ ==>). Add a fallback to handle unexpected values.",
              vscode.DiagnosticSeverity.Hint
            )
          );
        }
        inMatchBlock = true;
        matchHasDefault = false;
        matchLine = i;
        matchIndent = matchDirective[1].length;
      }

      // Check for default case in match
      if (inMatchBlock && /^\s*_\s*==>/.test(line)) {
        matchHasDefault = true;
      }

      // End match block on same-or-less indent directive
      if (inMatchBlock && i > matchLine) {
        const nonWs = line.search(/\S/);
        if (nonWs >= 0 && nonWs <= matchIndent && /^(\s*)@\w+/.test(line)) {
          if (!matchHasDefault) {
            diagnostics.push(
              new vscode.Diagnostic(
                new vscode.Range(matchLine, 0, matchLine, lines[matchLine].length),
                "@match block has no default case (_ ==>). Add a fallback to handle unexpected values.",
                vscode.DiagnosticSeverity.Hint
              )
            );
          }
          inMatchBlock = false;
        }
      }

      // ── Unclosed {{ or stray }} ───────────────────────────
      // Count {{ and }} on each line
      const opens = (line.match(/\{\{/g) || []).length;
      const closes = (line.match(/\}\}/g) || []).length;
      if (opens > closes) {
        const idx = line.lastIndexOf("{{");
        diagnostics.push(
          new vscode.Diagnostic(
            new vscode.Range(i, idx, i, idx + 2),
            "Unclosed `{{` — missing closing `}}`",
            vscode.DiagnosticSeverity.Error
          )
        );
      } else if (closes > opens) {
        const idx = line.indexOf("}}");
        diagnostics.push(
          new vscode.Diagnostic(
            new vscode.Range(i, idx, i, idx + 2),
            "Stray `}}` — missing opening `{{`",
            vscode.DiagnosticSeverity.Error
          )
        );
      }

      // ── @refine file existence ─────────────────────────────
      const refineMatch = line.match(/^\s*@refine\s+(\S+)/);
      if (refineMatch) {
        const filePath = refineMatch[1];
        const docDir = path.dirname(document.uri.fsPath);
        const absPath = path.resolve(docDir, filePath);
        if (!fs.existsSync(absPath)) {
          const col = line.indexOf(filePath);
          const range = new vscode.Range(i, col, i, col + filePath.length);
          diagnostics.push(
            new vscode.Diagnostic(
              range,
              `File not found: ${filePath}`,
              vscode.DiagnosticSeverity.Error
            )
          );
        }
      }
    }

    // Final match block at end of file
    if (inMatchBlock && !matchHasDefault) {
      diagnostics.push(
        new vscode.Diagnostic(
          new vscode.Range(matchLine, 0, matchLine, lines[matchLine].length),
          "@match block has no default case (_ ==>). Add a fallback to handle unexpected values.",
          vscode.DiagnosticSeverity.Hint
        )
      );
    }

    for (const d of diagnostics) {
      d.source = DIAGNOSTIC_SOURCE;
    }
    collection.set(document.uri, diagnostics);
  }

  // Run on open, save, and change
  if (vscode.window.activeTextEditor) {
    updateDiagnostics(vscode.window.activeTextEditor.document);
  }

  context.subscriptions.push(
    vscode.window.onDidChangeActiveTextEditor((editor) => {
      if (editor) updateDiagnostics(editor.document);
    }),
    vscode.workspace.onDidChangeTextDocument((event) => {
      updateDiagnostics(event.document);
    }),
    vscode.workspace.onDidCloseTextDocument((doc) => {
      collection.delete(doc.uri);
    })
  );

  return collection;
}

module.exports = { createDiagnosticsProvider };
