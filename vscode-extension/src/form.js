// PromptSpec — Webview form panel
//
// Renders an interactive form for filling in spec variables,
// with live preview and run capabilities.

const vscode = require("vscode");
const path = require("path");
const { exec } = require("child_process");

// ── State ───────────────────────────────────────────────────────

let _panel = null;

// ── Helpers ─────────────────────────────────────────────────────

function getCliPath() {
  const config = vscode.workspace.getConfiguration("promptspec");
  return config.get("cliPath", "promptspec");
}

function getModelArg() {
  const config = vscode.workspace.getConfiguration("promptspec");
  const model = config.get("defaultModel", "").trim();
  return model ? `--model ${model}` : "";
}

function getExtraArgs() {
  const config = vscode.workspace.getConfiguration("promptspec");
  return config.get("extraArgs", "").trim();
}

/**
 * Scan a spec file using `promptspec --scan` and return parsed metadata.
 */
function scanSpec(specPath) {
  return new Promise((resolve, reject) => {
    const cli = getCliPath();
    const cmd = `${cli} "${specPath}" --scan`;
    exec(cmd, { maxBuffer: 1024 * 512 }, (err, stdout, stderr) => {
      if (err) {
        reject(new Error(stderr || err.message));
        return;
      }
      try {
        resolve(JSON.parse(stdout));
      } catch (e) {
        reject(new Error(`Failed to parse scan output: ${e.message}`));
      }
    });
  });
}

// ── Panel creation ──────────────────────────────────────────────

/**
 * Open the PromptSpec form panel for the given spec file.
 */
async function openFormPanel(uri) {
  // Resolve spec path
  let specPath;
  if (uri && uri.fsPath) {
    specPath = uri.fsPath;
  } else {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
      vscode.window.showWarningMessage("PromptSpec: No file is open.");
      return;
    }
    specPath = editor.document.fileName;
    if (!specPath.endsWith(".promptspec.md")) {
      vscode.window.showWarningMessage(
        "PromptSpec: Current file is not a .promptspec.md file."
      );
      return;
    }
    if (editor.document.isDirty) {
      await editor.document.save();
    }
  }

  // Scan the spec
  let metadata;
  try {
    metadata = await scanSpec(specPath);
  } catch (err) {
    vscode.window.showErrorMessage(
      `PromptSpec: Failed to scan spec — ${err.message}`
    );
    return;
  }

  // Create or reuse panel
  if (_panel) {
    _panel.reveal(vscode.ViewColumn.Beside);
  } else {
    _panel = vscode.window.createWebviewPanel(
      "promptspecForm",
      `⚡ ${metadata.title || "PromptSpec"}`,
      vscode.ViewColumn.Beside,
      {
        enableScripts: true,
        retainContextWhenHidden: true,
      }
    );
    _panel.onDidDispose(() => {
      _panel = null;
    });
  }

  _panel.title = `⚡ ${metadata.title || "PromptSpec"}`;
  _panel.webview.html = buildFormHtml(metadata, specPath);

  // Handle messages from webview
  _panel.webview.onDidReceiveMessage(async (msg) => {
    if (msg.command === "compose") {
      runCommand(specPath, msg.values, "");
    } else if (msg.command === "run") {
      runCommand(specPath, msg.values, "--run --verbose");
    } else if (msg.command === "openTUI") {
      runCommand(specPath, msg.values, "--ui");
    } else if (msg.command === "refresh") {
      // Re-scan and rebuild
      try {
        const newMeta = await scanSpec(specPath);
        _panel.webview.html = buildFormHtml(newMeta, specPath);
      } catch (err) {
        vscode.window.showErrorMessage(`PromptSpec: ${err.message}`);
      }
    }
  });
}

/**
 * Build CLI command from form values and send to terminal.
 */
function runCommand(specPath, values, flags) {
  const cli = getCliPath();
  const model = getModelArg();
  const extra = getExtraArgs();

  // Build --var flags from form values
  const varFlags = Object.entries(values)
    .filter(([, v]) => v !== "" && v !== null && v !== undefined)
    .map(([k, v]) => `--var ${k}="${v.replace(/"/g, '\\"')}"`)
    .join(" ");

  const parts = [cli, `"${specPath}"`, flags, varFlags, model, extra].filter(
    Boolean
  );
  const command = parts.join(" ");

  // Find or create terminal
  let terminal = vscode.window.terminals.find(
    (t) => t.name === "PromptSpec" && !t.exitStatus
  );
  if (!terminal) {
    terminal = vscode.window.createTerminal({
      name: "PromptSpec",
      iconPath: new vscode.ThemeIcon("zap"),
    });
  }
  terminal.show(false);
  terminal.sendText(command);
}

// ── HTML generation ─────────────────────────────────────────────

