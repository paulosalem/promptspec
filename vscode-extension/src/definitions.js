// PromptSpec — Definition provider
//
// Ctrl+Click / F12 on @refine file paths → opens the referenced file

const vscode = require("vscode");
const path = require("path");
const fs = require("fs");

class PromptSpecDefinitionProvider {
  provideDefinition(document, position) {
    const line = document.lineAt(position).text;
    const refineMatch = line.match(/^\s*@refine\s+(\S+)/);
    if (!refineMatch) return undefined;

    const filePath = refineMatch[1];
    const fileStart = line.indexOf(filePath);
    const fileEnd = fileStart + filePath.length;

    // Only trigger if cursor is on the file path
    if (position.character < fileStart || position.character > fileEnd) {
      return undefined;
    }

    const docDir = path.dirname(document.uri.fsPath);
    const absPath = path.resolve(docDir, filePath);

    if (!fs.existsSync(absPath)) return undefined;

    return new vscode.Location(vscode.Uri.file(absPath), new vscode.Position(0, 0));
  }
}

module.exports = { PromptSpecDefinitionProvider };
