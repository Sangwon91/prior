"""Tests for ConditionalNode."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from workflow import BaseNode, End, Graph, GraphRunContext
from workflow.nodes.conditional import ConditionalNode


@dataclass
class TestState:
    """Test state for conditional tests."""

    value: int = 0
    flag: bool = False


@dataclass
class TrueNode(BaseNode[TestState, None, str]):
    """Node executed when condition is true."""

    async def run(
        self, ctx: GraphRunContext[TestState]
    ) -> End[str]:
        return End("true_result")


@dataclass
class FalseNode(BaseNode[TestState, None, str]):
    """Node executed when condition is false."""

    async def run(
        self, ctx: GraphRunContext[TestState]
    ) -> End[str]:
        return End("false_result")


@pytest.mark.asyncio
async def test_conditional_node_true():
    """Test conditional node with true condition."""
    state = TestState(value=10)

    def condition(ctx: GraphRunContext[TestState]) -> bool:
        return ctx.state.value > 5

    cond_node = ConditionalNode(
        condition=condition,
        true_node=TrueNode(),
        false_node=FalseNode(),
    )

    ctx = GraphRunContext(state=state)
    next_node = await cond_node.run(ctx)

    assert isinstance(next_node, TrueNode)


@pytest.mark.asyncio
async def test_conditional_node_false():
    """Test conditional node with false condition."""
    state = TestState(value=3)

    def condition(ctx: GraphRunContext[TestState]) -> bool:
        return ctx.state.value > 5

    cond_node = ConditionalNode(
        condition=condition,
        true_node=TrueNode(),
        false_node=FalseNode(),
    )

    ctx = GraphRunContext(state=state)
    next_node = await cond_node.run(ctx)

    assert isinstance(next_node, FalseNode)


@pytest.mark.asyncio
async def test_conditional_in_graph():
    """Test conditional node in a workflow graph."""
    state = TestState(flag=True)

    def condition(ctx: GraphRunContext[TestState]) -> bool:
        return ctx.state.flag

    cond_node = ConditionalNode(
        condition=condition,
        true_node=TrueNode(),
        false_node=FalseNode(),
    )

    graph = Graph(nodes=(ConditionalNode, TrueNode, FalseNode))
    result = await graph.run(cond_node, state=state)

    assert result.output == "true_result"


@pytest.mark.asyncio
async def test_conditional_in_graph_false():
    """Test conditional node in a workflow graph with false condition."""
    state = TestState(flag=False)

    def condition(ctx: GraphRunContext[TestState]) -> bool:
        return ctx.state.flag

    cond_node = ConditionalNode(
        condition=condition,
        true_node=TrueNode(),
        false_node=FalseNode(),
    )

    graph = Graph(nodes=(ConditionalNode, TrueNode, FalseNode))
    result = await graph.run(cond_node, state=state)

    assert result.output == "false_result"
