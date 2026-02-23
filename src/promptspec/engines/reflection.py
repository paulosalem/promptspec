"""Reflection engine — wraps ellements ReflectionStrategy."""

from __future__ import annotations

from typing import Optional

from ellements.patterns import ReflectionStrategy

from ..controller import CompositionResult
from .base import BaseEngine, ExecutionResult, RuntimeConfig


class ReflectionEngine(BaseEngine):
    """Generate → critique → revise loop engine."""

    async def execute(
        self,
        result: CompositionResult,
        config: Optional[RuntimeConfig] = None,
    ) -> ExecutionResult:
        strategy = ReflectionStrategy()
        sr = await strategy.execute(
            result.prompts or {"default": result.composed_prompt},
            self.client,
            tools=result.tools or None,
            config=self._build_strategy_config(result, config),
        )
        return self._wrap_result(sr)
