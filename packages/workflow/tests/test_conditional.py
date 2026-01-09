"""Tests for conditional branching with pydantic_graph style."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from workflow import BaseNode, End, Graph, GraphRunContext


@dataclass
class TestState:
    """Test state for conditional tests."""

    value: int = 0
    flag: bool = False


@dataclass
class TrueNode(BaseNode[TestState, None, str]):
    """Node executed when condition is true."""

    async def run(self, ctx: GraphRunContext[TestState]) -> End[str]:
        return End("true_result")


@dataclass
class FalseNode(BaseNode[TestState, None, str]):
    """Node executed when condition is false."""

    async def run(self, ctx: GraphRunContext[TestState]) -> End[str]:
        return End("false_result")


@dataclass
class CheckValueNode(BaseNode[TestState, None, str]):
    """Node that conditionally branches based on state value."""

    async def run(
        self, ctx: GraphRunContext[TestState]
    ) -> TrueNode | FalseNode | End[str]:
        if ctx.state.value > 5:
            return TrueNode()
        else:
            return FalseNode()


@dataclass
class CheckFlagNode(BaseNode[TestState, None, str]):
    """Node that conditionally branches based on state flag."""

    async def run(
        self, ctx: GraphRunContext[TestState]
    ) -> TrueNode | FalseNode | End[str]:
        if ctx.state.flag:
            return TrueNode()
        else:
            return FalseNode()


@pytest.mark.asyncio
async def test_conditional_node_returns_true_branch_when_condition_true():
    """Test conditional node returns true branch when condition is true."""
    state = TestState(value=10)

    ctx = GraphRunContext(state=state)
    check_node = CheckValueNode()
    next_node = await check_node.run(ctx)

    assert isinstance(next_node, TrueNode)


@pytest.mark.asyncio
async def test_conditional_node_returns_false_branch_when_condition_false():
    """Test conditional node returns false branch when condition is false."""
    state = TestState(value=3)

    ctx = GraphRunContext(state=state)
    check_node = CheckValueNode()
    next_node = await check_node.run(ctx)

    assert isinstance(next_node, FalseNode)


@pytest.mark.asyncio
async def test_conditional_branching_in_workflow_graph_executes_true_branch():
    """Test conditional branching in workflow graph executes true branch."""
    state = TestState(flag=True)

    graph = Graph(nodes=(CheckFlagNode, TrueNode, FalseNode))
    result = await graph.run(CheckFlagNode(), state=state)

    assert result.output == "true_result"


@pytest.mark.asyncio
async def test_conditional_branching_in_workflow_graph_executes_false_branch():
    """Test conditional branching in workflow graph executes false branch."""
    state = TestState(flag=False)

    graph = Graph(nodes=(CheckFlagNode, TrueNode, FalseNode))
    result = await graph.run(CheckFlagNode(), state=state)

    assert result.output == "false_result"
