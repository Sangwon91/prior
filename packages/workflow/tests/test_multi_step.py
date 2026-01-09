"""Tests for multi-step workflows."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from workflow import BaseNode, End, Graph, GraphRunContext


@dataclass
class MultiStepState:
    """Test state for multi-step workflow tests."""

    step: int = 0
    total: int = 0
    history: list[str] = None
    processed_items: list[int] = None

    def __post_init__(self):
        if self.history is None:
            self.history = []
        if self.processed_items is None:
            self.processed_items = []


@dataclass
class Step1Node(BaseNode[MultiStepState, None, str]):
    """First step in multi-step workflow."""

    async def run(
        self, ctx: GraphRunContext[MultiStepState]
    ) -> Step2Node | End[str]:
        ctx.state.step = 1
        ctx.state.history.append("step1")
        ctx.state.total += 10
        return Step2Node()


@dataclass
class Step2Node(BaseNode[MultiStepState, None, str]):
    """Second step in multi-step workflow."""

    async def run(
        self, ctx: GraphRunContext[MultiStepState]
    ) -> Step3Node | End[str]:
        ctx.state.step = 2
        ctx.state.history.append("step2")
        ctx.state.total += 20
        return Step3Node()


@dataclass
class Step3Node(BaseNode[MultiStepState, None, str]):
    """Third step in multi-step workflow."""

    async def run(self, ctx: GraphRunContext[MultiStepState]) -> End[str]:
        ctx.state.step = 3
        ctx.state.history.append("step3")
        ctx.state.total += 30
        return End(f"completed_total_{ctx.state.total}")


@dataclass
class ProcessNode(BaseNode[MultiStepState, None, int]):
    """Node that processes an item."""

    item: int

    async def run(
        self, ctx: GraphRunContext[MultiStepState]
    ) -> AggregateNode | End[int]:
        ctx.state.processed_items.append(self.item)
        ctx.state.total += self.item
        return AggregateNode()


@dataclass
class AggregateNode(BaseNode[MultiStepState, None, int]):
    """Node that aggregates results."""

    async def run(self, ctx: GraphRunContext[MultiStepState]) -> End[int]:
        return End(sum(ctx.state.processed_items))


@dataclass
class InitNode(BaseNode[MultiStepState, None, int]):
    """Initialization node."""

    async def run(
        self, ctx: GraphRunContext[MultiStepState]
    ) -> ProcessNode | End[int]:
        ctx.state.history.append("init")
        return ProcessNode(item=5)


@dataclass
class ConditionalStepNode(BaseNode[MultiStepState, None, str]):
    """Node that conditionally goes to next step."""

    target_step: int

    async def run(
        self, ctx: GraphRunContext[MultiStepState]
    ) -> ConditionalStepNode | End[str]:
        ctx.state.step += 1
        ctx.state.history.append(f"conditional_step_{ctx.state.step}")

        if ctx.state.step < self.target_step:
            return ConditionalStepNode(target_step=self.target_step)
        return End(f"reached_step_{ctx.state.step}")


@pytest.mark.asyncio
async def test_three_step_workflow():
    """Test a simple three-step workflow."""
    state = MultiStepState()

    graph = Graph(nodes=(Step1Node, Step2Node, Step3Node))
    result = await graph.run(Step1Node(), state=state)

    assert result.output == "completed_total_60"
    assert result.state.step == 3
    assert result.state.total == 60
    assert result.state.history == ["step1", "step2", "step3"]


@pytest.mark.asyncio
async def test_multi_step_with_processing():
    """Test multi-step workflow with data processing."""
    state = MultiStepState()

    graph = Graph(nodes=(InitNode, ProcessNode, AggregateNode))
    result = await graph.run(InitNode(), state=state)

    assert result.output == 5
    assert len(result.state.processed_items) == 1
    assert result.state.processed_items[0] == 5
    assert result.state.total == 5
    assert "init" in result.state.history


@pytest.mark.asyncio
async def test_conditional_multi_step():
    """Test conditional multi-step workflow."""
    state = MultiStepState()

    graph = Graph(nodes=(ConditionalStepNode,))
    result = await graph.run(ConditionalStepNode(target_step=5), state=state)

    assert result.output == "reached_step_5"
    assert result.state.step == 5
    assert len(result.state.history) == 5
    assert all(
        f"conditional_step_{i + 1}" in result.state.history for i in range(5)
    )


@pytest.mark.asyncio
async def test_long_chain_workflow():
    """Test a longer chain of steps."""

    @dataclass
    class ChainNode(BaseNode[MultiStepState, None, int]):
        step_num: int
        max_steps: int

        async def run(
            self, ctx: GraphRunContext[MultiStepState]
        ) -> ChainNode | End[int]:
            ctx.state.step = self.step_num
            ctx.state.history.append(f"chain_{self.step_num}")
            ctx.state.total += self.step_num

            if self.step_num >= self.max_steps:
                return End(ctx.state.total)
            return ChainNode(
                step_num=self.step_num + 1, max_steps=self.max_steps
            )

    state = MultiStepState()
    graph = Graph(nodes=(ChainNode,))
    result = await graph.run(ChainNode(step_num=1, max_steps=10), state=state)

    assert result.output == sum(range(1, 11))  # 55
    assert result.state.step == 10
    assert len(result.state.history) == 10


@pytest.mark.asyncio
async def test_multi_step_state_accumulation():
    """Test that state accumulates correctly through multiple steps."""

    @dataclass
    class AccumulateNode(BaseNode[MultiStepState, None, int]):
        value: int
        next_value: int | None = None

        async def run(
            self, ctx: GraphRunContext[MultiStepState]
        ) -> AccumulateNode | End[int]:
            ctx.state.total += self.value
            ctx.state.processed_items.append(self.value)

            if self.next_value is None:
                return End(ctx.state.total)
            return AccumulateNode(value=self.next_value, next_value=None)

    state = MultiStepState()
    graph = Graph(nodes=(AccumulateNode,))
    result = await graph.run(AccumulateNode(value=1, next_value=2), state=state)

    assert result.output == 3
    assert result.state.total == 3
    assert result.state.processed_items == [1, 2]


@pytest.mark.asyncio
async def test_branching_multi_step():
    """Test multi-step workflow with branching."""

    @dataclass
    class BranchNode(BaseNode[MultiStepState, None, str]):
        async def run(
            self, ctx: GraphRunContext[MultiStepState]
        ) -> BranchANode | BranchBNode:
            if ctx.state.total % 2 == 0:
                return BranchANode()
            return BranchBNode()

    @dataclass
    class BranchANode(BaseNode[MultiStepState, None, str]):
        async def run(self, ctx: GraphRunContext[MultiStepState]) -> End[str]:
            ctx.state.history.append("branch_a")
            ctx.state.total += 100
            return End("branch_a_complete")

    @dataclass
    class BranchBNode(BaseNode[MultiStepState, None, str]):
        async def run(self, ctx: GraphRunContext[MultiStepState]) -> End[str]:
            ctx.state.history.append("branch_b")
            ctx.state.total += 200
            return End("branch_b_complete")

    state = MultiStepState(total=0)  # Even, should go to branch A
    graph = Graph(nodes=(BranchNode, BranchANode, BranchBNode))
    result = await graph.run(BranchNode(), state=state)

    assert result.output == "branch_a_complete"
    assert "branch_a" in result.state.history
    assert result.state.total == 100

    # Test branch B
    state2 = MultiStepState(total=1)  # Odd, should go to branch B
    result2 = await graph.run(BranchNode(), state=state2)

    assert result2.output == "branch_b_complete"
    assert "branch_b" in result2.state.history
    assert result2.state.total == 201
