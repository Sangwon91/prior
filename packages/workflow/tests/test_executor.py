"""Tests for Executor class."""

import pytest

from workflow.executor import Executor
from workflow.graph import Graph
from workflow.node import Node
from workflow.state import ExecutionContext
from workflow.types import NodeState


class SimpleNode(Node):
    """Simple test node."""

    def __init__(self, node_id: str, output: str = "output"):
        super().__init__(node_id)
        self.output = output

    async def execute(self, context):
        return self.output


class FailingNode(Node):
    """Node that always fails."""

    async def execute(self, context):
        raise ValueError("Node failed")


class ContextNode(Node):
    """Node that uses context."""

    async def execute(self, context):
        value = context.get("input", 0)
        context.set("output", value * 2)
        return value * 2


@pytest.mark.asyncio
async def test_execute_simple_graph():
    """Test executing simple sequential graph."""
    graph = Graph()
    node1 = SimpleNode("node1", "output1")
    node2 = SimpleNode("node2", "output2")

    graph.add_node(node1)
    graph.add_node(node2, dependencies=["node1"])

    executor = Executor()
    context = ExecutionContext()

    result_context = await executor.execute(graph, context)

    assert result_context.get_node_state("node1") == NodeState.COMPLETED
    assert result_context.get_node_state("node2") == NodeState.COMPLETED
    assert result_context.get_node_output("node1") == "output1"
    assert result_context.get_node_output("node2") == "output2"


@pytest.mark.asyncio
async def test_execute_parallel_nodes():
    """Test executing parallel nodes."""
    graph = Graph()
    node1 = SimpleNode("node1", "output1")
    node2 = SimpleNode("node2", "output2")
    node3 = SimpleNode("node3", "output3")

    graph.add_node(node1)
    graph.add_node(node2, dependencies=["node1"])
    graph.add_node(node3, dependencies=["node1"])

    executor = Executor()
    context = ExecutionContext()

    result_context = await executor.execute(graph, context)

    assert result_context.get_node_state("node1") == NodeState.COMPLETED
    assert result_context.get_node_state("node2") == NodeState.COMPLETED
    assert result_context.get_node_state("node3") == NodeState.COMPLETED


@pytest.mark.asyncio
async def test_execute_with_context():
    """Test executing graph with context data."""
    graph = Graph()
    node = ContextNode("node1")

    graph.add_node(node)

    executor = Executor()
    context = ExecutionContext({"input": 5})

    result_context = await executor.execute(graph, context)

    assert result_context.get_node_output("node1") == 10
    assert result_context.get("output") == 10


@pytest.mark.asyncio
async def test_execute_failing_node():
    """Test executing graph with failing node."""
    graph = Graph()
    node = FailingNode("node1")

    graph.add_node(node)

    executor = Executor()
    context = ExecutionContext()

    with pytest.raises(ValueError, match="Node failed"):
        await executor.execute(graph, context)

    assert context.get_node_state("node1") == NodeState.FAILED
    assert context.get_result("node1").error is not None


@pytest.mark.asyncio
async def test_execute_invalid_graph():
    """Test executing invalid graph raises error."""
    graph = Graph()
    node1 = SimpleNode("node1")
    node2 = SimpleNode("node2")

    graph.add_node(node1)
    graph.add_node(node2)
    graph.add_edge("node1", "node2")
    graph.add_edge("node2", "node1")  # Creates cycle

    executor = Executor()
    context = ExecutionContext()

    with pytest.raises(ValueError, match="Invalid graph"):
        await executor.execute(graph, context)

