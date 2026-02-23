"""Engine protocol, base class, and runtime configuration."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

from ellements.core import LLMClient
from ellements.patterns.strategies import OnStepCallback, StepRecord, StrategyResult

from ..controller import CompositionResult


@dataclass
class PromptConfig:
    """Per-prompt runtime configuration."""

    model: Optional[str] = None
    temperature: Optional[float] = None


@dataclass
class RuntimeConfig:
    """Runtime configuration loaded from a .promptspec.yaml file."""

    engine: str = "single-call"
    engine_config: Dict[str, Any] = field(default_factory=dict)
    prompts: Dict[str, PromptConfig] = field(default_factory=dict)
    variables: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_yaml(cls, path: Path) -> "RuntimeConfig":
        """Load config from a YAML file."""
        try:
            import yaml
        except ImportError:
            raise ImportError(
                "PyYAML is required for .promptspec.yaml config files. "
                "Install it with: pip install pyyaml"
            )
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return cls()

        prompt_configs = {}
        for name, cfg in data.get("prompts", {}).items():
            if isinstance(cfg, dict):
                prompt_configs[name] = PromptConfig(
                    model=cfg.get("model"),
                    temperature=cfg.get("temperature"),
                )

        return cls(
            engine=data.get("engine", "single-call"),
            engine_config=data.get("engine_config", {}),
            prompts=prompt_configs,
            variables=data.get("variables", {}),
        )

    @classmethod
    def from_json(cls, path: Path) -> "RuntimeConfig":
        """Load config from a JSON file."""
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return cls()

        prompt_configs = {}
        for name, cfg in data.get("prompts", {}).items():
            if isinstance(cfg, dict):
                prompt_configs[name] = PromptConfig(
                    model=cfg.get("model"),
                    temperature=cfg.get("temperature"),
                )

        return cls(
            engine=data.get("engine", "single-call"),
            engine_config=data.get("engine_config", {}),
            prompts=prompt_configs,
            variables=data.get("variables", {}),
        )


@dataclass
class ExecutionResult:
    """Result of executing a compiled spec via an engine."""

    output: str
    steps: List[StepRecord] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class Engine(Protocol):
    """Protocol for execution engines.

    Any object with an ``execute`` method matching this signature works.
    No inheritance required — duck typing is sufficient.
    """

    async def execute(
        self,
        result: CompositionResult,
        config: Optional[RuntimeConfig] = None,
        on_step: Optional[OnStepCallback] = None,
    ) -> ExecutionResult: ...


class BaseEngine:
    """Convenience base class for engines that delegate to ellements strategies."""

    # Subclasses should set this to the strategy class they wrap.
    STRATEGY_CLASS: Optional[type] = None

    def __init__(self, client: Optional[LLMClient] = None) -> None:
        self.client = client or LLMClient()

    def _validate_prompts(self, result: CompositionResult) -> None:
        """Check that the spec provides all prompts required by the strategy.

        Raises ValueError with a clear message listing missing prompts.
        """
        if self.STRATEGY_CLASS is None:
            return
        required = getattr(self.STRATEGY_CLASS, "REQUIRED_PROMPTS", None)
        if not required:
            return

        available = set(result.prompts.keys()) if result.prompts else {"default"}
        # "default" is always available from composed_prompt
        if result.composed_prompt:
            available.add("default")

        missing = [p for p in required if p not in available]
        if missing:
            strategy_name = self.STRATEGY_CLASS.__name__
            raise ValueError(
                f"{strategy_name} requires @prompt directives: "
                f"{', '.join(required)}. "
                f"Missing: {', '.join(missing)}. "
                f"Available: {', '.join(sorted(available))}."
            )

    def _build_strategy_config(
        self,
        result: CompositionResult,
        config: Optional[RuntimeConfig] = None,
        on_step: Optional[OnStepCallback] = None,
    ) -> Dict[str, Any]:
        """Merge execution metadata from the spec with runtime config."""
        strategy_config: Dict[str, Any] = {}
        # Start with spec-level @execute config
        if result.execution:
            strategy_config.update(
                {k: v for k, v in result.execution.items() if k != "type"}
            )
        # Override with runtime engine_config
        if config and config.engine_config:
            strategy_config.update(config.engine_config)
        # Inject on_step callback
        if on_step:
            strategy_config["on_step"] = on_step
        return strategy_config

    def _wrap_result(self, sr: StrategyResult) -> ExecutionResult:
        """Convert an ellements StrategyResult to an ExecutionResult."""
        return ExecutionResult(
            output=sr.output,
            steps=sr.steps,
            metadata=sr.metadata,
        )
