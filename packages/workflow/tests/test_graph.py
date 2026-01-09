"""Tests for Graph class."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from workflow import BaseNode, End, Graph, GraphRunContext


@dataclass
class TestState:
    """Test state for graph execution."""

    value: int = 0
    output: str = ""


@dataclass
class SimpleNode(BaseNode[TestState, None, str]):
    """Simple test node."""

    output: str = "test"

    async def run(
        self, ctx: GraphRunContext[TestState]
    ) -> End[str]:
        return End(self.output)


@dataclass
class IncrementNode(BaseNode[TestState, None, int]):
    """Node that increments state value."""

    async def run(
        self, ctx: GraphRunContext[TestState]
    ) -> EndNode:
        ctx.state.value += 1
        return EndNode()


@dataclass
class EndNode(BaseNode[TestState, None, int]):
    """Node that ends with integer result."""

    async def run(
        self, ctx: GraphRunContext[TestState]
    ) -> End[int]:
        return End(ctx.state.value)


@pytest.mark.asyncio
async def test_graph_run_simple():
    """Test running a simple graph."""
    graph = Graph(nodes=(SimpleNode,))
    state = TestState()

    result = await graph.run(SimpleNode(output="hello"), state=state)

    assert result.output == "hello"


@pytest.mark.asyncio
async def test_graph_run_with_state():
    """Test running a graph that modifies state."""
    graph = Graph(nodes=(IncrementNode, EndNode))
    state = TestState(value=5)

    result = await graph.run(IncrementNode(), state=state)

    assert result.state.value == 6
    assert result.output == 6


@pytest.mark.asyncio
async def test_graph_iter():
    """Test iterating through graph execution."""
    graph = Graph(nodes=(IncrementNode, EndNode))
    state = TestState(value=0)

    nodes_executed = []
    async with graph.iter(IncrementNode(), state=state) as run:
        async for node in run:
            nodes_executed.append(type(node).__name__)

    assert "IncrementNode" in nodes_executed
    assert "End" in nodes_executed
    assert run.result is not None
    assert run.result.output == 1


@pytest.mark.asyncio
async def test_graph_node_not_in_graph():
    """Test that running a node not in graph raises error."""
    graph = Graph(nodes=(SimpleNode,))

    class OtherNode(BaseNode[TestState, None, str]):
        async def run(self, ctx: GraphRunContext[TestState]) -> End[str]:
            return End("other")

    state = TestState()

    async with graph.iter(OtherNode(), state=state) as run:
        with pytest.raises(ValueError, match="not in the graph"):
            await run.next(OtherNode())


