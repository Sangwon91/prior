"""Tests for ExecutionContext."""

from workflow.state import ExecutionContext
from workflow.types import ExecutionResult, NodeState


def test_context_set_get():
    """Test setting and getting context values."""
    context = ExecutionContext()

    context.set("key1", "value1")
    context.set("key2", 42)

    assert context.get("key1") == "value1"
    assert context.get("key2") == 42
    assert context.get("missing") is None
    assert context.get("missing", "default") == "default"


def test_context_has():
    """Test checking if key exists."""
    context = ExecutionContext()

    assert not context.has("key1")

    context.set("key1", "value1")

    assert context.has("key1")
    assert not context.has("key2")


def test_context_initial_data():
    """Test context with initial data."""
    context = ExecutionContext({"key1": "value1", "key2": 42})

    assert context.get("key1") == "value1"
    assert context.get("key2") == 42


def test_context_results():
    """Test setting and getting execution results."""
    context = ExecutionContext()

    result1 = ExecutionResult("node1", NodeState.COMPLETED, output="output1")
    result2 = ExecutionResult("node2", NodeState.FAILED, error=ValueError("error"))

    context.set_result("node1", result1)
    context.set_result("node2", result2)

    assert context.get_result("node1") == result1
    assert context.get_result("node2") == result2
    assert context.get_result("node3") is None


def test_context_node_state():
    """Test getting node state."""
    context = ExecutionContext()

    assert context.get_node_state("node1") == NodeState.PENDING

    result = ExecutionResult("node1", NodeState.RUNNING)
    context.set_result("node1", result)

    assert context.get_node_state("node1") == NodeState.RUNNING


def test_context_node_output():
    """Test getting node output."""
    context = ExecutionContext()

    assert context.get_node_output("node1") is None

    result = ExecutionResult("node1", NodeState.COMPLETED, output="output1")
    context.set_result("node1", result)

    assert context.get_node_output("node1") == "output1"

