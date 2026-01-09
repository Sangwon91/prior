"""Graph definition for workflow execution."""

from __future__ import annotations

from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Generic, TypeVar

from .node import BaseNode, End
from .state import DepsT, GraphRunContext, StateT

RunEndT = TypeVar("RunEndT")


@dataclass
class GraphRunResult(Generic[StateT, RunEndT]):
    """The final result of running a graph."""

    output: RunEndT | None
    state: StateT


class GraphRun(Generic[StateT, DepsT, RunEndT]):
    """Context manager for iterating through graph execution."""

    def __init__(
        self,
        graph: Graph[StateT, DepsT, RunEndT],
        start_node: BaseNode[StateT, DepsT, RunEndT],
        state: StateT,
        deps: DepsT | None = None,
    ):
        self.graph = graph
        self.state = state
        self.deps = deps
        self._next_node: BaseNode[StateT, DepsT, RunEndT] | End[RunEndT] = start_node
        self._is_started = False
        self.result: GraphRunResult[StateT, RunEndT] | None = None

    async def __aenter__(self) -> GraphRun[StateT, DepsT, RunEndT]:
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        pass

    def __aiter__(self) -> AsyncIterator[BaseNode[StateT, DepsT, RunEndT] | End[RunEndT]]:
        return self

    async def __anext__(
        self,
    ) -> BaseNode[StateT, DepsT, RunEndT] | End[RunEndT]:
        """Use the last returned node as the input to next."""
        if not self._is_started:
            self._is_started = True
            return self._next_node

        if isinstance(self._next_node, End):
            raise StopAsyncIteration

        return await self.next(self._next_node)

    async def next(
        self, node: BaseNode[StateT, DepsT, RunEndT] | None = None
    ) -> BaseNode[StateT, DepsT, RunEndT] | End[RunEndT]:
        """
        Manually drive the graph run by passing in the node you want to run next.

        Args:
            node: The node to run next in the graph. If not specified, uses self._next_node.

        Returns:
            The next node returned by the graph logic, or an End node if the run has completed.
        """
        if node is None:
            if isinstance(self._next_node, End):
                return self._next_node
            node = self._next_node

        if not isinstance(node, BaseNode):
            raise TypeError(f"`next` must be called with a `BaseNode` instance, got {node!r}.")

        # Check if node is in graph
        node_class = type(node)
        if node_class not in self.graph.node_defs:
            raise ValueError(f"Node `{node}` is not in the graph.")

        # Execute node
        ctx = GraphRunContext(state=self.state, deps=self.deps)
        self._next_node = await node.run(ctx)

        # Update state from context
        self.state = ctx.state

        # If we got an End node, store the result
        if isinstance(self._next_node, End):
            self.result = GraphRunResult(
                output=self._next_node.data,
                state=self.state,
            )

        return self._next_node


@dataclass
class Graph(Generic[StateT, DepsT, RunEndT]):
    """Workflow graph with nodes, similar to pydantic_graph's Graph."""

    node_defs: dict[type[BaseNode[StateT, DepsT, RunEndT]], None] = field(default_factory=dict)
    name: str | None = None

    def __init__(
        self,
        *,
        nodes: Sequence[type[BaseNode[StateT, DepsT, RunEndT]]],
        name: str | None = None,
    ):
        """
        Create a graph from a sequence of node classes.

        Args:
            nodes: The node classes which make up the graph
            name: Optional name for the graph
        """
        self.name = name
        self.node_defs = {node_class: None for node_class in nodes}
        self._validate_edges()

    def _validate_edges(self) -> None:
        """Validate that all node return types are valid."""
        for node_class in self.node_defs:
            # Check that run method exists and has proper return type
            if not hasattr(node_class, "run"):
                raise ValueError(f"Node {node_class} must have a `run` method")
            # Type checking would be done by type checkers, not at runtime

    @asynccontextmanager
    async def iter(
        self,
        start_node: BaseNode[StateT, DepsT, RunEndT],
        *,
        state: StateT,
        deps: DepsT | None = None,
    ) -> AsyncIterator[GraphRun[StateT, DepsT, RunEndT]]:
        """
        Iterate through graph execution.

        Args:
            start_node: The first node to run
            state: The initial state of the graph
            deps: The dependencies of the graph

        Yields:
            GraphRun context manager for iterating through nodes
        """
        run = GraphRun(self, start_node, state, deps)
        async with run:
            yield run

    async def run(
        self,
        start_node: BaseNode[StateT, DepsT, RunEndT],
        *,
        state: StateT,
        deps: DepsT | None = None,
    ) -> GraphRunResult[StateT, RunEndT]:
        """
        Run the graph from a starting node until it ends.

        Args:
            start_node: The first node to run
            state: The initial state of the graph
            deps: The dependencies of the graph

        Returns:
            A GraphRunResult containing the final result and state
        """
        async with self.iter(start_node, state=state, deps=deps) as graph_run:
            async for _node in graph_run:
                pass

        if graph_run.result is None:
            raise RuntimeError("Graph run did not end with an End node")

        return graph_run.result

    def run_sync(
        self,
        start_node: BaseNode[StateT, DepsT, RunEndT],
        *,
        state: StateT,
        deps: DepsT | None = None,
    ) -> GraphRunResult[StateT, RunEndT]:
        """
        Synchronously run the graph.

        Args:
            start_node: The first node to run
            state: The initial state of the graph
            deps: The dependencies of the graph

        Returns:
            The result of running the graph
        """
        import asyncio

        try:
            loop = asyncio.get_running_loop()
            # If we're already in an event loop, we can't use run_until_complete
            # Instead, we need to use a different approach
            # For now, raise an error suggesting to use async run() instead
            raise RuntimeError(
                "Cannot use run_sync() within an async context. "
                "Use await graph.run() instead."
            )
        except RuntimeError:
            # No running loop, create a new one
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    raise RuntimeError(
                        "Cannot use run_sync() within an async context. "
                        "Use await graph.run() instead."
                    )
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

        return loop.run_until_complete(self.run(start_node, state=state, deps=deps))
