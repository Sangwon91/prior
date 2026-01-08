"""Tool registry for managing and discovering agent tools."""

from collections.abc import Callable
from typing import Any

# Global tool registry
_tools: dict[str, Callable[..., Any]] = {}


def register_tool(name: str, func: Callable[..., Any]) -> None:
    """
    Register a tool function.

    Args:
        name: Tool name
        func: Tool function
    """
    _tools[name] = func


def get_tool(name: str) -> Callable[..., Any] | None:
    """
    Get a tool by name.

    Args:
        name: Tool name

    Returns:
        Tool function or None if not found
    """
    return _tools.get(name)


def list_tools() -> list[str]:
    """
    List all registered tools.

    Returns:
        List of tool names
    """
    return list(_tools.keys())

