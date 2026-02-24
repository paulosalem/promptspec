// PromptSpec — Completion provider
//
// Provides:
//   • Directive completions when typing "@"
//   • Parameter value completions (key: value)
//   • Variable completions when typing "{{"
//   • File path completions for @refine
//   • Execution strategy completions for @execute
//   • Match case snippet

const vscode = require("vscode");
const path = require("path");
const { DIRECTIVES, DEBUG_DIRECTIVES, EXECUTION_STRATEGIES } = require("./directives");

// ── Directive completions ───────────────────────────────────────

function createDirectiveCompletions() {
  const items = [];
  for (const [name, info] of Object.entries(DIRECTIVES)) {
    const item = new vscode.CompletionItem(info.label, vscode.CompletionItemKind.Keyword);
    item.detail = info.detail;
    item.documentation = new vscode.MarkdownString(info.documentation);
    item.insertText = new vscode.SnippetString(info.snippet);
    item.filterText = `@${name}`;
    item.sortText = `0-${info.category}-${name}`;
    items.push(item);
  }
  for (const [name, info] of Object.entries(DEBUG_DIRECTIVES)) {
    const item = new vscode.CompletionItem(info.label, vscode.CompletionItemKind.Function);
    item.detail = info.detail;
    item.documentation = new vscode.MarkdownString(info.documentation);
    item.insertText = new vscode.SnippetString(info.snippet);
    item.filterText = `@${name}`;
    item.sortText = `1-debug-${name}`;
    items.push(item);
  }
  return items;
}

// ── Variable scanning ───────────────────────────────────────────

function collectVariables(document) {
  const vars = new Set();
  const re = /\{\{(\w+)\}\}/g;
  const text = document.getText();
  let m;
  while ((m = re.exec(text)) !== null) {
    if (m[1] !== "." && m[1] !== "#" && m[1] !== "/") {
      vars.add(m[1]);
    }
  }
  // Also collect @{var}
  const re2 = /@\{(\w+)\}/g;
  while ((m = re2.exec(text)) !== null) {
    vars.add(m[1]);
  }
  // Also collect variables from @match and @if lines
  const re3 = /^\s*@(?:match|if)\s+(\w+)/gm;
  while ((m = re3.exec(text)) !== null) {
    vars.add(m[1]);
  }
  return vars;
}

// ── Match-case snippet ─────────────────────────────────────────

function createMatchCaseSnippet() {
  const item = new vscode.CompletionItem('"value" ==>', vscode.CompletionItemKind.Snippet);
  item.detail = "Match case branch";
  item.documentation = new vscode.MarkdownString(
    "A case branch inside a `@match` block.\n\n" +
      '`"value" ==>` matches the literal value.\n' +
      "`_ ==>` is the default/fallback case."
  );
  item.insertText = new vscode.SnippetString('"${1:value}" ==>\n    ${2:content}');
  item.sortText = "2-match-case";
  return item;
}

function createDefaultCaseSnippet() {
  const item = new vscode.CompletionItem("_ ==>", vscode.CompletionItemKind.Snippet);
  item.detail = "Default match case (fallback)";
  item.documentation = new vscode.MarkdownString("The default/fallback case in a `@match` block.");
  item.insertText = new vscode.SnippetString("_ ==>\n    ${1:default content}");
  item.sortText = "2-match-default";
  return item;
}

// ── Provider ────────────────────────────────────────────────────

class PromptSpecCompletionProvider {
  provideCompletionItems(document, position, _token, _context) {
    const line = document.lineAt(position).text;
    const prefix = line.substring(0, position.character);

    // 1. Typing "@" at line start → directive completions
    if (/^\s*@\w*$/.test(prefix)) {
      return createDirectiveCompletions();
    }

    // 2. After @execute <strategy> or on @execute line → strategy names
    if (/^\s*@execute\s+\S*$/.test(prefix)) {
      return EXECUTION_STRATEGIES.map((s) => {
        const item = new vscode.CompletionItem(s, vscode.CompletionItemKind.EnumMember);
        item.detail = `Execution strategy`;
        return item;
      });
    }

    // 3. Parameter value completions: "key: " → suggest values
    const kvMatch = prefix.match(/^\s+(\w+):\s*(\S*)$/);
    if (kvMatch) {
      // Check preceding lines for the directive
      for (let i = position.line - 1; i >= 0 && i >= position.line - 5; i--) {
        const prevLine = document.lineAt(i).text;
        const dirMatch = prevLine.match(/^\s*@(\w+)/);
        if (dirMatch) {
          const directive = DIRECTIVES[dirMatch[1]];
          if (directive && directive.params[kvMatch[1]]) {
            return directive.params[kvMatch[1]].map((v) => {
              const item = new vscode.CompletionItem(v, vscode.CompletionItemKind.Value);
              item.detail = `${kvMatch[1]} value`;
              return item;
            });
          }
          break;
        }
      }
    }

    // 4. Inline parameter completions on directive line: @directive ... key:
    const inlineKvMatch = prefix.match(/^\s*@(\w+)\s+.*?(\w+):\s*(\S*)$/);
    if (inlineKvMatch) {
      const directive = DIRECTIVES[inlineKvMatch[1]];
      if (directive && directive.params[inlineKvMatch[2]]) {
        return directive.params[inlineKvMatch[2]].map((v) => {
          const item = new vscode.CompletionItem(v, vscode.CompletionItemKind.Value);
          item.detail = `${inlineKvMatch[2]} value`;
          return item;
        });
      }
    }

    // 5. Variable completions when typing {{ or @{
    if (/\{\{\w*$/.test(prefix) || /@\{\w*$/.test(prefix)) {
      const vars = collectVariables(document);
      return [...vars].map((v) => {
        const item = new vscode.CompletionItem(v, vscode.CompletionItemKind.Variable);
        item.detail = "Template variable";
        return item;
      });
    }

    // 6. Inside @match block → case snippets
    if (/^\s{2,}$/.test(prefix) || /^\s{2,}["_]/.test(prefix)) {
      // Check if we're inside a @match block
      for (let i = position.line - 1; i >= 0 && i >= position.line - 20; i--) {
        const prevLine = document.lineAt(i).text;
        if (/^\s*@match\b/.test(prevLine)) {
          return [createMatchCaseSnippet(), createDefaultCaseSnippet()];
        }
        if (/^\s*@\w+/.test(prevLine) && !/^\s*@match/.test(prevLine)) {
          break;
        }
      }
    }

    // 7. @refine file path completions
    if (/^\s*@refine\s+\S*$/.test(prefix)) {
      return this._getRefineFileCompletions(document);
    }

    return undefined;
  }

  async _getRefineFileCompletions(document) {
    const docDir = path.dirname(document.uri.fsPath);
    const workspaceFolders = vscode.workspace.workspaceFolders;
    if (!workspaceFolders) return [];

    const items = [];
    const pattern = new vscode.RelativePattern(workspaceFolders[0], "**/*.promptspec.md");
    const files = await vscode.workspace.findFiles(pattern, "**/node_modules/**", 50);

    for (const file of files) {
      if (file.fsPath === document.uri.fsPath) continue;
      const rel = path.relative(docDir, file.fsPath);
      const item = new vscode.CompletionItem(rel, vscode.CompletionItemKind.File);
      item.detail = "PromptSpec file";
      item.insertText = rel;
      items.push(item);
    }
    return items;
  }
}

// Trigger characters for completions
const TRIGGER_CHARACTERS = ["@", "{", ":", " "];

module.exports = { PromptSpecCompletionProvider, TRIGGER_CHARACTERS };
