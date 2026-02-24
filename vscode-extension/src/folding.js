// PromptSpec — Folding range provider
//
// Smart folding for:
//   • @note blocks (indent-based)
//   • @match blocks (until next same-level directive)
//   • @if / @else blocks
//   • @prompt blocks
//   • @tool blocks

const vscode = require("vscode");

class PromptSpecFoldingRangeProvider {
  provideFoldingRanges(document) {
    const ranges = [];
    const lines = [];
    for (let i = 0; i < document.lineCount; i++) {
      lines.push(document.lineAt(i).text);
    }

    // Track block-start directives and close them when a same-or-less indent directive appears
    const blockDirectives = /^\s*@(?:note|match|if|else|prompt|tool|execute)\b/;
    const stack = []; // { line, indent }

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      const nonWs = line.search(/\S/);
      if (nonWs < 0) continue; // blank line

      const isDirective = blockDirectives.test(line);
      if (isDirective) {
        const indent = nonWs;
        // Close any stack entries at same or deeper indent
        while (stack.length > 0 && stack[stack.length - 1].indent >= indent) {
          const opened = stack.pop();
          // Find last non-blank line before this one
          let end = i - 1;
          while (end > opened.line && lines[end].trim() === "") end--;
          if (end > opened.line) {
            ranges.push(new vscode.FoldingRange(opened.line, end, opened.kind));
          }
        }
        // Determine fold kind
        let kind = vscode.FoldingRangeKind.Region;
        if (/^\s*@note\b/.test(line)) {
          kind = vscode.FoldingRangeKind.Comment;
        }
        stack.push({ line: i, indent, kind });
      }
    }

    // Close remaining stack entries at end of file
    const lastLine = lines.length - 1;
    while (stack.length > 0) {
      const opened = stack.pop();
      let end = lastLine;
      while (end > opened.line && lines[end].trim() === "") end--;
      if (end > opened.line) {
        ranges.push(new vscode.FoldingRange(opened.line, end, opened.kind));
      }
    }

    return ranges;
  }
}

module.exports = { PromptSpecFoldingRangeProvider };