function buildFormHtml(metadata, specPath) {
  const title = escapeHtml(metadata.title || "Untitled Spec");
  const desc = escapeHtml(metadata.description || "");
  const filename = escapeHtml(path.basename(specPath));

  const inputsHtml = (metadata.inputs || []).map(buildInputHtml).join("\n");

  const hasExecution = metadata.execution && metadata.execution.strategy;
  const strategyBadge = hasExecution
    ? `<span class="badge strategy">${escapeHtml(metadata.execution.strategy)}</span>`
    : "";

  const toolBadges = (metadata.tool_names || [])
    .map((t) => `<span class="badge tool">🔧 ${escapeHtml(t)}</span>`)
    .join(" ");

  const promptBadges = (metadata.prompt_names || [])
    .map((p) => `<span class="badge prompt">💬 ${escapeHtml(p)}</span>`)
    .join(" ");

  return `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
  :root {
    --gold: #FFD700;
    --gold-dim: #B8960F;
    --bg: var(--vscode-editor-background);
    --fg: var(--vscode-editor-foreground);
    --input-bg: var(--vscode-input-background);
    --input-fg: var(--vscode-input-foreground);
    --input-border: var(--vscode-input-border, #444);
    --btn-bg: var(--vscode-button-background);
    --btn-fg: var(--vscode-button-foreground);
    --btn-hover: var(--vscode-button-hoverBackground);
    --focus: var(--vscode-focusBorder);
  }

  * { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    font-family: var(--vscode-font-family, system-ui, sans-serif);
    font-size: var(--vscode-font-size, 13px);
    color: var(--fg);
    background: var(--bg);
    padding: 16px 20px;
    line-height: 1.5;
  }

  /* Header */
  .header {
    border-bottom: 2px solid var(--gold);
    padding-bottom: 12px;
    margin-bottom: 20px;
  }
  .header h1 {
    font-size: 1.4em;
    color: var(--gold);
    margin-bottom: 4px;
  }
  .header .filename {
    font-size: 0.85em;
    opacity: 0.6;
  }
  .header .desc {
    margin-top: 6px;
    opacity: 0.8;
  }
  .badges {
    margin-top: 8px;
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
  }
  .badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 10px;
    font-size: 0.8em;
    font-weight: 600;
  }
  .badge.strategy { background: rgba(255, 165, 0, 0.2); color: #FFA500; }
  .badge.tool { background: rgba(0, 206, 209, 0.15); color: #00CED1; }
  .badge.prompt { background: rgba(0, 191, 255, 0.15); color: #00BFFF; }

  /* Form */
  .form-section {
    margin-bottom: 24px;
  }
  .form-section h2 {
    font-size: 1.05em;
    color: var(--gold-dim);
    margin-bottom: 12px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .field {
    margin-bottom: 16px;
  }
  .field label {
    display: block;
    margin-bottom: 4px;
    font-weight: 600;
  }
  .field label .directive-tag {
    font-weight: normal;
    font-size: 0.85em;
    opacity: 0.5;
    margin-left: 6px;
  }
  .field .hint {
    font-size: 0.85em;
    opacity: 0.6;
    margin-bottom: 4px;
  }

  input[type="text"],
  textarea,
  select {
    width: 100%;
    padding: 6px 10px;
    background: var(--input-bg);
    color: var(--input-fg);
    border: 1px solid var(--input-border);
    border-radius: 4px;
    font-family: inherit;
    font-size: inherit;
    outline: none;
  }
  input:focus, textarea:focus, select:focus {
    border-color: var(--focus);
  }
  textarea {
    min-height: 80px;
    resize: vertical;
  }
  select {
    cursor: pointer;
  }

  /* Toggle switch for booleans */
  .toggle-row {
    display: flex;
    align-items: center;
    gap: 10px;
  }
  .toggle {
    position: relative;
    width: 40px;
    height: 22px;
    cursor: pointer;
  }
  .toggle input {
    opacity: 0;
    width: 0;
    height: 0;
  }
  .toggle .slider {
    position: absolute;
    inset: 0;
    background: var(--input-border);
    border-radius: 11px;
    transition: background 0.2s;
  }
  .toggle .slider::before {
    content: "";
    position: absolute;
    width: 16px;
    height: 16px;
    left: 3px;
    top: 3px;
    background: white;
    border-radius: 50%;
    transition: transform 0.2s;
  }
  .toggle input:checked + .slider {
    background: var(--gold);
  }
  .toggle input:checked + .slider::before {
    transform: translateX(18px);
  }

  /* Buttons */
  .actions {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
    padding-top: 16px;
    border-top: 1px solid var(--input-border);
  }
  button {
    padding: 8px 18px;
    border: none;
    border-radius: 4px;
    font-family: inherit;
    font-size: inherit;
    font-weight: 600;
    cursor: pointer;
    transition: opacity 0.15s;
  }
  button:hover { opacity: 0.85; }
  button:active { opacity: 0.7; }

  .btn-compose {
    background: var(--btn-bg);
    color: var(--btn-fg);
  }
  .btn-run {
    background: var(--gold);
    color: #1a1a1a;
  }
  .btn-tui {
    background: rgba(0, 191, 255, 0.2);
    color: #00BFFF;
    border: 1px solid rgba(0, 191, 255, 0.4);
  }
  .btn-refresh {
    margin-left: auto;
    background: transparent;
    color: var(--fg);
    opacity: 0.6;
    border: 1px solid var(--input-border);
  }

  /* Empty state */
  .empty {
    text-align: center;
    padding: 40px 20px;
    opacity: 0.5;
  }
  .empty .icon { font-size: 2em; margin-bottom: 8px; }
</style>
</head>
<body>

<div class="header">
  <h1>⚡ ${title}</h1>
  <div class="filename">${filename}</div>
  ${desc ? `<div class="desc">${desc}</div>` : ""}
  <div class="badges">
    ${strategyBadge}
    ${toolBadges}
    ${promptBadges}
  </div>
</div>

${
  (metadata.inputs || []).length === 0
    ? `<div class="empty">
        <div class="icon">✨</div>
        <p>This spec has no variables to fill in.<br>You can run it directly.</p>
      </div>`
    : `<div class="form-section">
        <h2>Variables</h2>
        ${inputsHtml}
      </div>`
}

<div class="actions">
  <button class="btn-compose" onclick="doCompose()" title="Compile the spec">▶ Compose</button>
  <button class="btn-run" onclick="doRun()" title="Compile and execute via LLM">🚀 Run</button>
  <button class="btn-tui" onclick="doTUI()" title="Open in interactive TUI">🖥 TUI</button>
  <button class="btn-refresh" onclick="doRefresh()" title="Re-scan the spec file">↻ Refresh</button>
</div>

<script>
  const vscode = acquireVsCodeApi();

  function getValues() {
    const values = {};
    document.querySelectorAll('[data-field]').forEach(el => {
      const name = el.dataset.field;
      if (el.type === 'checkbox') {
        values[name] = el.checked ? 'true' : 'false';
      } else {
        values[name] = el.value;
      }
    });
    return values;
  }

  function doCompose() {
    vscode.postMessage({ command: 'compose', values: getValues() });
  }
  function doRun() {
    vscode.postMessage({ command: 'run', values: getValues() });
  }
  function doTUI() {
    vscode.postMessage({ command: 'openTUI', values: getValues() });
  }
  function doRefresh() {
    vscode.postMessage({ command: 'refresh' });
  }
</script>

</body>
</html>`;
}

