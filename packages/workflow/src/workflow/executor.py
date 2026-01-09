"""Workflow execution engine."""

from .graph import Graph
from .node import Node
from .scheduler import Scheduler
from .state import ExecutionContext
from .types import ExecutionResult, NodeState


class Executor:
    """Graph execution engine."""

    def __init__(
        self,
        max_parallel: int | None = None,
        continue_on_error: bool = False,
    ):
        """
        Initialize executor.

        Args:
            max_parallel: Maximum number of parallel node executions (None = unlimited)
            continue_on_error: If True, continue execution even when nodes fail
        """
        self.max_parallel = max_parallel
        self.continue_on_error = continue_on_error
        self.scheduler = Scheduler(max_parallel=max_parallel)

    async def execute(
        self, graph: Graph, context: ExecutionContext | None = None
    ) -> ExecutionContext:
        """
        Execute a workflow graph.

        Args:
            graph: Graph to execute
            context: Initial execution context

        Returns:
            Execution context with results
        """
        if context is None:
            context = ExecutionContext()

        # Validate graph
        is_valid, error_msg = graph.validate()
        if not is_valid:
            raise ValueError(f"Invalid graph: {error_msg}")

        # Get execution order
        execution_layers = graph.get_execution_order()

        # Execute each layer
        for layer in execution_layers:
            # Execute nodes in this layer (can be parallel)
            await self._execute_layer(graph, layer, context)

        return context

    async def _execute_layer(
        self, graph: Graph, layer: list[str], context: ExecutionContext
    ) -> None:
        """
        Execute a layer of nodes.

        Args:
            graph: Graph being executed
            layer: List of node IDs in this layer
            context: Execution context
        """
        tasks = []
        for node_id in layer:
            node = graph.get_node(node_id)
            if node is None:
                continue

            # Check if node can be executed
            if not await node.validate(context):
                context.set_result(
                    node_id,
                    ExecutionResult(node_id, NodeState.SKIPPED),
                )
                continue

            # Create execution task
            task = self._execute_node_safe(node, context)
            tasks.append(task)

        # Execute tasks (with parallelism control)
        if tasks:
            await self.scheduler.execute_tasks(tasks)

    async def _execute_node_safe(
        self, node: Node, context: ExecutionContext
    ) -> None:
        """
        Execute a single node with error handling.

        Args:
            node: Node to execute
            context: Execution context
        """
        try:
            await self._execute_node(node, context)
        except Exception:
            if not self.continue_on_error:
                raise

    async def _execute_node(
        self, node: Node, context: ExecutionContext
    ) -> None:
        """
        Execute a single node.

        Args:
            node: Node to execute
            context: Execution context
        """
        node_id = node.id

        # Mark as running
        context.set_result(
            node_id,
            ExecutionResult(node_id, NodeState.RUNNING),
        )

        try:
            # Execute node
            output = await node.execute(context)

            # Mark as completed
            context.set_result(
                node_id,
                ExecutionResult(node_id, NodeState.COMPLETED, output=output),
            )
        except Exception as e:
            # Mark as failed
            context.set_result(
                node_id,
                ExecutionResult(node_id, NodeState.FAILED, error=e),
            )
            # Re-raise to allow error handling strategies
            raise
