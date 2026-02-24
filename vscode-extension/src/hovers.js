// PromptSpec — Hover provider
//
// Shows documentation when hovering over:
//   • @directive names
//   • {{variable}} references
//   • ==> match arrows
//   • @execute strategy names

const vscode = require("vscode");
const { DIRECTIVES, DEBUG_DIRECTIVES, EXECUTION_STRATEGIES } = require("./directives");

class PromptSpecHoverProvider {
  provideHover(document, position) {
    const line = document.lineAt(position).text;
    const range = document.getWordRangeAtPosition(position, /@\w+\??/);

    // 1. Hover over @directive
    if (range) {
      const word = document.getText(range).replace("@", "");
      const info = DIRECTIVES[word] || DEBUG_DIRECTIVES[word];
      if (info) {
        const md = new vscode.MarkdownString();
        md.appendMarkdown(`### ${info.label}\n\n`);
        if (info.category) {
          md.appendMarkdown(`*Category: ${info.category}*\n\n`);
        }
        md.appendMarkdown(info.documentation);
        return new vscode.Hover(md, range);
      }
    }

    // 2. Hover over {{variable}}
    const varRange = document.getWordRangeAtPosition(position, /\{\{\w+\}\}/);
    if (varRange) {
      const varText = document.getText(varRange);
      const varName = varText.replace(/[{}]/g, "");
      const usages = this._countUsages(document, varName);
      const md = new vscode.MarkdownString();
      md.appendMarkdown(`### Variable: \`{{${varName}}}\`\n\n`);
      md.appendMarkdown(`Template variable replaced at composition time with values from a vars file or CLI arguments.\n\n`);
      md.appendMarkdown(`**Usages in this file:** ${usages}\n\n`);
      md.appendMarkdown(`*Provide values via:*\n`);
      md.appendMarkdown(`- \`promptspec compose spec.promptspec.md --vars vars.json\`\n`);
      md.appendMarkdown(`- Inline: \`promptspec compose spec.promptspec.md ${varName}="value"\`\n`);
      return new vscode.Hover(md, varRange);
    }

    // 3. Hover over @{variable}
    const bracedVarRange = document.getWordRangeAtPosition(position, /@\{\w+\}/);
    if (bracedVarRange) {
      const varText = document.getText(bracedVarRange);
      const varName = varText.replace(/[@{}]/g, "");
      const md = new vscode.MarkdownString();
      md.appendMarkdown(`### Variable: \`@{${varName}}\`\n\n`);
      md.appendMarkdown(`Inline variable syntax. Equivalent to \`{{${varName}}}\`.\n`);
      return new vscode.Hover(md, bracedVarRange);
    }

    // 4. Hover over ==> (match arrow)
    const arrowRange = document.getWordRangeAtPosition(position, /==>/);
    if (arrowRange) {
      const md = new vscode.MarkdownString();
      md.appendMarkdown("### Match Case Arrow `==>`\n\n");
      md.appendMarkdown('Separates a match pattern from its content in a `@match` block.\n\n');
      md.appendMarkdown('- `"value" ==>` matches a specific string\n');
      md.appendMarkdown('- `_ ==>` is the default/fallback case\n');
      return new vscode.Hover(md, arrowRange);
    }

    // 5. Hover over execution strategy name (after @execute)
    const execMatch = line.match(/^\s*@execute\s+(\S+)/);
    if (execMatch) {
      const strategyName = execMatch[1];
      const strategyStart = line.indexOf(strategyName);
      const strategyEnd = strategyStart + strategyName.length;
      const strategyRange = new vscode.Range(position.line, strategyStart, position.line, strategyEnd);
      if (strategyRange.contains(position) && EXECUTION_STRATEGIES.includes(strategyName)) {
        const descriptions = {
          "single-call": "Sends the prompt in a single LLM call. Simplest and fastest strategy.",
          "self-consistency": "Generates multiple independent samples and picks the most common answer via majority voting. Improves reliability for reasoning tasks.",
          "tree-of-thought": "Multi-step: Generate candidate approaches → Evaluate each → Synthesise the best. Requires `@prompt generate`, `@prompt evaluate`, and `@prompt synthesize` sections.",
          "reflection": "Generate an initial response → Critique it → Revise based on the critique. Requires `@prompt generate`, `@prompt critique`, and `@prompt revise` sections.",
        };
        const md = new vscode.MarkdownString();
        md.appendMarkdown(`### Strategy: \`${strategyName}\`\n\n`);
        md.appendMarkdown(descriptions[strategyName] || "");
        return new vscode.Hover(md, strategyRange);
      }
    }

    // 6. Hover over @@ escaped directive
    const escapedRange = document.getWordRangeAtPosition(position, /@@\w+/);
    if (escapedRange) {
      const md = new vscode.MarkdownString();
      md.appendMarkdown("### Escaped Directive\n\n");
      md.appendMarkdown("`@@` outputs a literal `@` character. The directive is **not** processed.\n");
      return new vscode.Hover(md, escapedRange);
    }

    return undefined;
  }

  _countUsages(document, varName) {
    const text = document.getText();
    const re = new RegExp(`\\{\\{${varName}\\}\\}|@\\{${varName}\\}|@${varName}\\b`, "g");
    let count = 0;
    while (re.exec(text)) count++;
    return count;
  }
}

module.exports = { PromptSpecHoverProvider };
