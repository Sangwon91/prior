"""Tests for GraphRunContext."""

from dataclasses import dataclass

from workflow import GraphRunContext


@dataclass
class TestState:
    """Test state."""

    value: int = 0
    name: str = ""


def test_graph_run_context_provides_access_to_state():
    """Test GraphRunContext provides access to state."""
    state = TestState(value=42, name="test")
    ctx = GraphRunContext(state=state)

    assert ctx.state.value == 42
    assert ctx.state.name == "test"


def test_graph_run_context_provides_access_to_deps():
    """Test GraphRunContext provides access to dependencies."""
    state = TestState()
    deps = {"service": "test_service"}

    ctx = GraphRunContext(state=state, deps=deps)

    assert ctx.deps == deps


def test_graph_run_context_allows_none_deps():
    """Test GraphRunContext allows None for dependencies."""
    state = TestState()
    ctx = GraphRunContext(state=state)

    assert ctx.deps is None
