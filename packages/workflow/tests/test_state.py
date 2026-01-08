"""Tests for GraphRunContext."""

from dataclasses import dataclass

from workflow import GraphRunContext


@dataclass
class TestState:
    """Test state."""

    value: int = 0
    name: str = ""


def test_context_state():
    """Test GraphRunContext state access."""
    state = TestState(value=42, name="test")
    ctx = GraphRunContext(state=state)

    assert ctx.state.value == 42
    assert ctx.state.name == "test"


def test_context_deps():
    """Test GraphRunContext deps."""
    state = TestState()
    deps = {"service": "test_service"}

    ctx = GraphRunContext(state=state, deps=deps)

    assert ctx.deps == deps


def test_context_deps_none():
    """Test GraphRunContext with no deps."""
    state = TestState()
    ctx = GraphRunContext(state=state)

    assert ctx.deps is None
