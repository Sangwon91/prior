"""Tests for dependency injection in workflows."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from workflow import BaseNode, End, Graph, GraphRunContext


@dataclass
class DepsState:
    """Test state for dependency tests."""

    result: str = ""
    processed_data: list[str] = None

    def __post_init__(self):
        if self.processed_data is None:
            self.processed_data = []


@dataclass
class NodeWithDeps(BaseNode[DepsState, dict[str, str], str]):
    """Node that uses dependencies."""

    async def run(
        self, ctx: GraphRunContext[DepsState, dict[str, str]]
    ) -> End[str]:
        if ctx.deps:
            service_name = ctx.deps.get("service", "unknown")
            ctx.state.result = f"processed_by_{service_name}"
        else:
            ctx.state.result = "no_deps"
        return End(ctx.state.result)


@dataclass
class NodeWithDepsList(BaseNode[DepsState, list[str], str]):
    """Node that uses list dependencies."""

    async def run(
        self, ctx: GraphRunContext[DepsState, list[str]]
    ) -> End[str]:
        if ctx.deps:
            ctx.state.processed_data = ctx.deps.copy()
            return End(f"processed_{len(ctx.deps)}_items")
        return End("no_deps")


@dataclass
class NodeWithOptionalDeps(BaseNode[DepsState, dict | None, str]):
    """Node that handles optional dependencies."""

    async def run(
        self, ctx: GraphRunContext[DepsState, dict | None]
    ) -> End[str]:
        if ctx.deps is None:
            ctx.state.result = "deps_is_none"
        elif "key" in ctx.deps:
            ctx.state.result = f"found_{ctx.deps['key']}"
        else:
            ctx.state.result = "deps_empty"
        return End(ctx.state.result)


@dataclass
class NodeWithComplexDeps(BaseNode[DepsState, dict, str]):
    """Node that uses complex dependency structure."""

    async def run(
        self, ctx: GraphRunContext[DepsState, dict]
    ) -> End[str]:
        if ctx.deps:
            config = ctx.deps.get("config", {})
            api_key = config.get("api_key", "missing")
            timeout = ctx.deps.get("timeout", 0)
            ctx.state.result = f"api_key_{api_key}_timeout_{timeout}"
        return End(ctx.state.result)


@pytest.mark.asyncio
async def test_node_with_dict_deps():
    """Test node using dictionary dependencies."""
    state = DepsState()
    deps = {"service": "test_service"}

    graph = Graph(nodes=(NodeWithDeps,))
    result = await graph.run(NodeWithDeps(), state=state, deps=deps)

    assert result.output == "processed_by_test_service"
    assert result.state.result == "processed_by_test_service"


@pytest.mark.asyncio
async def test_node_with_no_deps():
    """Test node when deps is None."""
    state = DepsState()

    graph = Graph(nodes=(NodeWithDeps,))
    result = await graph.run(NodeWithDeps(), state=state, deps=None)

    assert result.output == "no_deps"
    assert result.state.result == "no_deps"


@pytest.mark.asyncio
async def test_node_with_list_deps():
    """Test node using list dependencies."""
    state = DepsState()
    deps = ["item1", "item2", "item3"]

    graph = Graph(nodes=(NodeWithDepsList,))
    result = await graph.run(NodeWithDepsList(), state=state, deps=deps)

    assert result.output == "processed_3_items"
    assert len(result.state.processed_data) == 3
    assert result.state.processed_data == ["item1", "item2", "item3"]


@pytest.mark.asyncio
async def test_node_with_optional_deps_none():
    """Test node handling None dependencies."""
    state = DepsState()

    graph = Graph(nodes=(NodeWithOptionalDeps,))
    result = await graph.run(NodeWithOptionalDeps(), state=state, deps=None)

    assert result.output == "deps_is_none"
    assert result.state.result == "deps_is_none"


@pytest.mark.asyncio
async def test_node_with_optional_deps_with_key():
    """Test node with optional deps that has key."""
    state = DepsState()
    deps = {"key": "value123"}

    graph = Graph(nodes=(NodeWithOptionalDeps,))
    result = await graph.run(NodeWithOptionalDeps(), state=state, deps=deps)

    assert result.output == "found_value123"
    assert result.state.result == "found_value123"


@pytest.mark.asyncio
async def test_node_with_optional_deps_empty():
    """Test node with optional deps that is empty dict."""
    state = DepsState()
    deps = {}

    graph = Graph(nodes=(NodeWithOptionalDeps,))
    result = await graph.run(NodeWithOptionalDeps(), state=state, deps=deps)

    assert result.output == "deps_empty"
    assert result.state.result == "deps_empty"


@pytest.mark.asyncio
async def test_node_with_complex_deps():
    """Test node using complex nested dependency structure."""
    state = DepsState()
    deps = {
        "config": {"api_key": "secret123"},
        "timeout": 30,
    }

    graph = Graph(nodes=(NodeWithComplexDeps,))
    result = await graph.run(NodeWithComplexDeps(), state=state, deps=deps)

    assert result.output == "api_key_secret123_timeout_30"
    assert result.state.result == "api_key_secret123_timeout_30"


@pytest.mark.asyncio
async def test_deps_passed_through_chain():
    """Test that deps are passed through a chain of nodes."""
    state = DepsState()
    deps = {"service": "chain_service"}

    @dataclass
    class FirstNode(BaseNode[DepsState, dict[str, str], str]):
        async def run(
            self, ctx: GraphRunContext[DepsState, dict[str, str]]
        ) -> SecondNode | End[str]:
            if ctx.deps:
                ctx.state.result += f"first_{ctx.deps.get('service', '')}_"
            return SecondNode()

    @dataclass
    class SecondNode(BaseNode[DepsState, dict[str, str], str]):
        async def run(
            self, ctx: GraphRunContext[DepsState, dict[str, str]]
        ) -> End[str]:
            if ctx.deps:
                ctx.state.result += f"second_{ctx.deps.get('service', '')}"
            return End(ctx.state.result)

    graph = Graph(nodes=(FirstNode, SecondNode))
    result = await graph.run(FirstNode(), state=state, deps=deps)

    assert "first_chain_service_" in result.output
    assert "second_chain_service" in result.output

