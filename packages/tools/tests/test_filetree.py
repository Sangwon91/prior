"""Unit tests for filetree utility."""

import tempfile
from pathlib import Path

from tools.filetree import get_project_tree


def test_get_project_tree_returns_tree_structure_with_all_files():
    """Test get_project_tree returns tree structure containing all files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)

        # Create some test files
        (root / "file1.py").write_text("# test")
        (root / "file2.txt").write_text("test")
        (root / "subdir").mkdir()
        (root / "subdir" / "file3.py").write_text("# test")

        tree = get_project_tree(root)

        # Verify all files and directories are included
        assert root.name in tree
        assert "file1.py" in tree
        assert "file2.txt" in tree
        assert "subdir" in tree
        assert "file3.py" in tree


def test_get_project_tree_ignores_pycache():
    """Test get_project_tree ignores __pycache__."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)

        (root / "file.py").write_text("# test")
        (root / "__pycache__").mkdir()
        (root / "__pycache__" / "file.pyc").write_bytes(b"test")

        tree = get_project_tree(root)

        assert "file.py" in tree
        assert "__pycache__" not in tree
        assert "file.pyc" not in tree


def test_get_project_tree_ignores_git():
    """Test get_project_tree ignores .git directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)

        (root / "file.py").write_text("# test")
        (root / ".git").mkdir()
        (root / ".git" / "config").write_text("test")

        tree = get_project_tree(root)

        assert "file.py" in tree
        assert ".git" not in tree


def test_get_project_tree_respects_max_depth_parameter():
    """Test get_project_tree limits tree depth based on max_depth parameter."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)

        # Create nested structure
        current = root
        for i in range(5):
            current = current / f"dir{i}"
            current.mkdir()
            (current / f"file{i}.py").write_text("# test")

        tree_shallow = get_project_tree(root, max_depth=2)
        tree_deep = get_project_tree(root, max_depth=5)

        # Shallow tree should have fewer directory levels
        # Deep tree should include more levels
        assert "dir0" in tree_shallow
        assert "dir0" in tree_deep
        # Deep tree should have more content
        assert len(tree_deep) > len(tree_shallow)


def test_get_project_tree_uses_current_directory_when_no_root_specified():
    """Test get_project_tree uses current directory when root is not specified."""
    tree = get_project_tree()

    # Should return a non-empty tree string
    assert isinstance(tree, str)
    assert len(tree) > 0
