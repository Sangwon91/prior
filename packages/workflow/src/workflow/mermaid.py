"""Mermaid visualization utilities for workflow graphs."""

from __future__ import annotations

import base64
import inspect
import json
import zlib
from pathlib import Path
from typing import TYPE_CHECKING, Literal, get_args, get_origin, get_type_hints
from urllib.request import urlopen

from typing_extensions import Union

from .node import BaseNode, End

if TYPE_CHECKING:
    from .graph import Graph


def graph_to_mermaid(graph: "Graph") -> str:
    """
    Generate a mermaid graph representation of a workflow graph.

    Args:
        graph: The workflow graph to visualize

    Returns:
        A mermaid graph string that can be rendered in markdown or mermaid viewers.
    """
    lines = ["graph TD"]
    
    # Helper function to sanitize node names for mermaid
    def sanitize_name(name: str) -> str:
        """Convert node class name to mermaid-safe identifier."""
        # Replace spaces and special characters with underscores
        return name.replace(" ", "_").replace("-", "_").replace(".", "_")
    
    # Helper function to extract possible next nodes from return type
    def extract_next_nodes(return_type) -> list[type]:
        """Extract BaseNode subclasses from return type annotation."""
        next_nodes = []
        
        # Handle tuple of types (from string annotation parsing)
        if isinstance(return_type, tuple):
            return list(return_type)
        
        # Handle string annotations (from __future__ import annotations)
        # These should already be resolved, but handle just in case
        if isinstance(return_type, str):
            return next_nodes
        
        # Handle Union types (Python 3.10+ uses | operator, older uses Union)
        origin = get_origin(return_type)
        
        # Check for Union type (both typing.Union and | operator)
        is_union = False
        if origin is Union:
            is_union = True
        elif origin is not None:
            # Python 3.10+ uses types.UnionType for | operator
            try:
                import types
                if origin is types.UnionType:
                    is_union = True
            except (ImportError, AttributeError):
                pass
        
        if is_union:
            # Handle both typing.Union and | operator
            args = get_args(return_type)
            for arg in args:
                # Check if it's a BaseNode subclass (but not BaseNode itself)
                if (inspect.isclass(arg) and 
                    issubclass(arg, BaseNode) and 
                    arg is not BaseNode):
                    next_nodes.append(arg)
                # Check if it's End type (could be End or End[SomeType])
                elif arg is End:
                    next_nodes.append(End)
                elif (hasattr(arg, '__origin__') and 
                      get_origin(arg) is End):
                    next_nodes.append(End)
                # Recursively check nested unions
                else:
                    nested = extract_next_nodes(arg)
                    if nested:
                        next_nodes.extend(nested)
        else:
            # Single type (not a Union)
            if inspect.isclass(return_type):
                if (issubclass(return_type, BaseNode) and 
                    return_type is not BaseNode):
                    next_nodes.append(return_type)
                elif return_type is End:
                    next_nodes.append(End)
            elif hasattr(return_type, '__origin__'):
                # Handle generic types like End[SomeType]
                origin_type = get_origin(return_type)
                if origin_type is End:
                    next_nodes.append(End)
                # Also check if it's a BaseNode subclass
                elif (inspect.isclass(origin_type) and
                      issubclass(origin_type, BaseNode) and
                      origin_type is not BaseNode):
                    next_nodes.append(origin_type)
        
        return next_nodes
    
    # Build node to next nodes mapping
    node_edges: dict[type[BaseNode], list[type | type[End]]] = {}
    end_nodes: set[str] = set()
    
    for node_class in graph.node_defs:
        # Get the run method
        if not hasattr(node_class, "run"):
            continue
        
        run_method = getattr(node_class, "run")
        sig = inspect.signature(run_method)
        return_annotation = sig.return_annotation
        
        # Skip if no return annotation
        if return_annotation is inspect.Signature.empty:
            continue
        
        # Handle string annotations (from __future__ import annotations)
        # Parse string annotations to extract node types
        if isinstance(return_annotation, str):
            # Simple pattern matching for common cases
            if return_annotation.startswith("End[") or return_annotation == "End":
                # It's an End type
                return_annotation = End
            else:
                # Try to extract node class names from the string
                # Look for patterns like "NodeName" or "NodeName | End[str]"
                import re
                module = inspect.getmodule(node_class)
                if module is not None:
                    # Extract potential class names (capitalized words)
                    node_pattern = r'\b([A-Z][a-zA-Z0-9_]*)\b'
                    matches = re.findall(node_pattern, return_annotation)
                    found_types = []
                    for match in matches:
                        if match in module.__dict__:
                            obj = module.__dict__[match]
                            if match == "End" or (inspect.isclass(obj) and obj is End):
                                found_types.append(End)
                            elif (inspect.isclass(obj) and 
                                  issubclass(obj, BaseNode) and 
                                  obj is not BaseNode and
                                  obj in graph.node_defs):
                                found_types.append(obj)
                    
                    # If we found types, create a union-like structure
                    if found_types:
                        if len(found_types) == 1:
                            return_annotation = found_types[0]
                        else:
                            # Multiple types found, we'll handle this in extract_next_nodes
                            # For now, store as a tuple that extract_next_nodes can process
                            return_annotation = tuple(found_types)
        else:
            # Not a string, try get_type_hints for non-string annotations
            try:
                module = inspect.getmodule(node_class)
                if module is not None:
                    hints = get_type_hints(run_method, globalns=module.__dict__, include_extras=True)
                    if "return" in hints:
                        return_annotation = hints["return"]
            except (NameError, TypeError, AttributeError, KeyError):
                pass
        
        # Extract possible next nodes
        next_nodes = extract_next_nodes(return_annotation)
        node_edges[node_class] = next_nodes
        
        # Check if this node can transition to End
        for next_node in next_nodes:
            if next_node is End:
                end_nodes.add(sanitize_name(node_class.__name__))
    
    # Generate mermaid nodes and edges
    node_ids: dict[type[BaseNode], str] = {}
    
    # Create node definitions
    for node_class in graph.node_defs:
        node_id = sanitize_name(node_class.__name__)
        node_ids[node_class] = node_id
        node_label = node_class.__name__
        lines.append(f'    {node_id}["{node_label}"]')
    
    # Create End node if any node can reach it
    if end_nodes:
        end_id = "End"
        lines.append(f'    {end_id}["End"]')
    
    # Create edges
    for node_class, next_nodes in node_edges.items():
        node_id = node_ids[node_class]
        
        for next_node in next_nodes:
            if next_node is End:
                lines.append(f"    {node_id} --> {end_id}")
            elif next_node in node_ids:
                next_id = node_ids[next_node]
                lines.append(f"    {node_id} --> {next_id}")
    
    # Wrap in subgraph if graph has a name
    if graph.name:
        graph_lines = lines[1:]  # Skip "graph TD"
        lines = ["graph TD"]
        lines.append(f'    subgraph "{graph.name}"')
        for line in graph_lines:
            lines.append(f"    {line}")
        lines.append("    end")
    
    return "\n".join(lines)


