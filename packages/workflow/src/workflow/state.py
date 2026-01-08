"""State management for workflow execution."""

from typing import Any

from .types import ExecutionResult, NodeState


class ExecutionContext:
    """Context for workflow execution."""

    def __init__(self, initial_data: dict[str, Any] | None = None):
        """
        Initialize execution context.

        Args:
            initial_data: Initial context data
        """
        self._data: dict[str, Any] = initial_data or {}
        self._results: dict[str, ExecutionResult] = {}

    def set(self, key: str, value: Any) -> None:
        """
        Set a value in the context.

        Args:
            key: Key name
            value: Value to set
        """
        self._data[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a value from the context.

        Args:
            key: Key name
            default: Default value if key not found

        Returns:
            Value or default
        """
        return self._data.get(key, default)

    def has(self, key: str) -> bool:
        """
        Check if key exists in context.

        Args:
            key: Key name

        Returns:
            True if key exists
        """
        return key in self._data

    def set_result(self, node_id: str, result: ExecutionResult) -> None:
        """
        Set execution result for a node.

        Args:
            node_id: Node identifier
            result: Execution result
        """
        self._results[node_id] = result

    def get_result(self, node_id: str) -> ExecutionResult | None:
        """
        Get execution result for a node.

        Args:
            node_id: Node identifier

        Returns:
            Execution result or None
        """
        return self._results.get(node_id)

    def get_node_state(self, node_id: str) -> NodeState:
        """
        Get state of a node.

        Args:
            node_id: Node identifier

        Returns:
            Node state
        """
        result = self.get_result(node_id)
        if result is None:
            return NodeState.PENDING
        return result.state

    def get_node_output(self, node_id: str) -> Any:
        """
        Get output of a node.

        Args:
            node_id: Node identifier

        Returns:
            Node output or None
        """
        result = self.get_result(node_id)
        if result is None:
            return None
        return result.output

