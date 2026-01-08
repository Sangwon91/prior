"""Conditional node for branching workflows."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Generic, TypeVar

from ..node import BaseNode, End
from ..state import DepsT, GraphRunContext, StateT

RunEndT = TypeVar("RunEndT")


@dataclass
class ConditionalNode(BaseNode[StateT, DepsT, RunEndT], Generic[StateT, DepsT, RunEndT]):
    """Node that conditionally branches based on context state."""

    condition: Callable[[GraphRunContext[StateT, DepsT]], bool]
    true_node: BaseNode[StateT, DepsT, RunEndT] | End[RunEndT]
    false_node: BaseNode[StateT, DepsT, RunEndT] | End[RunEndT]

    async def run(
        self, ctx: GraphRunContext[StateT, DepsT]
    ) -> BaseNode[StateT, DepsT, RunEndT] | End[RunEndT]:
        """
        Execute conditional logic and return the appropriate next node.

        Args:
            ctx: Graph run context

        Returns:
            Next node based on condition evaluation
        """
        if self.condition(ctx):
            return self.true_node
        else:
            return self.false_node
