"""Tree-of-thought engines — wraps ellements ToT strategies.

Provides two engines:
  ``TreeOfThoughtEngine``           — Full BFS/DFS tree search (canonical Yao et al.)
  ``SimplifiedTreeOfThoughtEngine`` — Generate → evaluate → synthesize (simplified)
"""

from __future__ import annotations

from typing import Optional

from ellements.patterns import TreeOfThoughtStrategy, SimplifiedTreeOfThoughtStrategy
from ellements.patterns.strategies import OnStepCallback

from ..controller import CompositionResult
from .base import BaseEngine, ExecutionResult, RuntimeConfig


class TreeOfThoughtEngine(BaseEngine):
    """Full BFS/DFS tree search engine (canonical Yao et al. 2023)."""

    STRATEGY_CLASS = TreeOfThoughtStrategy

    async def execute(
        self,
        result: CompositionResult,
        config: Optional[RuntimeConfig] = None,
        on_step: Optional[OnStepCallback] = None,
    ) -> ExecutionResult:
        self._validate_prompts(result)
        strategy = TreeOfThoughtStrategy()
        sr = await strategy.execute(
            result.prompts or {"default": result.composed_prompt},
            self.client,
            tools=result.tools or None,
            config=self._build_strategy_config(result, config, on_step),
        )
        return self._wrap_result(sr)


class SimplifiedTreeOfThoughtEngine(BaseEngine):
    """Simplified generate → evaluate → synthesize engine."""

    STRATEGY_CLASS = SimplifiedTreeOfThoughtStrategy

    async def execute(
        self,
        result: CompositionResult,
        config: Optional[RuntimeConfig] = None,
        on_step: Optional[OnStepCallback] = None,
    ) -> ExecutionResult:
        self._validate_prompts(result)
        strategy = SimplifiedTreeOfThoughtStrategy()
        sr = await strategy.execute(
            result.prompts or {"default": result.composed_prompt},
            self.client,
            tools=result.tools or None,
            config=self._build_strategy_config(result, config, on_step),
        )
        return self._wrap_result(sr)