def encode_mermaid_for_ink(mermaid_code: str) -> str:
    """
    Encode mermaid code for mermaid.ink URL.
    
    Mermaid.ink expects a JSON object containing the mermaid code, compressed with zlib,
    and then base64 URL-safe encoded.
    
    According to mermaid.ink documentation and working examples:
    - The data is a JSON object: {"code": "mermaid code here"}
    - Compressed with standard zlib (not raw deflate)
    - Encoded with URL-safe base64 (uses _ and - instead of + and /)
    - Padding is removed
    
    Args:
        mermaid_code: The mermaid diagram code
        
    Returns:
        Encoded string for mermaid.ink URL
    """
    # Create JSON object with mermaid code
    # mermaid.ink expects {"code": "..."} format
    json_data = {"code": mermaid_code}
    json_str = json.dumps(json_data, separators=(',', ':'))
    
    # Compress using standard zlib (pako uses zlib with header)
    compressed = zlib.compress(json_str.encode('utf-8'), level=9)
    
    # Base64 encode using URL-safe alphabet (uses _ and -)
    # This is the key difference - mermaid.ink uses URL-safe base64
    encoded = base64.urlsafe_b64encode(compressed).decode('ascii')
    # Remove padding (mermaid.ink doesn't use padding)
    encoded = encoded.rstrip('=')
    return encoded


