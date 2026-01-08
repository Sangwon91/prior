"""Tests for Graph class."""

import pytest

from workflow.graph import Graph
from workflow.node import Node


class MockNode(Node):
    """Mock node implementation for testing."""

    def __init__(self, node_id: str, output: str = "test"):
        super().__init__(node_id)
        self.output = output

    async def execute(self, context):
        return self.output


def test_add_node():
    """Test adding nodes to graph."""
    graph = Graph()
    node = MockNode("node1")

    graph.add_node(node)

    assert graph.get_node("node1") == node
    assert len(graph.get_all_nodes()) == 1


def test_add_node_with_dependencies():
    """Test adding node with dependencies."""
    graph = Graph()
    node1 = MockNode("node1")
    node2 = MockNode("node2")

    graph.add_node(node1)
    graph.add_node(node2, dependencies=["node1"])

    deps = graph.get_dependencies("node2")
    assert "node1" in deps
    assert "node2" in graph.get_dependents("node1")


def test_add_node_missing_dependency():
    """Test adding node with missing dependency raises error."""
    graph = Graph()
    node = MockNode("node1")

    graph.add_node(node)

    node2 = MockNode("node2")
    with pytest.raises(ValueError, match="Dependency.*not found"):
        graph.add_node(node2, dependencies=["missing"])


def test_add_edge():
    """Test adding edge between nodes."""
    graph = Graph()
    node1 = MockNode("node1")
    node2 = MockNode("node2")

    graph.add_node(node1)
    graph.add_node(node2)
    graph.add_edge("node1", "node2")

    assert "node1" in graph.get_dependencies("node2")
    assert "node2" in graph.get_dependents("node1")


def test_validate_acyclic_graph():
    """Test validation of acyclic graph."""
    graph = Graph()
    node1 = MockNode("node1")
    node2 = MockNode("node2")
    node3 = MockNode("node3")

    graph.add_node(node1)
    graph.add_node(node2, dependencies=["node1"])
    graph.add_node(node3, dependencies=["node2"])

    is_valid, error = graph.validate()
    assert is_valid
    assert error is None


def test_validate_cyclic_graph():
    """Test validation detects cycles."""
    graph = Graph()
    node1 = MockNode("node1")
    node2 = MockNode("node2")

    graph.add_node(node1)
    graph.add_node(node2)
    graph.add_edge("node1", "node2")
    graph.add_edge("node2", "node1")  # Creates cycle

    is_valid, error = graph.validate()
    assert not is_valid
    assert error is not None
    assert "Cycle" in error


def test_get_execution_order():
    """Test getting execution order."""
    graph = Graph()
    node1 = MockNode("node1")
    node2 = MockNode("node2")
    node3 = MockNode("node3")

    graph.add_node(node1)
    graph.add_node(node2, dependencies=["node1"])
    graph.add_node(node3, dependencies=["node1"])

    order = graph.get_execution_order()

    # First layer should have node1
    assert "node1" in order[0]
    # Second layer should have node2 and node3 (can run in parallel)
    assert "node2" in order[1]
    assert "node3" in order[1]


def test_get_execution_order_raises_on_cycle():
    """Test execution order raises error on cycle."""
    graph = Graph()
    node1 = MockNode("node1")
    node2 = MockNode("node2")

    graph.add_node(node1)
    graph.add_node(node2)
    graph.add_edge("node1", "node2")
    graph.add_edge("node2", "node1")

    with pytest.raises(ValueError, match="cycles"):
        graph.get_execution_order()

