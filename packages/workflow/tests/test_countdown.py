"""Tests for countdown pattern in workflows."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from workflow import BaseNode, End, Graph, GraphRunContext


@dataclass
class CountdownState:
    """Test state for countdown tests."""

    counter: int = 0
    history: list[int] = None

    def __post_init__(self):
        if self.history is None:
            self.history = []


@dataclass
class CountdownNode(BaseNode[CountdownState, None, int]):
    """Node that decrements the counter."""

    async def run(
        self, ctx: GraphRunContext[CountdownState]
    ) -> CheckCountdownNode | End[int]:
        ctx.state.counter -= 1
        ctx.state.history.append(ctx.state.counter)
        return CheckCountdownNode()


@dataclass
class CheckCountdownNode(BaseNode[CountdownState, None, int]):
    """Node that checks if countdown should continue or end."""

    async def run(
        self, ctx: GraphRunContext[CountdownState]
    ) -> CountdownNode | End[int]:
        if ctx.state.counter > 0:
            return CountdownNode()
        else:
            return End(ctx.state.counter)


@pytest.mark.asyncio
async def test_countdown_basic():
    """Test basic countdown from 5 to 0."""
    state = CountdownState(counter=5)

    graph = Graph(nodes=(CountdownNode, CheckCountdownNode))
    result = await graph.run(CountdownNode(), state=state)

    assert result.output == 0
    assert result.state.counter == 0
    assert len(result.state.history) == 5
    assert result.state.history == [4, 3, 2, 1, 0]


@pytest.mark.asyncio
async def test_countdown_from_zero():
    """Test countdown starting from 0."""
    state = CountdownState(counter=0)

    graph = Graph(nodes=(CountdownNode, CheckCountdownNode))
    result = await graph.run(CountdownNode(), state=state)

    assert result.output == -1
    assert result.state.counter == -1
    assert len(result.state.history) == 1
    assert result.state.history == [-1]


@pytest.mark.asyncio
async def test_countdown_large_value():
    """Test countdown with a large initial value."""
    state = CountdownState(counter=10)

    graph = Graph(nodes=(CountdownNode, CheckCountdownNode))
    result = await graph.run(CountdownNode(), state=state)

    assert result.output == 0
    assert result.state.counter == 0
    assert len(result.state.history) == 10
    assert result.state.history[-1] == 0


@pytest.mark.asyncio
async def test_countdown_single_step():
    """Test countdown with counter=1."""
    state = CountdownState(counter=1)

    graph = Graph(nodes=(CountdownNode, CheckCountdownNode))
    result = await graph.run(CountdownNode(), state=state)

    assert result.output == 0
    assert result.state.counter == 0
    assert len(result.state.history) == 1
    assert result.state.history == [0]


@pytest.mark.asyncio
async def test_countdown_negative_start():
    """Test countdown starting from negative value."""
    state = CountdownState(counter=-3)

    graph = Graph(nodes=(CountdownNode, CheckCountdownNode))
    result = await graph.run(CountdownNode(), state=state)

    # Should decrement once and then end (since -4 <= 0)
    assert result.output == -4
    assert result.state.counter == -4
    assert len(result.state.history) == 1
    assert result.state.history == [-4]