def mermaid_to_ink_url(
    mermaid_code: str,
    format: Literal["img", "svg", "pdf"] = "img",
    theme: str | None = None,
    bg_color: str | None = None,
    width: int | None = None,
    height: int | None = None,
) -> str:
    """
    Generate a mermaid.ink URL for mermaid code.
    
    Args:
        mermaid_code: The mermaid diagram code
        format: Output format - "img" (default), "svg", or "pdf"
        theme: Optional theme name (default, neutral, dark, forest)
        bg_color: Optional background color (hex code or named color with ! prefix)
        width: Optional image width in pixels
        height: Optional image height in pixels
        
    Returns:
        URL string for mermaid.ink image
        
    Examples:
        >>> mermaid_code = "graph TD\\n    A --> B"
        >>> url = mermaid_to_ink_url(mermaid_code)
        >>> url = mermaid_to_ink_url(mermaid_code, format="svg", theme="dark")
    """
    encoded = encode_mermaid_for_ink(mermaid_code)
    
    # Build URL with pako: prefix (mermaid.ink format)
    # mermaid.ink requires the pako: prefix before the encoded string
    base_url = f"https://mermaid.ink/{format}/pako:{encoded}"
    
    # Add query parameters
    # Note: SVG and PDF endpoints do not support query parameters
    # Only /img endpoint supports query parameters
    params = []
    if format == "img":
        # /img endpoint supports query parameters
        if theme:
            params.append(f"theme={theme}")
        if bg_color:
            params.append(f"bgColor={bg_color}")
        if width:
            params.append(f"width={width}")
        if height:
            params.append(f"height={height}")
    
    if params:
        base_url += "?" + "&".join(params)
    
    return base_url


def save_mermaid_as_image(
    mermaid_code: str,
    filepath: str | Path,
    format: Literal["png", "jpeg", "webp", "svg", "pdf"] = "svg",
    theme: str | None = None,
    bg_color: str | None = None,
    width: int | None = None,
    height: int | None = None,
) -> None:
    """
    Save mermaid code as an image file using mermaid.ink.
    
    Args:
        mermaid_code: The mermaid diagram code
        filepath: Path where to save the image file
        format: Image format - "png", "jpeg", "webp", "svg", or "pdf" (default: "svg")
        theme: Optional theme name (default, neutral, dark, forest)
        bg_color: Optional background color (hex code or named color with ! prefix)
        width: Optional image width in pixels
        height: Optional image height in pixels
        
    Raises:
        IOError: If the image cannot be downloaded or saved
        
    Examples:
        >>> mermaid_code = "graph TD\\n    A --> B"
        >>> save_mermaid_as_image(mermaid_code, "graph.svg")
        >>> save_mermaid_as_image(mermaid_code, "graph.png", format="png")
    """
    filepath = Path(filepath)
    
    # Map format to mermaid.ink endpoint
    # According to mermaid.ink docs:
    # - /img endpoint: default is jpeg, use ?type=png or ?type=webp for other formats
    # - /svg endpoint: returns SVG
    # - /pdf endpoint: returns PDF
    
    if format in ("png", "jpeg", "webp"):
        ink_format = "img"
        # Build query parameters
        params = []
        # /img endpoint defaults to jpeg, so only add type if not jpeg
        if format != "jpeg":
            params.append(f"type={format}")
        if theme:
            params.append(f"theme={theme}")
        if bg_color:
            params.append(f"bgColor={bg_color}")
        if width:
            params.append(f"width={width}")
        if height:
            params.append(f"height={height}")
        
        # Build URL with query parameters
        encoded = encode_mermaid_for_ink(mermaid_code)
        base_url = f"https://mermaid.ink/{ink_format}/pako:{encoded}"
        if params:
            url = base_url + "?" + "&".join(params)
        else:
            url = base_url
    elif format == "svg":
        ink_format = "svg"
        url = mermaid_to_ink_url(
            mermaid_code,
            format=ink_format,
            theme=theme,
            bg_color=bg_color,
            width=width,
            height=height,
        )
    elif format == "pdf":
        ink_format = "pdf"
        url = mermaid_to_ink_url(
            mermaid_code,
            format=ink_format,
            theme=theme,
            bg_color=bg_color,
            width=width,
            height=height,
        )
    else:
        raise ValueError(f"Unsupported format: {format}")
    
    # Download and save
    try:
        with urlopen(url) as response:
            filepath.write_bytes(response.read())
    except Exception as e:
        raise IOError(f"Failed to download image from mermaid.ink: {e}") from e

