"""Tests for agent workflows."""

import tempfile
from pathlib import Path

import pytest

from agent.workflows import (
    create_project_analysis_workflow,
    execute_project_analysis,
)
from workflow.types import NodeState


@pytest.mark.asyncio
async def test_create_project_analysis_workflow():
    """Test creating project analysis workflow."""
    graph = create_project_analysis_workflow()

    assert graph.get_node("get_project_tree") is not None
    assert graph.get_node("analyze_project") is not None

    deps = graph.get_dependencies("analyze_project")
    assert "get_project_tree" in deps


@pytest.mark.asyncio
async def test_execute_project_analysis():
    """Test executing project analysis workflow."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)

        # Create some test files
        (root / "file1.py").write_text("# test")
        (root / "file2.txt").write_text("test")
        (root / "subdir").mkdir()
        (root / "subdir" / "file3.py").write_text("# test")

        context = await execute_project_analysis(root)

        # Check results
        assert context.get_node_state("get_project_tree") == NodeState.COMPLETED
        assert context.get_node_state("analyze_project") == NodeState.COMPLETED

        # Check context data
        tree = context.get("project_tree")
        assert tree is not None
        assert "file1.py" in tree

        analysis = context.get("analysis")
        assert analysis is not None
        assert "file_count" in analysis
        assert analysis["file_count"] > 0

