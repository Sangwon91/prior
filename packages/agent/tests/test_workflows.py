"""Tests for agent workflows."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from agent.workflows import (
    create_project_analysis_workflow,
    execute_project_analysis,
)


@pytest.mark.asyncio
async def test_create_project_analysis_workflow():
    """Test creating project analysis workflow."""
    graph = create_project_analysis_workflow()

    # Graph should have the node classes
    assert len(graph.node_defs) == 2


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

        result = await execute_project_analysis(root)

        # Check results
        assert result is not None
        assert "file_count" in result
        assert result["file_count"] > 0
        assert "total_lines" in result
        assert "tree" in result
        assert "file1.py" in result["tree"]
