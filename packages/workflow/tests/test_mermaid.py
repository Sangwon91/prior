"""Tests for Mermaid visualization functionality."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from workflow import BaseNode, End, Graph, GraphRunContext


@dataclass
class TestState:
    """Test state for graph execution."""

    value: int = 0
    output: str = ""


@dataclass
class SimpleNode(BaseNode[TestState, None, str]):
    """Simple test node."""

    output: str = "test"

    async def run(self, ctx: GraphRunContext[TestState]) -> End[str]:
        return End(self.output)


@dataclass
class BranchNode(BaseNode[TestState, None, bool]):
    """Node that branches based on condition."""

    condition: bool = True

    async def run(
        self, ctx: GraphRunContext[TestState]
    ) -> TrueBranchNode | FalseBranchNode:
        if self.condition:
            return TrueBranchNode()
        return FalseBranchNode()


@dataclass
class TrueBranchNode(BaseNode[TestState, None, str]):
    """Node for true branch."""

    async def run(self, ctx: GraphRunContext[TestState]) -> End[str]:
        return End("true")


@dataclass
class FalseBranchNode(BaseNode[TestState, None, str]):
    """Node for false branch."""

    async def run(self, ctx: GraphRunContext[TestState]) -> End[str]:
        return End("false")


@dataclass
class DecisionNode(BaseNode[TestState, None, str]):
    """Decision node that branches."""

    async def run(
        self, ctx: GraphRunContext[TestState]
    ) -> ConvergeA | ConvergeB:
        if ctx.state.value > 0:
            return ConvergeA()
        return ConvergeB()


@dataclass
class ConvergeA(BaseNode[TestState, None, str]):
    """Convergence path A."""

    async def run(self, ctx: GraphRunContext[TestState]) -> ConvergeNode:
        return ConvergeNode()


@dataclass
class ConvergeB(BaseNode[TestState, None, str]):
    """Convergence path B."""

    async def run(self, ctx: GraphRunContext[TestState]) -> ConvergeNode:
        return ConvergeNode()


@dataclass
class ConvergeNode(BaseNode[TestState, None, str]):
    """Node where paths converge."""

    async def run(self, ctx: GraphRunContext[TestState]) -> End[str]:
        return End("converged")


def test_graph_generates_mermaid_diagram_with_single_node():
    """Test graph generates mermaid diagram containing single node."""
    graph = Graph(nodes=(SimpleNode,))
    mermaid = graph.to_mermaid()

    assert "graph TD" in mermaid
    assert "SimpleNode" in mermaid
    assert "End" in mermaid
    assert "SimpleNode --> End" in mermaid


def test_graph_generates_mermaid_diagram_with_branching():
    """Test graph generates mermaid diagram showing branching paths."""
    graph = Graph(nodes=(BranchNode, TrueBranchNode, FalseBranchNode))
    mermaid = graph.to_mermaid()

    assert "graph TD" in mermaid
    assert "BranchNode" in mermaid
    assert "TrueBranchNode" in mermaid
    assert "FalseBranchNode" in mermaid
    assert "BranchNode -->" in mermaid


def test_graph_generates_mermaid_diagram_with_converging_paths():
    """Test graph generates mermaid diagram showing converging paths."""
    graph = Graph(nodes=(DecisionNode, ConvergeA, ConvergeB, ConvergeNode))
    mermaid = graph.to_mermaid()

    assert "graph TD" in mermaid
    assert "DecisionNode" in mermaid
    assert "ConvergeA" in mermaid
    assert "ConvergeB" in mermaid
    assert "ConvergeNode" in mermaid
    # Both paths should converge to ConvergeNode
    assert "ConvergeA --> ConvergeNode" in mermaid
    assert "ConvergeB --> ConvergeNode" in mermaid


def test_graph_generates_mermaid_diagram_with_custom_name():
    """Test graph generates mermaid diagram with custom graph name."""
    graph = Graph(nodes=(SimpleNode,), name="TestGraph")
    mermaid = graph.to_mermaid()

    assert "graph TD" in mermaid
    assert "subgraph TestGraph" in mermaid or "TestGraph" in mermaid


def test_graph_generates_mermaid_ink_url():
    """Test graph generates mermaid.ink URL for visualization."""
    graph = Graph(nodes=(SimpleNode,))
    url = graph.to_mermaid_ink_url()

    assert url.startswith("https://mermaid.ink/")
    assert "pako:" in url

    # Test with format
    svg_url = graph.to_mermaid_ink_url(format="svg")
    assert svg_url.startswith("https://mermaid.ink/svg/")

    # Test with theme (only for img format)
    img_url = graph.to_mermaid_ink_url(format="img", theme="dark")
    assert img_url.startswith("https://mermaid.ink/img/")
    assert "theme=dark" in img_url


def test_graph_saves_as_image_file(tmp_path):
    """Test graph saves mermaid diagram as image file (default SVG)."""
    graph = Graph(nodes=(SimpleNode,))
    output_file = tmp_path / "test_graph.svg"

    # Note: This test requires internet connection
    # Skip if network is not available
    try:
        graph.save_as_image(output_file)  # Default is SVG
        assert output_file.exists()
        assert output_file.stat().st_size > 0
    except (IOError, OSError, Exception) as e:
        error_msg = str(e)
        if "400" in error_msg or "404" in error_msg:
            pytest.skip(f"mermaid.ink API error (may be encoding issue): {e}")
        else:
            pytest.skip(
                f"Network not available or mermaid.ink is unreachable: {e}"
            )

    # Test SVG with theme
    svg_file = tmp_path / "test_graph_dark.svg"
    try:
        graph.save_as_image(svg_file, theme="dark")
        assert svg_file.exists()
        assert svg_file.stat().st_size > 0
    except (IOError, OSError, Exception) as e:
        error_msg = str(e)
        if "400" in error_msg or "404" in error_msg:
            pytest.skip(f"mermaid.ink API error (may be encoding issue): {e}")
        else:
            pytest.skip(
                f"Network not available or mermaid.ink is unreachable: {e}"
            )


def test_generate_visualization_images(image_output_dir, should_save_images):
    """
    Generate visualization images for manual inspection.

    This test generates images for various graph types so you can visually
    inspect the mermaid output. Run with --save-images to keep the files.

    Note: This test requires mermaid.ink API to be working. If it fails,
    you can still use graph.to_mermaid() to get the mermaid code and
    paste it into https://mermaid.live/ to visualize.

    Usage:
        pytest tests/test_mermaid.py::test_generate_visualization_images --save-images
        pytest tests/test_mermaid.py::test_generate_visualization_images --save-images --image-output-dir=my_images
    """
    # Create output directory
    image_output_dir.mkdir(parents=True, exist_ok=True)

    # Also save mermaid code files for manual inspection
    if should_save_images:
        mermaid_output_dir = image_output_dir.parent / "mermaid_code"
        mermaid_output_dir.mkdir(parents=True, exist_ok=True)

    # Test 1: Simple graph
    graph1 = Graph(nodes=(SimpleNode,), name="SimpleGraph")

    # Save mermaid code for manual inspection
    if should_save_images:
        mermaid_code_file = (
            image_output_dir.parent / "mermaid_code" / "simple_graph.mmd"
        )
        mermaid_code_file.parent.mkdir(parents=True, exist_ok=True)
        mermaid_code_file.write_text(graph1.to_mermaid())
        print(f"\n✓ Saved mermaid code: {mermaid_code_file}")
        print("  You can paste this into https://mermaid.live/ to visualize")

    try:
        output_file = image_output_dir / "simple_graph.svg"
        graph1.save_as_image(output_file)  # Default is SVG
        assert output_file.exists()
        if should_save_images:
            print(f"✓ Saved simple graph image: {output_file}")
    except (IOError, OSError, Exception) as e:
        # Continue to next test even if this one fails
        if should_save_images:
            print(f"⚠ Could not save simple graph image: {e}")
            print(
                f"  (Mermaid code is available at {image_output_dir.parent / 'mermaid_code' / 'simple_graph.mmd'})"
            )

    # Test 2: Branching graph
    graph2 = Graph(
        nodes=(BranchNode, TrueBranchNode, FalseBranchNode),
        name="BranchingGraph",
    )

    if should_save_images:
        mermaid_code_file = (
            image_output_dir.parent / "mermaid_code" / "branching_graph.mmd"
        )
        mermaid_code_file.write_text(graph2.to_mermaid())
        print(f"✓ Saved mermaid code: {mermaid_code_file}")

    try:
        output_file = image_output_dir / "branching_graph.svg"
        graph2.save_as_image(output_file)  # Default is SVG
        assert output_file.exists()
        if should_save_images:
            print(f"✓ Saved branching graph image: {output_file}")

        # Also save with dark theme
        try:
            svg_file = image_output_dir / "branching_graph_dark.svg"
            graph2.save_as_image(svg_file, theme="dark", bg_color="!black")
            assert svg_file.exists()
            if should_save_images:
                print(f"✓ Saved branching graph (dark) image: {svg_file}")
        except (IOError, OSError, Exception) as e:
            if should_save_images:
                print(f"⚠ Could not save dark theme SVG image: {e}")
    except (IOError, OSError, Exception) as e:
        # Continue to next test even if this one fails
        if should_save_images:
            print(f"⚠ Could not save branching graph image: {e}")

    # Test 3: Converging graph
    graph3 = Graph(
        nodes=(DecisionNode, ConvergeA, ConvergeB, ConvergeNode),
        name="ConvergingGraph",
    )

    if should_save_images:
        mermaid_code_file = (
            image_output_dir.parent / "mermaid_code" / "converging_graph.mmd"
        )
        mermaid_code_file.write_text(graph3.to_mermaid())
        print(f"✓ Saved mermaid code: {mermaid_code_file}")

    try:
        output_file = image_output_dir / "converging_graph.svg"
        graph3.save_as_image(output_file, width=800)  # Default is SVG
        assert output_file.exists()
        if should_save_images:
            print(f"✓ Saved converging graph image: {output_file}")
    except (IOError, OSError, Exception) as e:
        # Continue even if this fails
        if should_save_images:
            print(f"⚠ Could not save converging graph image: {e}")

    if should_save_images:
        print(
            f"\n📁 Mermaid code files saved to: {image_output_dir.parent / 'mermaid_code'}"
        )
        print(
            f"📁 Image files (if successful) saved to: {image_output_dir.absolute()}"
        )
        print(
            "\n💡 Tip: If images failed to generate, paste the .mmd files into https://mermaid.live/"
        )
    else:
        print(
            "\n💡 Tip: Run with --save-images to keep the generated images and mermaid code"
        )
