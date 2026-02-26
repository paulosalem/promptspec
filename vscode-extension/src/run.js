// PromptSpec — Run commands
//
// Opens a VS Code integrated terminal and runs promptspec CLI commands.
// Supports: Compose, Run, TUI, and Discover modes.

const vscode = require("vscode");
const path = require("path");
const fs = require("fs");

// ── Helpers ─────────────────────────────────────────────────────

/**
 * Get or create a reusable "PromptSpec" terminal.
 * If the previous terminal was closed, creates a new one.
 */
let _terminal = null;

function getTerminal() {
  // Check if our terminal is still alive
  if (_terminal && !_terminal.exitStatus) {
    return _terminal;
  }
  _terminal = vscode.window.createTerminal({
    name: "PromptSpec",
    iconPath: new vscode.ThemeIcon("zap"),
  });
  return _terminal;
}

/**
 * Get the CLI path from settings.
 */
function getCliPath() {
  const config = vscode.workspace.getConfiguration("promptspec");
  return config.get("cliPath", "promptspec");
}

/**
 * Get extra CLI arguments from settings.
 */
function getExtraArgs() {
  const config = vscode.workspace.getConfiguration("promptspec");
  return config.get("extraArgs", "").trim();
}

/**
 * Get the default model override from settings (if set).
 */
function getModelArg() {
  const config = vscode.workspace.getConfiguration("promptspec");
  const model = config.get("defaultModel", "").trim();
  return model ? `--model ${model}` : "";
}

/**
 * Resolve the spec file path from the active editor or a URI argument.
 * Returns null (with user warning) if no valid spec is available.
 */
function resolveSpecFile(uri) {
  // If called from explorer context menu, uri is provided
  if (uri && uri.fsPath) {
    return uri.fsPath;
  }

  const editor = vscode.window.activeTextEditor;
  if (!editor) {
    vscode.window.showWarningMessage("PromptSpec: No file is open.");
    return null;
  }

  const filePath = editor.document.fileName;
  if (!filePath.endsWith(".promptspec.md")) {
    vscode.window.showWarningMessage(
      "PromptSpec: Current file is not a .promptspec.md file."
    );
    return null;
  }

  // Prompt to save if dirty
  if (editor.document.isDirty) {
    editor.document.save();
  }

  return filePath;
}

/**
 * Look for matching vars files for a given spec.
 * Searches for vars/<stem>.json and vars/<stem>-*.json in the same directory.
 */
async function findVarsFiles(specPath) {
  const dir = path.dirname(specPath);
  const basename = path.basename(specPath);
  // Strip .promptspec.md to get the stem
  const stem = basename.replace(/\.promptspec\.md$/, "");

  const varsDir = path.join(dir, "vars");
  if (!fs.existsSync(varsDir)) {
    return [];
  }

  try {
    const files = fs.readdirSync(varsDir);
    return files
      .filter((f) => {
        const lower = f.toLowerCase();
        return (
          lower.endsWith(".json") &&
          (lower === `${stem.toLowerCase()}.json` ||
            lower.startsWith(`${stem.toLowerCase()}-`))
        );
      })
      .map((f) => path.join(varsDir, f));
  } catch {
    return [];
  }
}

/**
 * If vars files exist for the spec, prompt the user to pick one (or skip).
 * Returns the --vars-file flag string, or empty string.
 */
async function resolveVarsFlag(specPath) {
  const varsFiles = await findVarsFiles(specPath);
  if (varsFiles.length === 0) {
    return "";
  }

  if (varsFiles.length === 1) {
    const name = path.basename(varsFiles[0]);
    const pick = await vscode.window.showQuickPick(
      [`Use ${name}`, "Skip (no vars file)"],
      { placeHolder: `Found vars file: ${name}` }
    );
    if (pick && pick.startsWith("Use")) {
      return `--vars-file "${varsFiles[0]}"`;
    }
    return "";
  }

  // Multiple vars files — let user pick
  const items = [
    ...varsFiles.map((f) => path.basename(f)),
    "Skip (no vars file)",
  ];
  const pick = await vscode.window.showQuickPick(items, {
    placeHolder: "Multiple vars files found — pick one or skip",
  });
  if (pick && pick !== "Skip (no vars file)") {
    const chosen = varsFiles.find((f) => path.basename(f) === pick);
    if (chosen) {
      return `--vars-file "${chosen}"`;
    }
  }
  return "";
}

/**
 * Build the full CLI command string.
 */
function buildCommand(specPath, flags) {
  const cli = getCliPath();
  const model = getModelArg();
  const extra = getExtraArgs();
  const parts = [cli, `"${specPath}"`, flags, model, extra].filter(Boolean);
  return parts.join(" ");
}

/**
 * Send a command to the PromptSpec terminal.
 */
function runInTerminal(command) {
  const terminal = getTerminal();
  terminal.show(/* preserveFocus */ false);
  terminal.sendText(command);
}

// ── Command handlers ────────────────────────────────────────────

/**
 * PromptSpec: Compose — compile the spec to stdout.
 */
async function compose(uri) {
  const specPath = resolveSpecFile(uri);
  if (!specPath) return;

  const varsFlag = await resolveVarsFlag(specPath);
  const command = buildCommand(specPath, varsFlag);
  runInTerminal(command);
}

/**
 * PromptSpec: Run — compile and execute via LLM.
 */
async function run(uri) {
  const specPath = resolveSpecFile(uri);
  if (!specPath) return;

  const varsFlag = await resolveVarsFlag(specPath);
  const command = buildCommand(specPath, `--run --verbose ${varsFlag}`);
  runInTerminal(command);
}

/**
 * PromptSpec: Open in TUI — launch the interactive TUI.
 */
async function openTUI(uri) {
  const specPath = resolveSpecFile(uri);
  if (!specPath) return;

  const varsFlag = await resolveVarsFlag(specPath);
  const command = buildCommand(specPath, `--ui ${varsFlag}`);
  runInTerminal(command);
}

/**
 * PromptSpec: Discover — launch spec discovery chat.
 * This doesn't need a spec file.
 */
function discover() {
  const cli = getCliPath();
  const model = getModelArg();
  const extra = getExtraArgs();
  const parts = [cli, "--discover", model, extra].filter(Boolean);
  runInTerminal(parts.join(" "));
}

// ── Registration ────────────────────────────────────────────────

/**
 * Register all run commands. Called from extension.js activate().
 */
function registerRunCommands(context) {
  context.subscriptions.push(
    vscode.commands.registerCommand("promptspec.compose", compose),
    vscode.commands.registerCommand("promptspec.run", run),
    vscode.commands.registerCommand("promptspec.openTUI", openTUI),
    vscode.commands.registerCommand("promptspec.discover", discover)
  );

  // Clean up terminal reference when it closes
  context.subscriptions.push(
    vscode.window.onDidCloseTerminal((t) => {
      if (t === _terminal) {
        _terminal = null;
      }
    })
  );
}

module.exports = { registerRunCommands };
