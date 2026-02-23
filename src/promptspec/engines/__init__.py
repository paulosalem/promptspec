"""PromptSpec execution engines.

Thin wrappers that delegate to ellements strategies, wiring
CompilationResult → ellements strategy → ExecutionResult.
"""

from .base import BaseEngine, Engine, ExecutionResult, PromptConfig, RuntimeConfig
from .registry import resolve_engine
from .reflection import ReflectionEngine
from .self_consistency import SelfConsistencyEngine
from .single_call import SingleCallEngine
from .tree_of_thought import TreeOfThoughtEngine

__all__ = [
    "BaseEngine",
    "Engine",
    "ExecutionResult",
    "PromptConfig",
    "ReflectionEngine",
    "RuntimeConfig",
    "SelfConsistencyEngine",
    "SingleCallEngine",
    "TreeOfThoughtEngine",
    "resolve_engine",
]