function buildInputHtml(input) {
  const name = escapeHtml(input.name);
  const label = escapeHtml(formatLabel(input.name));
  const directive = input.source_directive
    ? `<span class="directive-tag">(${escapeHtml(input.source_directive)})</span>`
    : "";
  const hint = input.description
    ? `<div class="hint">${escapeHtml(input.description)}</div>`
    : "";
  const defaultVal = input.default || "";

  switch (input.input_type) {
    case "select": {
      const opts = (input.options || [])
        .map(
          (o) =>
            `<option value="${escapeHtml(o)}"${
              o === defaultVal ? " selected" : ""
            }>${escapeHtml(o)}</option>`
        )
        .join("\n");
      return `<div class="field">
        <label>${label} ${directive}</label>
        ${hint}
        <select data-field="${name}">
          <option value="">— select —</option>
          ${opts}
        </select>
      </div>`;
    }

    case "boolean":
      return `<div class="field">
        <label>${label} ${directive}</label>
        ${hint}
        <div class="toggle-row">
          <label class="toggle">
            <input type="checkbox" data-field="${name}" ${
        defaultVal === "true" ? "checked" : ""
      }>
            <span class="slider"></span>
          </label>
          <span class="toggle-label">${
            defaultVal === "true" ? "Enabled" : "Disabled"
          }</span>
        </div>
      </div>`;

    case "multiline":
      return `<div class="field">
        <label>${label} ${directive}</label>
        ${hint}
        <textarea data-field="${name}" placeholder="Enter ${label.toLowerCase()}…" rows="4">${escapeHtml(
        defaultVal
      )}</textarea>
      </div>`;

    case "file":
      return `<div class="field">
        <label>${label} ${directive}</label>
        ${hint}
        <input type="text" data-field="${name}" placeholder="${
        input.file_hint || "Path to file…"
      }" value="${escapeHtml(defaultVal)}">
      </div>`;

    default:
      // text
      return `<div class="field">
        <label>${label} ${directive}</label>
        ${hint}
        <input type="text" data-field="${name}" placeholder="Enter ${label.toLowerCase()}…" value="${escapeHtml(
        defaultVal
      )}">
      </div>`;
  }
}

function formatLabel(name) {
  return name
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

// ── Registration ────────────────────────────────────────────────

function registerFormPanel(context) {
  context.subscriptions.push(
    vscode.commands.registerCommand("promptspec.fillForm", openFormPanel)
  );
}

module.exports = { registerFormPanel };
