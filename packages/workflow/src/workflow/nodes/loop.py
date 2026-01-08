"""Loop node for iterative workflows."""

from collections.abc import Callable
from typing import Any

from ..node import Node
from ..state import ExecutionContext


class LoopNode(Node):
    """Node that loops until condition is met."""

    def __init__(
        self,
        node_id: str,
        body_node_id: str,
        condition: Callable[[ExecutionContext], bool],
        max_iterations: int = 100,
    ):
        """
        Initialize loop node.

        Args:
            node_id: Node identifier
            body_node_id: Node ID to execute in loop body
            condition: Function that returns True to continue looping
            max_iterations: Maximum number of iterations
        """
        super().__init__(node_id)
        self.body_node_id = body_node_id
        self.condition = condition
        self.max_iterations = max_iterations

    async def execute(self, context: ExecutionContext) -> Any:
        """
        Execute loop logic.

        Args:
            context: Execution context

        Returns:
            Number of iterations performed
        """
        iteration_count = 0
        context.set(f"{self.id}_iteration", 0)

        while self.condition(context) and iteration_count < self.max_iterations:
            iteration_count += 1
            context.set(f"{self.id}_iteration", iteration_count)
            # Note: Actual body execution would be handled by executor
            # This node just tracks iteration state

        context.set(f"{self.id}_final_iteration", iteration_count)
        return iteration_count

