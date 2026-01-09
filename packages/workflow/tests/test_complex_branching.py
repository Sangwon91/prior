"""Tests for complex branching patterns in workflows."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from workflow import BaseNode, End, Graph, GraphRunContext


@dataclass
class BranchingState:
    """Test state for complex branching tests."""

    value: int = 0
    path: list[str] = None
    flags: dict[str, bool] = None

    def __post_init__(self):
        if self.path is None:
            self.path = []
        if self.flags is None:
            self.flags = {}


@dataclass
class MultiConditionNode(BaseNode[BranchingState, None, str]):
    """Node with multiple conditional branches."""

    async def run(
        self, ctx: GraphRunContext[BranchingState]
    ) -> BranchANode | BranchBNode | BranchCNode | End[str]:
        if ctx.state.value < 0:
            return BranchANode()
        elif ctx.state.value == 0:
            return BranchBNode()
        elif ctx.state.value > 10:
            return BranchCNode()
        else:
            return End("default")


@dataclass
class BranchANode(BaseNode[BranchingState, None, str]):
    """Branch A node."""

    async def run(self, ctx: GraphRunContext[BranchingState]) -> End[str]:
        ctx.state.path.append("A")
        return End("branch_a")


@dataclass
class BranchBNode(BaseNode[BranchingState, None, str]):
    """Branch B node."""

    async def run(self, ctx: GraphRunContext[BranchingState]) -> End[str]:
        ctx.state.path.append("B")
        return End("branch_b")


@dataclass
class BranchCNode(BaseNode[BranchingState, None, str]):
    """Branch C node."""

    async def run(self, ctx: GraphRunContext[BranchingState]) -> End[str]:
        ctx.state.path.append("C")
        return End("branch_c")


@dataclass
class NestedBranchNode(BaseNode[BranchingState, None, str]):
    """Node that creates nested branching."""

    level: int = 0

    async def run(
        self, ctx: GraphRunContext[BranchingState]
    ) -> NestedBranchNode | EndNode | End[str]:
        ctx.state.path.append(f"level_{self.level}")

        if self.level >= 3:
            return EndNode()
        elif ctx.state.value % 2 == 0:
            return NestedBranchNode(level=self.level + 1)
        else:
            return EndNode()


@dataclass
class EndNode(BaseNode[BranchingState, None, str]):
    """End node for nested branching."""

    async def run(self, ctx: GraphRunContext[BranchingState]) -> End[str]:
        ctx.state.path.append("end")
        return End("nested_complete")


@dataclass
class ConvergeNodeA(BaseNode[BranchingState, None, str]):
    """First branch that converges."""

    async def run(
        self, ctx: GraphRunContext[BranchingState]
    ) -> ConvergeNode | End[str]:
        ctx.state.path.append("branch_a")
        ctx.state.value += 10
        return ConvergeNode()


@dataclass
class ConvergeNodeB(BaseNode[BranchingState, None, str]):
    """Second branch that converges."""

    async def run(
        self, ctx: GraphRunContext[BranchingState]
    ) -> ConvergeNode | End[str]:
        ctx.state.path.append("branch_b")
        ctx.state.value += 20
        return ConvergeNode()


@dataclass
class ConvergeNode(BaseNode[BranchingState, None, str]):
    """Node where branches converge."""

    async def run(self, ctx: GraphRunContext[BranchingState]) -> End[str]:
        ctx.state.path.append("converge")
        return End(f"converged_value_{ctx.state.value}")


@dataclass
class DecisionNode(BaseNode[BranchingState, None, str]):
    """Node that decides which branch to take."""

    async def run(
        self, ctx: GraphRunContext[BranchingState]
    ) -> ConvergeNodeA | ConvergeNodeB:
        if ctx.state.value < 5:
            return ConvergeNodeA()
        return ConvergeNodeB()


@dataclass
class FlagBasedNode(BaseNode[BranchingState, None, str]):
    """Node that branches based on multiple flags."""

    async def run(
        self, ctx: GraphRunContext[BranchingState]
    ) -> FlagNode1 | FlagNode2 | FlagNode3 | End[str]:
        flag1 = ctx.state.flags.get("flag1", False)
        flag2 = ctx.state.flags.get("flag2", False)

        if flag1 and flag2:
            return FlagNode1()
        elif flag1:
            return FlagNode2()
        elif flag2:
            return FlagNode3()
        else:
            return End("no_flags")


@dataclass
class FlagNode1(BaseNode[BranchingState, None, str]):
    """Flag node 1."""

    async def run(self, ctx: GraphRunContext[BranchingState]) -> End[str]:
        ctx.state.path.append("flag1")
        return End("both_flags")


@dataclass
class FlagNode2(BaseNode[BranchingState, None, str]):
    """Flag node 2."""

    async def run(self, ctx: GraphRunContext[BranchingState]) -> End[str]:
        ctx.state.path.append("flag2")
        return End("flag1_only")


@dataclass
class FlagNode3(BaseNode[BranchingState, None, str]):
    """Flag node 3."""

    async def run(self, ctx: GraphRunContext[BranchingState]) -> End[str]:
        ctx.state.path.append("flag3")
        return End("flag2_only")


@pytest.mark.asyncio
async def test_multi_condition_branching():
    """Test branching with multiple conditions."""
    graph = Graph(
        nodes=(MultiConditionNode, BranchANode, BranchBNode, BranchCNode)
    )

    # Test branch A (value < 0)
    state_a = BranchingState(value=-5)
    result_a = await graph.run(MultiConditionNode(), state=state_a)
    assert result_a.output == "branch_a"
    assert "A" in result_a.state.path

    # Test branch B (value == 0)
    state_b = BranchingState(value=0)
    result_b = await graph.run(MultiConditionNode(), state=state_b)
    assert result_b.output == "branch_b"
    assert "B" in result_b.state.path

    # Test branch C (value > 10)
    state_c = BranchingState(value=15)
    result_c = await graph.run(MultiConditionNode(), state=state_c)
    assert result_c.output == "branch_c"
    assert "C" in result_c.state.path

    # Test default (0 < value <= 10)
    state_d = BranchingState(value=5)
    result_d = await graph.run(MultiConditionNode(), state=state_d)
    assert result_d.output == "default"


@pytest.mark.asyncio
async def test_nested_branching():
    """Test nested branching pattern."""
    state = BranchingState(value=0)  # Even, so will branch

    graph = Graph(nodes=(NestedBranchNode, EndNode))
    result = await graph.run(NestedBranchNode(level=0), state=state)

    assert result.output == "nested_complete"
    assert "end" in result.state.path
    # Should have multiple levels
    assert any("level_" in step for step in result.state.path)


@pytest.mark.asyncio
async def test_converging_branches():
    """Test multiple branches that converge to same node."""
    graph = Graph(
        nodes=(DecisionNode, ConvergeNodeA, ConvergeNodeB, ConvergeNode)
    )

    # Test branch A convergence
    state_a = BranchingState(value=3)
    result_a = await graph.run(DecisionNode(), state=state_a)
    assert result_a.output == "converged_value_13"  # 3 + 10
    assert "branch_a" in result_a.state.path
    assert "converge" in result_a.state.path

    # Test branch B convergence
    state_b = BranchingState(value=10)
    result_b = await graph.run(DecisionNode(), state=state_b)
    assert result_b.output == "converged_value_30"  # 10 + 20
    assert "branch_b" in result_b.state.path
    assert "converge" in result_b.state.path


@pytest.mark.asyncio
async def test_flag_based_branching():
    """Test branching based on multiple flags."""
    graph = Graph(nodes=(FlagBasedNode, FlagNode1, FlagNode2, FlagNode3))

    # Test both flags
    state_both = BranchingState(flags={"flag1": True, "flag2": True})
    result_both = await graph.run(FlagBasedNode(), state=state_both)
    assert result_both.output == "both_flags"
    assert "flag1" in result_both.state.path

    # Test flag1 only
    state_flag1 = BranchingState(flags={"flag1": True, "flag2": False})
    result_flag1 = await graph.run(FlagBasedNode(), state=state_flag1)
    assert result_flag1.output == "flag1_only"
    assert "flag2" in result_flag1.state.path

    # Test flag2 only
    state_flag2 = BranchingState(flags={"flag1": False, "flag2": True})
    result_flag2 = await graph.run(FlagBasedNode(), state=state_flag2)
    assert result_flag2.output == "flag2_only"
    assert "flag3" in result_flag2.state.path

    # Test no flags
    state_none = BranchingState(flags={})
    result_none = await graph.run(FlagBasedNode(), state=state_none)
    assert result_none.output == "no_flags"


@pytest.mark.asyncio
async def test_complex_decision_tree():
    """Test a complex decision tree with multiple levels."""

    @dataclass
    class Level1Node(BaseNode[BranchingState, None, str]):
        async def run(
            self, ctx: GraphRunContext[BranchingState]
        ) -> Level2ANode | Level2BNode:
            if ctx.state.value < 5:
                return Level2ANode()
            return Level2BNode()

    @dataclass
    class Level2ANode(BaseNode[BranchingState, None, str]):
        async def run(
            self, ctx: GraphRunContext[BranchingState]
        ) -> Level3ANode | Level3BNode:
            if ctx.state.value % 2 == 0:
                return Level3ANode()
            return Level3BNode()

    @dataclass
    class Level2BNode(BaseNode[BranchingState, None, str]):
        async def run(
            self, ctx: GraphRunContext[BranchingState]
        ) -> Level3CNode | End[str]:
            if ctx.state.value > 10:
                return Level3CNode()
            return End("level2b_end")

    @dataclass
    class Level3ANode(BaseNode[BranchingState, None, str]):
        async def run(self, ctx: GraphRunContext[BranchingState]) -> End[str]:
            ctx.state.path.append("L3A")
            return End("level3a")

    @dataclass
    class Level3BNode(BaseNode[BranchingState, None, str]):
        async def run(self, ctx: GraphRunContext[BranchingState]) -> End[str]:
            ctx.state.path.append("L3B")
            return End("level3b")

    @dataclass
    class Level3CNode(BaseNode[BranchingState, None, str]):
        async def run(self, ctx: GraphRunContext[BranchingState]) -> End[str]:
            ctx.state.path.append("L3C")
            return End("level3c")

    graph = Graph(
        nodes=(
            Level1Node,
            Level2ANode,
            Level2BNode,
            Level3ANode,
            Level3BNode,
            Level3CNode,
        )
    )

    # Test path: Level1 -> Level2A -> Level3A (value=2, even, < 5)
    state1 = BranchingState(value=2)
    result1 = await graph.run(Level1Node(), state=state1)
    assert result1.output == "level3a"
    assert "L3A" in result1.state.path

    # Test path: Level1 -> Level2A -> Level3B (value=3, odd, < 5)
    state2 = BranchingState(value=3)
    result2 = await graph.run(Level1Node(), state=state2)
    assert result2.output == "level3b"
    assert "L3B" in result2.state.path

    # Test path: Level1 -> Level2B -> End (value=8, >= 5, <= 10)
    state3 = BranchingState(value=8)
    result3 = await graph.run(Level1Node(), state=state3)
    assert result3.output == "level2b_end"

    # Test path: Level1 -> Level2B -> Level3C (value=15, >= 5, > 10)
    state4 = BranchingState(value=15)
    result4 = await graph.run(Level1Node(), state=state4)
    assert result4.output == "level3c"
    assert "L3C" in result4.state.path
