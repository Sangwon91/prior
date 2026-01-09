"""Type definitions for workflow engine."""

from enum import Enum
from typing import Any


class NodeState(str, Enum):
    """Node execution state."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class ExecutionResult:
    """Result of node execution."""

    def __init__(
        self,
        node_id: str,
        state: NodeState,
        output: Any = None,
        error: Exception | None = None,
    ):
        """
        Initialize execution result.

        Args:
            node_id: Node identifier
            state: Execution state
            output: Output data
            error: Error if execution failed
        """
        self.node_id = node_id
        self.state = state
        self.output = output
        self.error = error

    def __repr__(self) -> str:
        return f"ExecutionResult(node_id={self.node_id!r}, state={self.state.value}, error={self.error})"
