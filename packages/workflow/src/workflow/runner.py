"""Workflow execution and lifecycle management."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import TYPE_CHECKING, Generic, TypeVar

from .graph import Graph, GraphRunResult
from .node import BaseNode

if TYPE_CHECKING:
    from adapter import AdapterClient

StateT = TypeVar("StateT")
DepsT = TypeVar("DepsT")
RunEndT = TypeVar("RunEndT")


class WorkflowRunner(Generic[StateT, DepsT, RunEndT]):
    """Workflow execution and lifecycle management."""

    async def run_once(
        self,
        graph: Graph[StateT, DepsT, RunEndT],
        start_node: BaseNode[StateT, DepsT, RunEndT],
        state: StateT,
        deps: DepsT | None = None,
        adapter: "AdapterClient | None" = None,
    ) -> GraphRunResult[StateT, RunEndT]:
        """
        Execute workflow once.

        Args:
            graph: Workflow graph to execute
            start_node: Starting node for the workflow
            state: Initial state
            deps: Optional dependencies
            adapter: Optional adapter client for communication

        Returns:
            GraphRunResult containing output and final state
        """
        return await graph.run(
            start_node, state=state, deps=deps, adapter=adapter
        )

    async def run_loop(
        self,
        graph: Graph[StateT, DepsT, RunEndT],
        start_node: BaseNode[StateT, DepsT, RunEndT],
        state_factory: Callable[[], StateT],
        deps: DepsT | None = None,
        adapter: "AdapterClient | None" = None,
        on_error: Callable[[Exception], None] | None = None,
    ) -> None:
        """
        Execute workflow in a loop with error recovery.

        Continuously executes the workflow, restarting on errors.
        Cancellation is propagated to allow graceful shutdown.

        Args:
            graph: Workflow graph to execute
            start_node: Starting node for the workflow
            state_factory: Factory function to create initial state
            deps: Optional dependencies
            adapter: Optional adapter client for communication
            on_error: Optional error handler callback
        """
        while True:
            try:
                state = state_factory()
                result = await graph.run(
                    start_node, state=state, deps=deps, adapter=adapter
                )
                # If workflow ended, break
                if result.output is not None:
                    break
            except asyncio.CancelledError:
                # Allow cancellation to propagate
                raise
            except Exception as e:
                # On error, continue listening
                if on_error:
                    on_error(e)
                continue
