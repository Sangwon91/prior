"""Conditional node for branching workflows."""

from collections.abc import Callable
from typing import Any

from ..node import Node
from ..state import ExecutionContext


class ConditionalNode(Node):
    """Node that conditionally executes based on context."""

    def __init__(
        self,
        node_id: str,
        condition: Callable[[ExecutionContext], bool],
        true_node_id: str | None = None,
        false_node_id: str | None = None,
    ):
        """
        Initialize conditional node.

        Args:
            node_id: Node identifier
            condition: Function that evaluates condition from context
            true_node_id: Node ID to execute if condition is True
            false_node_id: Node ID to execute if condition is False
        """
        super().__init__(node_id)
        self.condition = condition
        self.true_node_id = true_node_id
        self.false_node_id = false_node_id

    async def execute(self, context: ExecutionContext) -> Any:
        """
        Execute conditional logic.

        Args:
            context: Execution context

        Returns:
            Boolean result of condition
        """
        result = self.condition(context)
        context.set(f"{self.id}_condition_result", result)
        context.set(f"{self.id}_next_node", self.true_node_id if result else self.false_node_id)
        return result

