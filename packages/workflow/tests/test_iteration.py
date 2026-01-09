"""Tests for manual iteration control in workflows."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from workflow import BaseNode, End, Graph, GraphRunContext


@dataclass
class IterationState:
    """Test state for iteration tests."""

    count: int = 0
    visited_nodes: list[str] = None
    values: list[int] = None

    def __post_init__(self):
        if self.visited_nodes is None:
            self.visited_nodes = []
        if self.values is None:
            self.values = []


@dataclass
class CounterNode(BaseNode[IterationState, None, int]):
    """Node that increments counter."""

    async def run(
        self, ctx: GraphRunContext[IterationState]
    ) -> NextCounterNode | End[int]:
        ctx.state.count += 1
        ctx.state.visited_nodes.append("CounterNode")
        ctx.state.values.append(ctx.state.count)

        if ctx.state.count >= 3:
            return End(ctx.state.count)
        return NextCounterNode()


@dataclass
class NextCounterNode(BaseNode[IterationState, None, int]):
    """Next node in counter chain."""

    async def run(
        self, ctx: GraphRunContext[IterationState]
    ) -> CounterNode | End[int]:
        ctx.state.visited_nodes.append("NextCounterNode")
        return CounterNode()


@dataclass
class SimpleNode(BaseNode[IterationState, None, str]):
    """Simple node for testing."""

    name: str = "simple"

    async def run(self, ctx: GraphRunContext[IterationState]) -> End[str]:
        ctx.state.visited_nodes.append(self.name)
        return End(f"result_{self.name}")


@pytest.mark.asyncio
async def test_iter_basic():
    """Test basic iteration through graph execution."""
    state = IterationState()

    graph = Graph(nodes=(CounterNode, NextCounterNode))
    nodes_seen = []

    async with graph.iter(CounterNode(), state=state) as run:
        async for node in run:
            nodes_seen.append(type(node).__name__)
            if isinstance(node, End):
                break

    assert "CounterNode" in nodes_seen
    assert "NextCounterNode" in nodes_seen
    assert "End" in nodes_seen
    assert run.result is not None
    assert run.result.output == 3
    assert state.count == 3


@pytest.mark.asyncio
async def test_iter_manual_next():
    """Test manual control using run.next()."""
    state = IterationState()

    graph = Graph(nodes=(CounterNode, NextCounterNode))

    async with graph.iter(CounterNode(), state=state) as run:
        node = await run.__anext__()
        assert isinstance(node, CounterNode)

        # Execute CounterNode, returns NextCounterNode
        node = await run.next(node)
        assert isinstance(node, NextCounterNode)
        assert state.count == 1

        # Execute NextCounterNode, returns CounterNode
        node = await run.next(node)
        assert isinstance(node, CounterNode)
        assert state.count == 1  # CounterNode not executed yet

        # Execute CounterNode, returns NextCounterNode (count=2)
        node = await run.next(node)
        assert isinstance(node, NextCounterNode)
        assert state.count == 2

        # Execute NextCounterNode, returns CounterNode
        node = await run.next(node)
        assert isinstance(node, CounterNode)

        # Execute CounterNode, returns End (count=3)
        node = await run.next(node)
        assert isinstance(node, End)

    assert run.result is not None
    assert run.result.output == 3
    assert state.count == 3


@pytest.mark.asyncio
async def test_iter_state_inspection():
    """Test inspecting state during iteration."""
    state = IterationState()

    graph = Graph(nodes=(CounterNode, NextCounterNode))
    state_snapshots = []

    async with graph.iter(CounterNode(), state=state) as run:
        async for node in run:
            state_snapshots.append(run.state.count)
            if isinstance(node, End):
                break

    # Initial state (0), then after each CounterNode execution (1, 2, 3)
    # and after NextCounterNode execution (same count)
    assert state_snapshots == [0, 1, 1, 2, 2, 3]
    assert run.result.output == 3


@pytest.mark.asyncio
async def test_iter_state_modification():
    """Test modifying state during iteration."""
    state = IterationState()

    graph = Graph(nodes=(CounterNode, NextCounterNode))

    async with graph.iter(CounterNode(), state=state) as run:
        async for node in run:
            # Modify state during iteration
            if isinstance(node, CounterNode):
                run.state.count += 10  # Modify state
            if isinstance(node, End):
                break

    # State modifications should be reflected
    assert run.state.count >= 3


@pytest.mark.asyncio
async def test_iter_early_break():
    """Test breaking iteration early."""
    state = IterationState()

    graph = Graph(nodes=(CounterNode, NextCounterNode))
    iteration_count = 0

    async with graph.iter(CounterNode(), state=state) as run:
        async for node in run:
            iteration_count += 1
            if iteration_count >= 2:  # Break early
                break

    # Should have iterated 2 times before breaking
    assert iteration_count == 2
    # Result may not be set if we break early
    assert state.count >= 1


@pytest.mark.asyncio
async def test_iter_simple_node():
    """Test iteration with a simple single node."""
    state = IterationState()

    graph = Graph(nodes=(SimpleNode,))
    nodes_seen = []

    async with graph.iter(SimpleNode(name="test"), state=state) as run:
        async for node in run:
            nodes_seen.append(type(node).__name__)
            if isinstance(node, End):
                break

    assert "SimpleNode" in nodes_seen
    assert "End" in nodes_seen
    assert run.result is not None
    assert run.result.output == "result_test"


@pytest.mark.asyncio
async def test_iter_multiple_manual_steps():
    """Test multiple manual steps with run.next()."""
    state = IterationState()

    @dataclass
    class StepNode(BaseNode[IterationState, None, str]):
        step: int
        max_steps: int

        async def run(
            self, ctx: GraphRunContext[IterationState]
        ) -> StepNode | End[str]:
            ctx.state.count = self.step
            ctx.state.visited_nodes.append(f"step_{self.step}")

            if self.step >= self.max_steps:
                return End(f"step_{self.step}")
            return StepNode(step=self.step + 1, max_steps=self.max_steps)

    graph = Graph(nodes=(StepNode,))

    async with graph.iter(StepNode(step=1, max_steps=5), state=state) as run:
        node = await run.__anext__()
        step_count = 0

        while not isinstance(node, End) and step_count < 10:
            node = await run.next(node)
            step_count += 1

    assert run.result is not None
    assert run.result.output == "step_5"
    assert state.count == 5
    assert len(state.visited_nodes) == 5


@pytest.mark.asyncio
async def test_iter_result_access():
    """Test accessing result after iteration."""
    state = IterationState()

    graph = Graph(nodes=(SimpleNode,))

    async with graph.iter(SimpleNode(name="final"), state=state) as run:
        async for _node in run:
            pass

    # After iteration, result should be available
    assert run.result is not None
    assert run.result.output == "result_final"
    assert run.result.state.count == state.count
