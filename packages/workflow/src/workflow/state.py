"""State management for workflow execution."""

from dataclasses import dataclass
from typing import Generic, TypeVar

StateT = TypeVar("StateT")
DepsT = TypeVar("DepsT")


@dataclass
class GraphRunContext(Generic[StateT, DepsT]):
    """Context for graph execution, similar to pydantic_graph's GraphRunContext."""

    state: StateT
    deps: DepsT | None = None
