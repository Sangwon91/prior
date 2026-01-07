"""Utility to read project file tree."""

from pathlib import Path


def get_project_tree(root: Path | None = None, max_depth: int = 5) -> str:
    """
    Get project file tree as a string.

    Args:
        root: Root directory (default: current working directory)
        max_depth: Maximum depth to traverse

    Returns:
        File tree as a formatted string
    """
    if root is None:
        root = Path.cwd()

    root = Path(root).resolve()

    # Files/directories to ignore
    ignore_patterns = {
        ".git",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".venv",
        "venv",
        "env",
        ".env",
        "node_modules",
        ".DS_Store",
        "*.pyc",
        "*.pyo",
        ".coverage",
        "htmlcov",
        ".tox",
        "dist",
        "build",
        "*.egg-info",
    }

    def should_ignore(path: Path) -> bool:
        """Check if path should be ignored."""
        name = path.name
        # Check exact matches
        if name in ignore_patterns:
            return True
        # Check patterns
        for pattern in ignore_patterns:
            if pattern.startswith("*") and name.endswith(pattern[1:]):
                return True
        return False

    def build_tree(path: Path, prefix: str = "", is_last: bool = True, depth: int = 0) -> list[str]:
        """Recursively build tree structure."""
        if depth > max_depth:
            return []

        lines = []
        if path != root:
            connector = "└── " if is_last else "├── "
            lines.append(f"{prefix}{connector}{path.name}")

        if path.is_file() or depth >= max_depth:
            return lines

        # Get children
        try:
            children = sorted(
                [p for p in path.iterdir() if not should_ignore(p)],
                key=lambda p: (p.is_file(), p.name.lower()),
            )
        except PermissionError:
            return lines

        if not children:
            return lines

        new_prefix = prefix + ("    " if is_last else "│   ")

        for i, child in enumerate(children):
            is_last_child = i == len(children) - 1
            lines.extend(build_tree(child, new_prefix, is_last_child, depth + 1))

        return lines

    tree_lines = [f"{root.name}/"]
    tree_lines.extend(build_tree(root, "", True, 0))

    return "\n".join(tree_lines)

