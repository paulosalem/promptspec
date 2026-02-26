"""Two-tier configuration system for PromptSpec.

Resolution order (later overrides earlier):
  1. Built-in defaults
  2. Global user config:  ~/.promptspec/config.json
  3. Project config:      .promptspec.config.json (searched cwd → parents)
  4. CLI flags (--specs-dir, --model, etc.)
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


GLOBAL_DIR = Path.home() / ".promptspec"
GLOBAL_CONFIG = GLOBAL_DIR / "config.json"
PROJECT_CONFIG_NAME = ".promptspec.config.json"


@dataclass
class PromptSpecEnvConfig:
    """Resolved configuration for PromptSpec."""

    specs_dirs: List[Path] = field(default_factory=list)
    default_model: str = "gpt-4.1"

    # Provenance tracking (which files contributed)
    _global_path: Optional[Path] = field(default=None, repr=False)
    _project_path: Optional[Path] = field(default=None, repr=False)

    def effective_specs_dirs(self, cwd: Optional[Path] = None) -> List[Path]:
        """Return specs dirs with the default ./specs/ prepended if cwd has one."""
        dirs = list(self.specs_dirs)
        if cwd is None:
            cwd = Path.cwd()
        default_specs = cwd / "specs"
        if default_specs.is_dir() and default_specs not in dirs:
            dirs.insert(0, default_specs)
        return dirs


def _find_project_config(start: Optional[Path] = None) -> Optional[Path]:
    """Walk from *start* up to the filesystem root looking for project config."""
    current = (start or Path.cwd()).resolve()
    for _ in range(50):  # safety limit
        candidate = current / PROJECT_CONFIG_NAME
        if candidate.is_file():
            return candidate
        parent = current.parent
        if parent == current:
            break
        current = parent
    return None


def _load_json(path: Path) -> Dict[str, Any]:
    """Load a JSON file, returning {} on any error."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _apply_dict(config: PromptSpecEnvConfig, data: Dict[str, Any], base_dir: Path) -> None:
    """Merge a raw JSON dict into a config object."""
    if "specs_dirs" in data:
        raw = data["specs_dirs"]
        if isinstance(raw, list):
            for d in raw:
                p = Path(d).expanduser()
                if not p.is_absolute():
                    p = (base_dir / p).resolve()
                if p not in config.specs_dirs:
                    config.specs_dirs.append(p)
    if "default_model" in data:
        config.default_model = str(data["default_model"])


def load_config(
    project_dir: Optional[Path] = None,
    extra_specs_dirs: Optional[List[Path]] = None,
) -> PromptSpecEnvConfig:
    """Load and merge the two-tier configuration.

    Parameters
    ----------
    project_dir : Path, optional
        Starting directory for project config search (defaults to cwd).
    extra_specs_dirs : list of Path, optional
        Additional --specs-dir values from CLI flags.
    """
    config = PromptSpecEnvConfig()

    # 1. Global
    if GLOBAL_CONFIG.is_file():
        data = _load_json(GLOBAL_CONFIG)
        _apply_dict(config, data, GLOBAL_DIR)
        config._global_path = GLOBAL_CONFIG

    # 2. Project (overrides global)
    proj = _find_project_config(project_dir)
    if proj:
        data = _load_json(proj)
        _apply_dict(config, data, proj.parent)
        config._project_path = proj

    # 3. CLI extras
    if extra_specs_dirs:
        for d in extra_specs_dirs:
            p = d.expanduser().resolve()
            if p not in config.specs_dirs:
                config.specs_dirs.append(p)

    return config


def print_env(config: PromptSpecEnvConfig, cwd: Optional[Path] = None) -> str:
    """Return a formatted string describing the resolved environment."""
    if cwd is None:
        cwd = Path.cwd()
    lines = []
    lines.append("PromptSpec Environment")
    lines.append("=" * 50)
    lines.append("")
    lines.append(f"  Global config:   {config._global_path or '(not found)'}")
    lines.append(f"  Project config:  {config._project_path or '(not found)'}")
    lines.append(f"  Default model:   {config.default_model}")
    lines.append(f"  Cache dir:       {GLOBAL_DIR}")
    lines.append("")
    lines.append("  Spec directories:")
    for d in config.effective_specs_dirs(cwd):
        exists = "✓" if d.is_dir() else "✗"
        lines.append(f"    {exists} {d}")
    if not config.effective_specs_dirs(cwd):
        lines.append("    (none)")
    lines.append("")
    return "\n".join(lines)
