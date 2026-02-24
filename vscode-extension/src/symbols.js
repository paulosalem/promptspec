// PromptSpec — Document symbol provider
//
// Populates the Outline view and breadcrumbs with:
//   • @execute — strategy declaration
//   • @prompt — named prompt sections
//   • @tool — tool definitions
//   • @match / @if — control flow blocks
//   • @refine — file inclusions
//   • Markdown headings (# ## ###)

const vscode = require("vscode");

const SYMBOL_PATTERNS = [
  { re: /^\s*@execute\s+(\S+)/, kind: vscode.SymbolKind.Event, prefix: "⚡ @execute" },
  { re: /^\s*@prompt\s+(\w+)/, kind: vscode.SymbolKind.Function, prefix: "📝 @prompt" },
  { re: /^\s*@tool\s+(\S+)/, kind: vscode.SymbolKind.Method, prefix: "🔧 @tool" },
  { re: /^\s*@match\s+(\w+)/, kind: vscode.SymbolKind.Enum, prefix: "🔀 @match" },
  { re: /^\s*@if\s+(.+?)\s*$/, kind: vscode.SymbolKind.Boolean, prefix: "❓ @if" },
  { re: /^\s*@refine\s+(\S+)/, kind: vscode.SymbolKind.Module, prefix: "📎 @refine" },
  { re: /^\s*(#{1,6})\s+(.+)$/, kind: vscode.SymbolKind.String, prefix: "" },
];

class PromptSpecDocumentSymbolProvider {
  provideDocumentSymbols(document) {
    const symbols = [];

    for (let i = 0; i < document.lineCount; i++) {
      const line = document.lineAt(i);
      const text = line.text;

      for (const pat of SYMBOL_PATTERNS) {
        const m = text.match(pat.re);
        if (!m) continue;

        let name;
        if (pat.prefix === "") {
          // Markdown heading
          const level = m[1].length;
          name = `${"#".repeat(level)} ${m[2]}`;
        } else {
          name = `${pat.prefix} ${m[1]}`;
        }

        const range = line.range;
        const symbol = new vscode.DocumentSymbol(name, "", pat.kind, range, range);
        symbols.push(symbol);
        break;
      }
    }

    return symbols;
  }
}

module.exports = { PromptSpecDocumentSymbolProvider };
