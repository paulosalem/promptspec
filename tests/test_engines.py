"""Tests for PromptSpec engines, @prompt/@execute parsing, and the run flow.

Unit tests (no LLM required) verify:
- parse_composition_xml handles <prompts> and <execution> tags
- Engine protocol and registry
- RuntimeConfig loading
- Engine wrappers delegate to ellements strategies correctly

Integration tests (require OPENAI_API_KEY) verify:
- @prompt and @execute directives work end-to-end
"""

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from unittest.mock import AsyncMock

import pytest

from promptspec.controller import (
    CompositionResult,
    parse_composition_xml,
    _parse_json_object,
)


# ═══════════════════════════════════════════════════════════════════
# Mock LLMClient (same as ellements tests)
# ═══════════════════════════════════════════════════════════════════

class MockLLMClient:
    """Mock LLMClient for testing engines without real LLM calls."""

    def __init__(self, responses=None):
        self._responses = responses or ["Mock response"]
        self._call_count = 0
        self.calls: List[Dict[str, Any]] = []
        self.default_model = "mock-model"

    async def complete(
        self,
        messages: Union[str, List[Dict[str, str]]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> str:
        if isinstance(messages, str):
            messages = [{"role": "user", "content": messages}]
        self.calls.append({
            "messages": messages,
            "model": model,
            "temperature": temperature,
        })
        if callable(self._responses):
            return self._responses(messages, **kwargs)
        idx = min(self._call_count, len(self._responses) - 1)
        self._call_count += 1
        return self._responses[idx]


# ═══════════════════════════════════════════════════════════════════
# Unit Tests: @prompt and @execute XML parsing
# ═══════════════════════════════════════════════════════════════════

class TestParsePromptsAndExecution:
    """Test parse_composition_xml handles <prompts> and <execution>."""

    def test_single_prompt_default(self):
        """No <prompts> tag — auto-creates {"default": prompt}."""
        xml = (
            "<output>\n"
            "  <prompt>Hello world.</prompt>\n"
            "  <analysis></analysis>\n"
            "  <warnings></warnings>\n"
            "  <errors></errors>\n"
            "  <suggestions></suggestions>\n"
            "</output>"
        )
        result = parse_composition_xml(xml)
        assert result.composed_prompt == "Hello world."
        assert result.prompts == {"default": "Hello world."}

    def test_named_prompts(self):
        """<prompts> with named prompts."""
        prompts = {
            "generate": "Generate 3 approaches to X.",
            "evaluate": "Rate these approaches.",
            "synthesize": "Elaborate the best one.",
        }
        xml = (
            "<output>\n"
            "  <prompt>Shared context.</prompt>\n"
            f"  <prompts>{json.dumps(prompts)}</prompts>\n"
            "  <tools>[]</tools>\n"
            "  <execution>{}</execution>\n"
            "  <analysis></analysis>\n"
            "  <warnings></warnings>\n"
            "  <errors></errors>\n"
            "  <suggestions></suggestions>\n"
            "</output>"
        )
        result = parse_composition_xml(xml)
        assert result.prompts == prompts
        assert "generate" in result.prompts
        assert "evaluate" in result.prompts
        assert "synthesize" in result.prompts

    def test_execution_metadata(self):
        """<execution> with strategy metadata."""
        execution = {
            "type": "tree-of-thought",
            "branching_factor": 3,
            "max_depth": 2,
        }
        xml = (
            "<output>\n"
            "  <prompt>Hello.</prompt>\n"
            f"  <execution>{json.dumps(execution)}</execution>\n"
            "  <analysis></analysis>\n"
            "  <warnings></warnings>\n"
            "  <errors></errors>\n"
            "  <suggestions></suggestions>\n"
            "</output>"
        )
        result = parse_composition_xml(xml)
        assert result.execution == execution
        assert result.execution["type"] == "tree-of-thought"
        assert result.execution["branching_factor"] == 3

    def test_empty_execution(self):
        """Empty <execution> tag."""
        xml = (
            "<output>\n"
            "  <prompt>Hello.</prompt>\n"
            "  <execution>{}</execution>\n"
            "  <analysis></analysis>\n"
            "  <warnings></warnings>\n"
            "  <errors></errors>\n"
            "  <suggestions></suggestions>\n"
            "</output>"
        )
        result = parse_composition_xml(xml)
        assert result.execution == {}

    def test_no_execution_tag(self):
        """Missing <execution> tag defaults to empty dict."""
        xml = (
            "<output>\n"
            "  <prompt>Hello.</prompt>\n"
            "  <analysis></analysis>\n"
            "  <warnings></warnings>\n"
            "  <errors></errors>\n"
            "  <suggestions></suggestions>\n"
            "</output>"
        )
        result = parse_composition_xml(xml)
        assert result.execution == {}

    def test_full_output_with_all_tags(self):
        """Full output with prompts, tools, execution, all tags."""
        prompts = {"default": "You are a helper."}
        tools = [{"type": "function", "function": {"name": "search"}}]
        execution = {"type": "self-consistency", "samples": 5}
        xml = (
            "<output>\n"
            "  <prompt>You are a helper.</prompt>\n"
            f"  <prompts>{json.dumps(prompts)}</prompts>\n"
            f"  <tools>{json.dumps(tools)}</tools>\n"
            f"  <execution>{json.dumps(execution)}</execution>\n"
            "  <analysis>Processed spec.</analysis>\n"
            "  <warnings>- Warning 1</warnings>\n"
            "  <errors></errors>\n"
            "  <suggestions></suggestions>\n"
            "</output>"
        )
        result = parse_composition_xml(xml)
        assert result.composed_prompt == "You are a helper."
        assert result.prompts == prompts
        assert len(result.tools) == 1
        assert result.execution == execution
        assert result.analysis == "Processed spec."
        assert len(result.warnings) == 1


class TestCompositionResultToDict:
    """Test to_dict includes prompts and execution."""

    def test_to_dict_with_prompts(self):
        prompts = {"generate": "gen", "evaluate": "eval"}
        result = CompositionResult(
            composed_prompt="gen",
            prompts=prompts,
        )
        d = result.to_dict()
        assert d["prompts"] == prompts

    def test_to_dict_with_execution(self):
        execution = {"type": "tree-of-thought", "branching_factor": 3}
        result = CompositionResult(
            composed_prompt="Hello",
            execution=execution,
        )
        d = result.to_dict()
        assert d["execution"] == execution

    def test_to_dict_empty_prompts_and_execution(self):
        result = CompositionResult(composed_prompt="Hello")
        d = result.to_dict()
        assert "prompts" not in d
        assert "execution" not in d


class TestParseJsonObject:
    """Test _parse_json_object helper."""

    def test_empty_string(self):
        assert _parse_json_object("", "test") == {}

    def test_valid_dict(self):
        assert _parse_json_object('{"a": 1}', "test") == {"a": 1}

    def test_invalid_json(self):
        assert _parse_json_object("not json", "test") == {}

    def test_non_dict(self):
        assert _parse_json_object("[1, 2]", "test") == {}


# ═══════════════════════════════════════════════════════════════════
# Unit Tests: Engine protocol and registry
# ═══════════════════════════════════════════════════════════════════

class TestEngineProtocol:
    """Verify Engine protocol and registry."""

    def test_builtin_engines_satisfy_protocol(self):
        from promptspec.engines import (
            Engine,
            SingleCallEngine,
            SelfConsistencyEngine,
            TreeOfThoughtEngine,
            ReflectionEngine,
        )
        assert isinstance(SingleCallEngine(), Engine)
        assert isinstance(SelfConsistencyEngine(), Engine)
        assert isinstance(TreeOfThoughtEngine(), Engine)
        assert isinstance(ReflectionEngine(), Engine)

    def test_custom_class_satisfies_protocol(self):
        from promptspec.engines import Engine, ExecutionResult

        class CustomEngine:
            async def execute(self, result, config=None):
                return ExecutionResult(output="custom")

        assert isinstance(CustomEngine(), Engine)

    def test_resolve_builtin_names(self):
        from promptspec.engines import resolve_engine
        from promptspec.engines.single_call import SingleCallEngine
        from promptspec.engines.self_consistency import SelfConsistencyEngine
        from promptspec.engines.tree_of_thought import TreeOfThoughtEngine
        from promptspec.engines.reflection import ReflectionEngine

        assert isinstance(resolve_engine("single-call"), SingleCallEngine)
        assert isinstance(resolve_engine("self-consistency"), SelfConsistencyEngine)
        assert isinstance(resolve_engine("tree-of-thought"), TreeOfThoughtEngine)
        assert isinstance(resolve_engine("reflection"), ReflectionEngine)

    def test_resolve_unknown_raises(self):
        from promptspec.engines import resolve_engine
        with pytest.raises(ValueError, match="Unknown engine"):
            resolve_engine("nonexistent-engine")


# ═══════════════════════════════════════════════════════════════════
# Unit Tests: RuntimeConfig
# ═══════════════════════════════════════════════════════════════════

class TestRuntimeConfig:
    """Test RuntimeConfig loading."""

    def test_from_json(self):
        from promptspec.engines import RuntimeConfig
        config_data = {
            "engine": "tree-of-thought",
            "engine_config": {"branching_factor": 3},
            "prompts": {
                "generate": {"model": "gpt-4.1", "temperature": 0.9},
                "evaluate": {"model": "gpt-4.1", "temperature": 0.1},
            },
            "variables": {"problem": "test"},
        }
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(config_data, f)
            f.flush()
            config = RuntimeConfig.from_json(Path(f.name))

        assert config.engine == "tree-of-thought"
        assert config.engine_config == {"branching_factor": 3}
        assert config.prompts["generate"].model == "gpt-4.1"
        assert config.prompts["generate"].temperature == 0.9
        assert config.prompts["evaluate"].temperature == 0.1
        assert config.variables == {"problem": "test"}
        Path(f.name).unlink()

    def test_from_yaml(self):
        from promptspec.engines import RuntimeConfig
        yaml_text = (
            "engine: self-consistency\n"
            "engine_config:\n"
            "  samples: 5\n"
            "  aggregation: majority-vote\n"
            "prompts:\n"
            "  default:\n"
            "    model: gpt-4.1\n"
            "    temperature: 0.8\n"
            "variables:\n"
            "  topic: testing\n"
        )
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            f.write(yaml_text)
            f.flush()
            config = RuntimeConfig.from_yaml(Path(f.name))

        assert config.engine == "self-consistency"
        assert config.engine_config["samples"] == 5
        assert config.prompts["default"].model == "gpt-4.1"
        assert config.prompts["default"].temperature == 0.8
        assert config.variables["topic"] == "testing"
        Path(f.name).unlink()

    def test_defaults(self):
        from promptspec.engines import RuntimeConfig
        config = RuntimeConfig()
        assert config.engine == "single-call"
        assert config.engine_config == {}
        assert config.prompts == {}
        assert config.variables == {}


# ═══════════════════════════════════════════════════════════════════
# Unit Tests: Engine wrappers with MockLLMClient
# ═══════════════════════════════════════════════════════════════════

class TestSingleCallEngine:

    @pytest.mark.asyncio
    async def test_basic_execution(self):
        from promptspec.engines.single_call import SingleCallEngine
        from promptspec.engines.base import ExecutionResult

        client = MockLLMClient(["The answer is 42."])
        engine = SingleCallEngine(client=client)

        result_cr = CompositionResult(
            composed_prompt="What is the meaning?",
            prompts={"default": "What is the meaning?"},
        )
        exec_result = await engine.execute(result_cr)

        assert isinstance(exec_result, ExecutionResult)
        assert exec_result.output == "The answer is 42."
        assert len(exec_result.steps) == 1
        assert len(client.calls) == 1


class TestSelfConsistencyEngine:

    @pytest.mark.asyncio
    async def test_majority_vote(self):
        from promptspec.engines.self_consistency import SelfConsistencyEngine
        from promptspec.engines.base import RuntimeConfig

        client = MockLLMClient(["Paris", "Paris", "London"])
        engine = SelfConsistencyEngine(client=client)

        result_cr = CompositionResult(
            composed_prompt="Capital of France?",
            prompts={"default": "Capital of France?"},
            execution={"type": "self-consistency", "samples": 3},
        )
        exec_result = await engine.execute(result_cr)

        assert exec_result.output == "Paris"
        assert len(client.calls) == 3


class TestTreeOfThoughtEngine:

    @pytest.mark.asyncio
    async def test_three_stage_pipeline(self):
        from promptspec.engines.tree_of_thought import TreeOfThoughtEngine

        responses = ["Approach A, B, C", "B is best", "Detailed solution B"]
        client = MockLLMClient(responses)
        engine = TreeOfThoughtEngine(client=client)

        result_cr = CompositionResult(
            composed_prompt="shared context",
            prompts={
                "generate": "Generate {{branching_factor}} approaches",
                "evaluate": "Evaluate: {{candidates}}",
                "synthesize": "Elaborate: {{best_approach}}",
            },
            execution={"type": "tree-of-thought", "branching_factor": 3},
        )
        exec_result = await engine.execute(result_cr)

        assert exec_result.output == "Detailed solution B"
        assert len(client.calls) == 3
        assert len(exec_result.steps) == 3

    @pytest.mark.asyncio
    async def test_config_override(self):
        """RuntimeConfig engine_config overrides @execute params."""
        from promptspec.engines.tree_of_thought import TreeOfThoughtEngine
        from promptspec.engines.base import RuntimeConfig

        responses = ["ideas", "eval", "synth"]
        client = MockLLMClient(responses)
        engine = TreeOfThoughtEngine(client=client)

        result_cr = CompositionResult(
            composed_prompt="ctx",
            prompts={
                "generate": "Gen {{branching_factor}}",
                "evaluate": "Eval {{candidates}}",
                "synthesize": "Synth {{best_approach}}",
            },
            execution={"type": "tree-of-thought", "branching_factor": 2},
        )
        runtime_config = RuntimeConfig(
            engine="tree-of-thought",
            engine_config={"branching_factor": 5},
        )
        exec_result = await engine.execute(result_cr, runtime_config)

        # The generate prompt should have "5" (from runtime override)
        gen_prompt = client.calls[0]["messages"][-1]["content"]
        assert "5" in gen_prompt


class TestReflectionEngine:

    @pytest.mark.asyncio
    async def test_generates_and_reflects(self):
        from promptspec.engines.reflection import ReflectionEngine

        responses = [
            "Draft answer",
            "No issues found, looks good.",
        ]
        client = MockLLMClient(responses)
        engine = ReflectionEngine(client=client)

        result_cr = CompositionResult(
            composed_prompt="ctx",
            prompts={
                "generate": "Write about X",
                "critique": "Critique: {{response}}",
                "revise": "Fix: {{response}} — {{critique}}",
            },
            execution={"type": "reflection", "max_rounds": 3},
        )
        exec_result = await engine.execute(result_cr)

        assert exec_result.output == "Draft answer"
        assert len(client.calls) == 2  # generate + critique (stopped early)


class TestBaseEngineConfigMerge:
    """Test that BaseEngine._build_strategy_config merges correctly."""

    def test_spec_only(self):
        from promptspec.engines.base import BaseEngine
        engine = BaseEngine()
        result = CompositionResult(
            composed_prompt="x",
            execution={"type": "tot", "branching_factor": 3, "max_depth": 2},
        )
        config = engine._build_strategy_config(result)
        assert config["branching_factor"] == 3
        assert config["max_depth"] == 2
        assert "type" not in config  # type is stripped

    def test_runtime_overrides_spec(self):
        from promptspec.engines.base import BaseEngine, RuntimeConfig
        engine = BaseEngine()
        result = CompositionResult(
            composed_prompt="x",
            execution={"type": "tot", "branching_factor": 3},
        )
        runtime = RuntimeConfig(engine_config={"branching_factor": 5, "extra": True})
        config = engine._build_strategy_config(result, runtime)
        assert config["branching_factor"] == 5  # runtime wins
        assert config["extra"] is True  # new key from runtime

    def test_empty_spec_and_runtime(self):
        from promptspec.engines.base import BaseEngine
        engine = BaseEngine()
        result = CompositionResult(composed_prompt="x")
        config = engine._build_strategy_config(result)
        assert config == {}


# ═══════════════════════════════════════════════════════════════════
# Integration Tests — require OPENAI_API_KEY
# ═══════════════════════════════════════════════════════════════════

_skip = pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY not set — requires a real LLM",
)


@_skip
class TestPromptDirectiveE2E:
    """End-to-end tests for the @prompt directive."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_named_prompts(self):
        """@prompt directives produce named prompts in the output."""
        from promptspec.controller import PromptSpecController, PromptSpecConfig

        spec = (
            "You are a problem solver.\n\n"
            "@prompt generate\n"
            "  Generate 3 approaches to solving the problem.\n\n"
            "@prompt evaluate\n"
            "  Evaluate and rank the following approaches.\n"
        )
        controller = PromptSpecController(PromptSpecConfig())
        result = await controller.compose(spec, {})

        assert result.prompts, "Should produce named prompts"
        assert len(result.prompts) >= 2
        assert "generate" in result.prompts
        assert "evaluate" in result.prompts

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_execution_directive(self):
        """@execute directive produces execution metadata."""
        from promptspec.controller import PromptSpecController, PromptSpecConfig

        spec = (
            "You are a solver.\n\n"
            "@execute self-consistency\n"
            "  samples: 5\n"
            "  aggregation: majority-vote\n"
        )
        controller = PromptSpecController(PromptSpecConfig())
        result = await controller.compose(spec, {})

        assert result.execution, "Should have execution metadata"
        assert result.execution.get("type") == "self-consistency"


# ═══════════════════════════════════════════════════════════════════
# Prompt validation tests
# ═══════════════════════════════════════════════════════════════════

class TestPromptValidation:
    """Verify engines reject specs missing required @prompt blocks."""

    @pytest.mark.asyncio
    async def test_tree_of_thought_missing_prompts(self):
        """ToT engine rejects spec with only default prompt."""
        from promptspec.engines.tree_of_thought import TreeOfThoughtEngine
        engine = TreeOfThoughtEngine(client=MockLLMClient(["x"] * 5))
        result = CompositionResult(
            composed_prompt="solve this",
            raw_xml="",
            prompts={"default": "solve this"},
        )
        with pytest.raises(ValueError, match="generate.*evaluate.*synthesize"):
            await engine.execute(result)

    @pytest.mark.asyncio
    async def test_tree_of_thought_with_all_prompts(self):
        """ToT engine accepts spec with all required prompts."""
        from promptspec.engines.tree_of_thought import TreeOfThoughtEngine
        engine = TreeOfThoughtEngine(client=MockLLMClient(["x"] * 5))
        result = CompositionResult(
            composed_prompt="",
            raw_xml="",
            prompts={
                "generate": "gen {{branching_factor}}",
                "evaluate": "eval {{candidates}}",
                "synthesize": "synth {{best_approach}}",
            },
        )
        exec_result = await engine.execute(result)
        assert exec_result.output

    @pytest.mark.asyncio
    async def test_reflection_missing_prompts(self):
        """Reflection engine rejects spec missing critique/revise."""
        from promptspec.engines.reflection import ReflectionEngine
        engine = ReflectionEngine(client=MockLLMClient(["x"] * 5))
        result = CompositionResult(
            composed_prompt="write something",
            raw_xml="",
            prompts={"default": "write something", "generate": "write"},
        )
        with pytest.raises(ValueError, match="critique.*revise"):
            await engine.execute(result)

    @pytest.mark.asyncio
    async def test_self_consistency_with_default_only(self):
        """Self-consistency only needs default — should pass."""
        from promptspec.engines.self_consistency import SelfConsistencyEngine
        engine = SelfConsistencyEngine(client=MockLLMClient(["ans"] * 5))
        result = CompositionResult(
            composed_prompt="What is 2+2?",
            raw_xml="",
        )
        exec_result = await engine.execute(result)
        assert exec_result.output

    @pytest.mark.asyncio
    async def test_single_call_with_default_only(self):
        """Single-call only needs default — should pass."""
        from promptspec.engines.single_call import SingleCallEngine
        engine = SingleCallEngine(client=MockLLMClient(["ok"]))
        result = CompositionResult(
            composed_prompt="Hello",
            raw_xml="",
        )
        exec_result = await engine.execute(result)
        assert exec_result.output == "ok"
