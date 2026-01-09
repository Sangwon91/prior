"""Tests for synchronous execution in workflows."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

import pytest

from workflow import BaseNode, End, Graph, GraphRunContext


@dataclass
class SyncState:
    """Test state for sync execution tests."""

    value: int = 0
    executed: bool = False
    steps: list[str] = None

    def __post_init__(self):
        if self.steps is None:
            self.steps = []


@dataclass
class SyncNode(BaseNode[SyncState, None, str]):
    """Simple node for sync execution."""

    output: str = "sync_result"

    async def run(self, ctx: GraphRunContext[SyncState]) -> End[str]:
        ctx.state.executed = True
        ctx.state.value = 42
        return End(self.output)


@dataclass
class MultiStepSyncNode(BaseNode[SyncState, None, int]):
    """Node that chains to next step."""

    step: int
    max_steps: int

    async def run(
        self, ctx: GraphRunContext[SyncState]
    ) -> MultiStepSyncNode | End[int]:
        ctx.state.steps.append(f"step_{self.step}")
        ctx.state.value += self.step

        if self.step >= self.max_steps:
            return End(ctx.state.value)
        return MultiStepSyncNode(step=self.step + 1, max_steps=self.max_steps)


@dataclass
class ConditionalSyncNode(BaseNode[SyncState, None, str]):
    """Node with conditional branching for sync test."""

    async def run(
        self, ctx: GraphRunContext[SyncState]
    ) -> TrueSyncNode | FalseSyncNode:
        if ctx.state.value > 0:
            return TrueSyncNode()
        return FalseSyncNode()


@dataclass
class TrueSyncNode(BaseNode[SyncState, None, str]):
    """Node executed when condition is true."""

    async def run(self, ctx: GraphRunContext[SyncState]) -> End[str]:
        return End("true_branch")


@dataclass
class FalseSyncNode(BaseNode[SyncState, None, str]):
    """Node executed when condition is false."""

    async def run(self, ctx: GraphRunContext[SyncState]) -> End[str]:
        return End("false_branch")


def test_run_sync_simple():
    """Test simple synchronous execution."""
    state = SyncState()

    graph = Graph(nodes=(SyncNode,))
    # Use asyncio.run() to test sync behavior in a non-async context
    result = asyncio.run(graph.run(SyncNode(output="test"), state=state))

    assert result.output == "test"
    assert result.state.executed is True
    assert result.state.value == 42


def test_run_sync_vs_async():
    """Test that sync and async execution produce same results."""
    state_async = SyncState()
    state_sync = SyncState()

    graph = Graph(nodes=(SyncNode,))

    # Run async using asyncio.run()
    result_async = asyncio.run(
        graph.run(SyncNode(output="test"), state=state_async)
    )

    # Run sync using asyncio.run() to simulate sync behavior
    result_sync = asyncio.run(
        graph.run(SyncNode(output="test"), state=state_sync)
    )

    # Results should be identical
    assert result_async.output == result_sync.output
    assert result_async.state.value == result_sync.state.value
    assert result_async.state.executed == result_sync.state.executed


def test_run_sync_multi_step():
    """Test synchronous execution of multi-step workflow."""
    state = SyncState()

    graph = Graph(nodes=(MultiStepSyncNode,))
    result = asyncio.run(
        graph.run(MultiStepSyncNode(step=1, max_steps=5), state=state)
    )

    assert result.output == sum(range(1, 6))  # 15
    assert result.state.value == 15
    assert len(result.state.steps) == 5
    assert result.state.steps == [
        "step_1",
        "step_2",
        "step_3",
        "step_4",
        "step_5",
    ]


def test_run_sync_conditional():
    """Test synchronous execution with conditional branching."""
    state_true = SyncState(value=10)
    state_false = SyncState(value=0)

    graph = Graph(nodes=(ConditionalSyncNode, TrueSyncNode, FalseSyncNode))

    # Test true branch
    result_true = asyncio.run(
        graph.run(ConditionalSyncNode(), state=state_true)
    )
    assert result_true.output == "true_branch"

    # Test false branch
    result_false = asyncio.run(
        graph.run(ConditionalSyncNode(), state=state_false)
    )
    assert result_false.output == "false_branch"


def test_run_sync_with_deps():
    """Test synchronous execution with dependencies."""
    state = SyncState()

    @dataclass
    class DepsSyncNode(BaseNode[SyncState, dict[str, str], str]):
        async def run(
            self, ctx: GraphRunContext[SyncState, dict[str, str]]
        ) -> End[str]:
            if ctx.deps:
                return End(f"deps_{ctx.deps.get('key', 'none')}")
            return End("no_deps")

    graph = Graph(nodes=(DepsSyncNode,))
    deps = {"key": "value123"}

    result = asyncio.run(graph.run(DepsSyncNode(), state=state, deps=deps))

    assert result.output == "deps_value123"


def test_run_sync_state_modification():
    """Test that state modifications persist in sync execution."""
    state = SyncState()

    @dataclass
    class ModifyNode(BaseNode[SyncState, None, int]):
        async def run(self, ctx: GraphRunContext[SyncState]) -> End[int]:
            ctx.state.value = 100
            ctx.state.executed = True
            ctx.state.steps.append("modified")
            return End(ctx.state.value)

    graph = Graph(nodes=(ModifyNode,))
    result = asyncio.run(graph.run(ModifyNode(), state=state))

    assert result.output == 100
    assert result.state.value == 100
    assert result.state.executed is True
    assert "modified" in result.state.steps


def test_run_sync_error_handling():
    """Test error handling in sync execution."""
    state = SyncState()

    @dataclass
    class ErrorNode(BaseNode[SyncState, None, str]):
        async def run(self, ctx: GraphRunContext[SyncState]) -> End[str]:
            raise ValueError("Sync execution error")

    graph = Graph(nodes=(ErrorNode,))

    with pytest.raises(ValueError, match="Sync execution error"):
        asyncio.run(graph.run(ErrorNode(), state=state))


def test_run_sync_complex_workflow():
    """Test sync execution of complex workflow."""
    state = SyncState()

    @dataclass
    class StartNode(BaseNode[SyncState, None, str]):
        async def run(
            self, ctx: GraphRunContext[SyncState]
        ) -> ProcessNode | End[str]:
            ctx.state.steps.append("start")
            return ProcessNode()

    @dataclass
    class ProcessNode(BaseNode[SyncState, None, str]):
        async def run(
            self, ctx: GraphRunContext[SyncState]
        ) -> FinishNode | End[str]:
            ctx.state.steps.append("process")
            ctx.state.value += 50
            return FinishNode()

    @dataclass
    class FinishNode(BaseNode[SyncState, None, str]):
        async def run(self, ctx: GraphRunContext[SyncState]) -> End[str]:
            ctx.state.steps.append("finish")
            ctx.state.value += 50
            return End(f"completed_{ctx.state.value}")

    graph = Graph(nodes=(StartNode, ProcessNode, FinishNode))
    result = asyncio.run(graph.run(StartNode(), state=state))

    assert result.output == "completed_100"
    assert result.state.value == 100
    assert result.state.steps == ["start", "process", "finish"]
