# Tools Package

Agent tools and utilities for project operations.

## Overview

This package provides reusable tools that can be used by both the agent and TUI packages, ensuring separation of concerns and avoiding UI dependencies in core functionality.

## Tools

### `get_project_tree`

Get project file tree as a formatted string.

```python
from tools.filetree import get_project_tree
from pathlib import Path

tree = get_project_tree(Path("/path/to/project"))
```

### Tool Registry

Tools can be registered and discovered:

```python
from tools.registry import register_tool, get_tool, list_tools

# Register a tool
register_tool("my_tool", my_function)

# Get a tool
tool = get_tool("my_tool")

# List all tools
all_tools = list_tools()
```

