"""Engine registry — resolve engine names to instances."""

from __future__ import annotations

import importlib
from typing import Dict, Optional, Type

from .base import BaseEngine, Engine


BUILTIN_ENGINES: Dict[str, Type[BaseEngine]] = {}


def _lazy_load_builtins() -> None:
    """Lazily populate the built-in registry on first use."""
    if BUILTIN_ENGINES:
        return
    from .single_call import SingleCallEngine
    from .self_consistency import SelfConsistencyEngine
    from .tree_of_thought import TreeOfThoughtEngine
    from .reflection import ReflectionEngine

    BUILTIN_ENGINES.update({
        "single-call": SingleCallEngine,
        "self-consistency": SelfConsistencyEngine,
        "tree-of-thought": TreeOfThoughtEngine,
        "reflection": ReflectionEngine,
    })


def resolve_engine(name_or_path: str) -> Engine:
    """Resolve an engine by built-in name or dotted Python import path.

    Args:
        name_or_path: Either a built-in name (``"single-call"``,
            ``"self-consistency"``, ``"tree-of-thought"``, ``"reflection"``)
            or a fully-qualified Python class path
            (e.g. ``"my_package.engines.CustomEngine"``).

    Returns:
        An instantiated :class:`Engine`.

    Raises:
        ValueError: If the name cannot be resolved.
    """
    _lazy_load_builtins()

    if name_or_path in BUILTIN_ENGINES:
        return BUILTIN_ENGINES[name_or_path]()

    # Try importing as a dotted path
    try:
        module_path, class_name = name_or_path.rsplit(".", 1)
        module = importlib.import_module(module_path)
        engine_cls = getattr(module, class_name)
        return engine_cls()
    except (ValueError, ImportError, AttributeError) as exc:
        available = ", ".join(sorted(BUILTIN_ENGINES.keys()))
        raise ValueError(
            f"Unknown engine '{name_or_path}'. "
            f"Built-in engines: {available}. "
            f"Or provide a dotted Python import path."
        ) from exc
