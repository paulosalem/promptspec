"""Self-consistency engine — wraps ellements SelfConsistencyStrategy."""

from __future__ import annotations

from typing import Optional

from ellements.patterns import SelfConsistencyStrategy

from ..controller import CompositionResult
from .base import BaseEngine, ExecutionResult, RuntimeConfig


class SelfConsistencyEngine(BaseEngine):
    """Run prompt N times and aggregate via voting or LLM judge."""

    async def execute(
        self,
        result: CompositionResult,
        config: Optional[RuntimeConfig] = None,
    ) -> ExecutionResult:
        strategy = SelfConsistencyStrategy()
        sr = await strategy.execute(
            result.prompts or {"default": result.composed_prompt},
            self.client,
            tools=result.tools or None,
            config=self._build_strategy_config(result, config),
        )
        return self._wrap_result(sr)
