"""PromptSpec execution engines.

Thin wrappers that delegate to ellements strategies, wiring
CompilationResult → ellements strategy → ExecutionResult.
"""

from .base import BaseEngine, Engine, ExecutionResult, PromptConfig, RuntimeConfig
from .collaborative import CollaborativeEngine
from .registry import resolve_engine
from .reflection import ReflectionEngine
from .self_consistency import SelfConsistencyEngine
from .single_call import SingleCallEngine
from .tree_of_thought import TreeOfThoughtEngine, SimplifiedTreeOfThoughtEngine

__all__ = [
    "BaseEngine",
    "CollaborativeEngine",
    "Engine",
    "ExecutionResult",
    "PromptConfig",
    "ReflectionEngine",
    "RuntimeConfig",
    "SelfConsistencyEngine",
    "SimplifiedTreeOfThoughtEngine",
    "SingleCallEngine",
    "TreeOfThoughtEngine",
    "resolve_engine",
]
