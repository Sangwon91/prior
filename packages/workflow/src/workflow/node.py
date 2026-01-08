"""Node base class for workflow execution."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generic, TypeVar

from typing_extensions import Never

from .state import DepsT, GraphRunContext, StateT

RunEndT = TypeVar("RunEndT")


@dataclass
class End(Generic[RunEndT]):
    """End node to indicate the graph run should end."""

    data: RunEndT | None = None


@dataclass
class BaseNode(ABC, Generic[StateT, DepsT, RunEndT]):
    """Base class for workflow nodes, similar to pydantic_graph's BaseNode."""

    async def validate(self, ctx: GraphRunContext[StateT, DepsT]) -> bool:
        """
        Validate if node can be executed.

        Args:
            ctx: Graph run context

        Returns:
            True if node can be executed
        """
        return True

    @abstractmethod
    async def run(
        self, ctx: GraphRunContext[StateT, DepsT]
    ) -> BaseNode[StateT, DepsT, RunEndT] | End[RunEndT]:
        """
        Execute the node and return the next node to run.

        Args:
            ctx: Graph run context

        Returns:
            Next node to execute or End node to terminate execution
        """
        ...

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"
