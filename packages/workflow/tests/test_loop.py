"""Tests for loop patterns in workflows."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from workflow import BaseNode, End, Graph, GraphRunContext


@dataclass
class LoopState:
    """Test state for loop tests."""

    iteration: int = 0
    max_iterations: int = 10
    values: list[int] = None

    def __post_init__(self):
        if self.values is None:
            self.values = []


@dataclass
class SelfLoopNode(BaseNode[LoopState, None, int]):
    """Node that returns itself to create a loop."""

    async def run(
        self, ctx: GraphRunContext[LoopState]
    ) -> SelfLoopNode | End[int]:
        ctx.state.iteration += 1
        ctx.state.values.append(ctx.state.iteration)

        if ctx.state.iteration >= ctx.state.max_iterations:
            return End(ctx.state.iteration)
        return SelfLoopNode()


@dataclass
class ConditionalLoopNode(BaseNode[LoopState, None, int]):
    """Node that loops based on state condition."""

    async def run(
        self, ctx: GraphRunContext[LoopState]
    ) -> ConditionalLoopNode | End[int]:
        ctx.state.iteration += 1
        ctx.state.values.append(ctx.state.iteration * 2)

        # Loop until iteration reaches max_iterations
        if ctx.state.iteration < ctx.state.max_iterations:
            return ConditionalLoopNode()
        return End(ctx.state.iteration)


@dataclass
class NestedLoopState:
    """State for nested loop tests."""

    outer_iteration: int = 0
    inner_iteration: int = 0
    max_outer: int = 3
    max_inner: int = 2
    trace: list[str] = None

    def __post_init__(self):
        if self.trace is None:
            self.trace = []


@dataclass
class OuterLoopNode(BaseNode[NestedLoopState, None, str]):
    """Outer loop node."""

    async def run(
        self, ctx: GraphRunContext[NestedLoopState]
    ) -> InnerLoopNode | End[str]:
        ctx.state.outer_iteration += 1
        ctx.state.trace.append(f"outer_{ctx.state.outer_iteration}")
        ctx.state.inner_iteration = 0  # Reset inner counter

        if ctx.state.outer_iteration > ctx.state.max_outer:
            return End(f"completed_{ctx.state.outer_iteration}")
        return InnerLoopNode()


@dataclass
class InnerLoopNode(BaseNode[NestedLoopState, None, str]):
    """Inner loop node."""

    async def run(
        self, ctx: GraphRunContext[NestedLoopState]
    ) -> InnerLoopNode | OuterLoopNode:
        ctx.state.inner_iteration += 1
        ctx.state.trace.append(f"inner_{ctx.state.inner_iteration}")

        if ctx.state.inner_iteration < ctx.state.max_inner:
            return InnerLoopNode()
        return OuterLoopNode()


@pytest.mark.asyncio
async def test_self_loop_basic():
    """Test basic self-referencing loop."""
    state = LoopState(max_iterations=5)

    graph = Graph(nodes=(SelfLoopNode,))
    result = await graph.run(SelfLoopNode(), state=state)

    assert result.output == 5
    assert result.state.iteration == 5
    assert len(result.state.values) == 5
    assert result.state.values == [1, 2, 3, 4, 5]


@pytest.mark.asyncio
async def test_self_loop_single_iteration():
    """Test self loop with max_iterations=1."""
    state = LoopState(max_iterations=1)

    graph = Graph(nodes=(SelfLoopNode,))
    result = await graph.run(SelfLoopNode(), state=state)

    assert result.output == 1
    assert result.state.iteration == 1
    assert len(result.state.values) == 1


@pytest.mark.asyncio
async def test_conditional_loop():
    """Test conditional loop based on state."""
    state = LoopState(max_iterations=3)

    graph = Graph(nodes=(ConditionalLoopNode,))
    result = await graph.run(ConditionalLoopNode(), state=state)

    assert result.output == 3
    assert result.state.iteration == 3
    assert len(result.state.values) == 3
    assert result.state.values == [2, 4, 6]


@pytest.mark.asyncio
async def test_nested_loops():
    """Test nested loop pattern."""
    state = NestedLoopState(max_outer=2, max_inner=2)

    graph = Graph(nodes=(OuterLoopNode, InnerLoopNode))
    result = await graph.run(OuterLoopNode(), state=state)

    assert result.output == "completed_3"
    assert result.state.outer_iteration == 3
    # Should have: outer_1, inner_1, inner_2, outer_2, inner_1, inner_2, outer_3
    expected_trace = [
        "outer_1",
        "inner_1",
        "inner_2",
        "outer_2",
        "inner_1",
        "inner_2",
        "outer_3",
    ]
    assert result.state.trace == expected_trace


@pytest.mark.asyncio
async def test_loop_with_zero_max():
    """Test loop that ends immediately due to zero max iterations."""
    state = LoopState(max_iterations=0)

    graph = Graph(nodes=(SelfLoopNode,))
    result = await graph.run(SelfLoopNode(), state=state)

    assert result.output == 1
    assert result.state.iteration == 1
    # Should execute once before checking condition
    assert len(result.state.values) == 1

