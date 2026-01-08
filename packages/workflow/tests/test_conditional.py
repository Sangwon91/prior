"""Tests for ConditionalNode."""

import pytest

from workflow.graph import Graph
from workflow.nodes.conditional import ConditionalNode
from workflow.node import Node
from workflow.state import ExecutionContext
from workflow.executor import Executor
from workflow.types import NodeState


class SimpleNode(Node):
    """Simple test node."""

    def __init__(self, node_id: str, output: str = "output"):
        super().__init__(node_id)
        self.output = output

    async def execute(self, context):
        return self.output


@pytest.mark.asyncio
async def test_conditional_node_true():
    """Test conditional node with true condition."""
    context = ExecutionContext({"value": 10})

    def condition(ctx):
        return ctx.get("value", 0) > 5

    node = ConditionalNode("cond1", condition, "true_node", "false_node")

    result = await node.execute(context)

    assert result is True
    assert context.get("cond1_condition_result") is True
    assert context.get("cond1_next_node") == "true_node"


@pytest.mark.asyncio
async def test_conditional_node_false():
    """Test conditional node with false condition."""
    context = ExecutionContext({"value": 3})

    def condition(ctx):
        return ctx.get("value", 0) > 5

    node = ConditionalNode("cond1", condition, "true_node", "false_node")

    result = await node.execute(context)

    assert result is False
    assert context.get("cond1_condition_result") is False
    assert context.get("cond1_next_node") == "false_node"


@pytest.mark.asyncio
async def test_conditional_in_graph():
    """Test conditional node in a workflow graph."""
    graph = Graph()

    def condition(ctx):
        return ctx.get("flag", False)

    cond_node = ConditionalNode("cond", condition, "node_true", "node_false")
    true_node = SimpleNode("node_true", "true_output")
    false_node = SimpleNode("node_false", "false_output")

    graph.add_node(cond_node)
    graph.add_node(true_node, dependencies=["cond"])
    graph.add_node(false_node, dependencies=["cond"])

    # Test with flag=True
    context = ExecutionContext({"flag": True})
    executor = Executor()
    await executor.execute(graph, context)

    assert context.get_node_state("cond") == NodeState.COMPLETED
    assert context.get("cond_next_node") == "node_true"

