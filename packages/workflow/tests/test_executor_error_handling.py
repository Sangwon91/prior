"""Tests for graph error handling."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from workflow import BaseNode, End, Graph, GraphRunContext


@dataclass
class TestState:
    """Test state."""

    value: int = 0


@dataclass
class FailingNode(BaseNode[TestState, None, str]):
    """Node that always fails."""

    async def run(self, ctx: GraphRunContext[TestState]) -> End[str]:
        raise ValueError("Node failed")


@dataclass
class SimpleNode(BaseNode[TestState, None, str]):
    """Simple test node."""

    output: str = "output"

    async def run(self, ctx: GraphRunContext[TestState]) -> End[str]:
        return End(self.output)


@pytest.mark.asyncio
async def test_graph_raises_on_error():
    """Test graph raises exception on node failure."""
    graph = Graph(nodes=(FailingNode,))
    state = TestState()

    with pytest.raises(ValueError, match="Node failed"):
        await graph.run(FailingNode(), state=state)
