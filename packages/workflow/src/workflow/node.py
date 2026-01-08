"""Node base class for workflow execution."""

from abc import ABC, abstractmethod
from typing import Any

from .state import ExecutionContext


class Node(ABC):
    """Base class for workflow nodes."""

    def __init__(self, node_id: str):
        """
        Initialize node.

        Args:
            node_id: Unique node identifier
        """
        self.id = node_id

    @abstractmethod
    async def execute(self, context: ExecutionContext) -> Any:
        """
        Execute the node.

        Args:
            context: Execution context

        Returns:
            Output data
        """
        ...

    async def validate(self, context: ExecutionContext) -> bool:
        """
        Validate if node can be executed.

        Args:
            context: Execution context

        Returns:
            True if node can be executed
        """
        return True

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.id!r})"

