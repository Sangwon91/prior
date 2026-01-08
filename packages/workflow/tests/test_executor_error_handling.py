"""Tests for executor error handling."""

import pytest

from workflow.executor import Executor
from workflow.graph import Graph
from workflow.node import Node
from workflow.state import ExecutionContext
from workflow.types import NodeState


class FailingNode(Node):
    """Node that always fails."""

    async def execute(self, context):
        raise ValueError("Node failed")


class SimpleNode(Node):
    """Simple test node."""

    def __init__(self, node_id: str, output: str = "output"):
        super().__init__(node_id)
        self.output = output

    async def execute(self, context):
        return self.output


@pytest.mark.asyncio
async def test_executor_raises_on_error():
    """Test executor raises exception on node failure by default."""
    graph = Graph()
    node = FailingNode("node1")
    graph.add_node(node)

    executor = Executor(continue_on_error=False)
    context = ExecutionContext()

    with pytest.raises(ValueError, match="Node failed"):
        await executor.execute(graph, context)

    assert context.get_node_state("node1") == NodeState.FAILED


@pytest.mark.asyncio
async def test_executor_continues_on_error():
    """Test executor continues execution when continue_on_error=True."""
    graph = Graph()
    failing_node = FailingNode("node1")
    simple_node = SimpleNode("node2", "output2")

    graph.add_node(failing_node)
    graph.add_node(simple_node, dependencies=["node1"])

    executor = Executor(continue_on_error=True)
    context = ExecutionContext()

    # Should not raise
    result_context = await executor.execute(graph, context)

    assert result_context.get_node_state("node1") == NodeState.FAILED
    # node2 should still execute even though node1 failed
    assert result_context.get_node_state("node2") == NodeState.COMPLETED

