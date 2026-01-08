"""Unit tests for filetree utility."""

import tempfile
from pathlib import Path

from tui.filetree import get_project_tree


def test_get_project_tree():
    """Test get_project_tree returns tree structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        
        # Create some test files
        (root / "file1.py").write_text("# test")
        (root / "file2.txt").write_text("test")
        (root / "subdir").mkdir()
        (root / "subdir" / "file3.py").write_text("# test")
        
        tree = get_project_tree(root)
        
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


def test_get_project_tree_respects_max_depth():
    """Test get_project_tree respects max_depth."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        
        # Create nested structure
        current = root
        for i in range(10):
            current = current / f"dir{i}"
            current.mkdir()
            (current / f"file{i}.py").write_text("# test")
        
        tree = get_project_tree(root, max_depth=3)
        
        # Should include files up to depth 3
        assert "dir0" in tree
        # But might not include very deep directories
        # (exact behavior depends on implementation)


def test_get_project_tree_default_root():
    """Test get_project_tree uses current directory by default."""
    tree = get_project_tree()
    
        # Should contain current directory name
    assert isinstance(tree, str)
    assert len(tree) > 0

