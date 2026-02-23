"""Single-call engine — wraps ellements SingleCallStrategy."""

from __future__ import annotations

from typing import Optional

from ellements.patterns import SingleCallStrategy
from ellements.patterns.strategies import OnStepCallback

from ..controller import CompositionResult
from .base import BaseEngine, ExecutionResult, RuntimeConfig


class SingleCallEngine(BaseEngine):
    """Default engine: one LLM call with the default prompt."""

    async def execute(
        self,
        result: CompositionResult,
        config: Optional[RuntimeConfig] = None,
        on_step: Optional[OnStepCallback] = None,
    ) -> ExecutionResult:
        strategy = SingleCallStrategy()
        sr = await strategy.execute(
            result.prompts or {"default": result.composed_prompt},
            self.client,
            tools=result.tools or None,
            config=self._build_strategy_config(result, config, on_step),
        )
        return self._wrap_result(sr)
