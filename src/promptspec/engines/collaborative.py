"""Collaborative editing engine — wraps ellements CollaborativeEditingStrategy."""

from __future__ import annotations

from typing import Optional

from ellements.patterns import CollaborativeEditingStrategy
from ellements.patterns.callbacks import PassthroughEditCallback
from ellements.patterns.strategies import OnStepCallback

from ..controller import CompositionResult
from .base import BaseEngine, ExecutionResult, RuntimeConfig


class CollaborativeEngine(BaseEngine):
    """Human-in-the-loop collaborative editing engine.

    Requires named prompts: ``generate``, ``continue``.

    Accepts an optional ``edit_callback`` in the runtime config (or
    ``config`` block of the spec).  Defaults to
    :class:`~ellements.patterns.callbacks.PassthroughEditCallback`
    so that specs can be executed non-interactively (e.g. in tests).
    """

    STRATEGY_CLASS = CollaborativeEditingStrategy

    async def execute(
        self,
        result: CompositionResult,
        config: Optional[RuntimeConfig] = None,
        on_step: Optional[OnStepCallback] = None,
    ) -> ExecutionResult:
        self._validate_prompts(result)
        strategy = CollaborativeEditingStrategy()
        strategy_config = self._build_strategy_config(result, config, on_step)
        # Ensure a callback is present; callers may inject their own via config
        strategy_config.setdefault("edit_callback", PassthroughEditCallback())
        sr = await strategy.execute(
            result.prompts or {"default": result.composed_prompt},
            self.client,
            tools=result.tools or None,
            config=strategy_config,
        )
        return self._wrap_result(sr)
