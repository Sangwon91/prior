# Workflow Package

Graph-based workflow execution engine for complex agent tasks.

## Overview

This package provides a graph-based execution engine for orchestrating complex workflows with state management, conditional branching, and type-safe node execution. The workflow engine uses a node-based architecture where each node can return the next node to execute or an `End` node to terminate execution.

## Implementation Notes

This implementation was inspired by pydantic's graph implementation, but the dependency system was reimplemented from scratch to avoid external dependencies. Whether this will continue to evolve in the same direction as pydantic's graph in the future is uncertain. This choice was made simply to suit our own preferences and needs.

## Features

- **Graph-based execution**: Define workflows as graphs with node classes
- **Type-safe state management**: Generic type support for state, dependencies, and return values
- **Conditional branching**: Support for conditional branching by returning different node types from `run()` method with type hints
- **Iterative execution**: Step through graph execution with `graph.iter()` for fine-grained control
- **State management**: Shared execution context (`GraphRunContext`) across nodes
- **Node validation**: Optional `validate()` method for pre-execution checks

## Basic Usage

```python
from dataclasses import dataclass
from workflow import BaseNode, End, Graph, GraphRunContext

# Define your state
@dataclass
class MyState:
    value: int = 0
    message: str = ""

# Create a node class
@dataclass
class MyNode(BaseNode[MyState, None, str]):
    """A simple node that returns a string result."""
    
    async def run(
        self, ctx: GraphRunContext[MyState]
    ) -> End[str]:
        ctx.state.message = "Hello, World!"
        return End("result")

# Create graph with node classes
graph = Graph(nodes=(MyNode,))

# Execute the graph
state = MyState()
result = await graph.run(MyNode(), state=state)

print(result.output)  # "result"
print(result.state.message)  # "Hello, World!"
```

## Node Types

### BaseNode

All workflow nodes must inherit from `BaseNode` and implement the `run()` method. The `run()` method receives a `GraphRunContext` and returns either:
- Another `BaseNode` instance (to continue execution)
- An `End` node (to terminate execution)

```python
@dataclass
class ProcessNode(BaseNode[MyState, None, str]):
    """Node that processes data and moves to next node."""
    
    next_node: BaseNode[MyState, None, str]
    
    async def run(
        self, ctx: GraphRunContext[MyState]
    ) -> BaseNode[MyState, None, str] | End[str]:
        # Process state
        ctx.state.value += 1
        
        # Return next node or End
        if ctx.state.value >= 10:
            return End("completed")
        return self.next_node
```

### Conditional Branching

You can implement conditional branching directly in your nodes by returning different node types based on the context state. Use type hints to specify all possible return types:

```python
@dataclass
class TrueNode(BaseNode[MyState, None, str]):
    async def run(self, ctx: GraphRunContext[MyState]) -> End[str]:
        return End("true_result")

@dataclass
class FalseNode(BaseNode[MyState, None, str]):
    async def run(self, ctx: GraphRunContext[MyState]) -> End[str]:
        return End("false_result")

@dataclass
class CheckNode(BaseNode[MyState, None, str]):
    """Node that conditionally branches based on state."""
    
    async def run(
        self, ctx: GraphRunContext[MyState]
    ) -> TrueNode | FalseNode | End[str]:
        if ctx.state.value > 5:
            return TrueNode()
        else:
            return FalseNode()

# Use in graph
graph = Graph(nodes=(CheckNode, TrueNode, FalseNode))
state = MyState(value=10)
result = await graph.run(CheckNode(), state=state)
# result.output == "true_result"
```

## Advanced Features

### Iterative Execution

Use `graph.iter()` to step through execution manually:

```python
async with graph.iter(MyNode(), state=state) as run:
    async for node in run:
        print(f"Executing: {type(node).__name__}")
        # You can inspect or modify state between nodes
        if isinstance(node, End):
            break

# Access final result
print(run.result.output)
```

### Manual Node Execution

Use `run.next()` to manually control execution:

```python
async with graph.iter(MyNode(), state=state) as run:
    node = await run.__anext__()  # Get first node
    while not isinstance(node, End):
        # Execute node manually
        node = await run.next(node)
```

### Synchronous Execution

For synchronous code, use `run_sync()`:

```python
result = graph.run_sync(MyNode(), state=state)
```

### Node Validation

Implement `validate()` to check if a node can be executed:

```python
@dataclass
class ValidatedNode(BaseNode[MyState, None, str]):
    async def validate(self, ctx: GraphRunContext[MyState]) -> bool:
        # Only execute if state meets condition
        return ctx.state.value > 0
    
    async def run(self, ctx: GraphRunContext[MyState]) -> End[str]:
        return End("validated")
```

### Generic Types

The workflow engine supports generic types for type safety:

```python
StateT = TypeVar("StateT")  # State type
DepsT = TypeVar("DepsT")    # Dependencies type
RunEndT = TypeVar("RunEndT")  # Return type

@dataclass
class TypedNode(BaseNode[MyState, dict, int]):
    """Node with typed state, dependencies, and return value."""
    
    async def run(
        self, ctx: GraphRunContext[MyState, dict]
    ) -> End[int]:
        # Access typed state and deps
        value = ctx.state.value
        config = ctx.deps.get("config") if ctx.deps else None
        return End(value * 2)
```

## API Reference

### Graph

- `Graph(nodes: Sequence[type[BaseNode]], name: str | None = None)` - Create a graph from node classes
- `async def run(start_node, *, state, deps=None) -> GraphRunResult` - Execute graph to completion
- `def run_sync(start_node, *, state, deps=None) -> GraphRunResult` - Synchronously execute graph
- `async def iter(start_node, *, state, deps=None) -> AsyncIterator[GraphRun]` - Iterate through execution

### BaseNode

- `async def validate(ctx: GraphRunContext) -> bool` - Validate if node can execute (default: True)
- `async def run(ctx: GraphRunContext) -> BaseNode | End` - Execute node and return next node

### GraphRunContext

- `state: StateT` - The workflow state
- `deps: DepsT | None` - Optional dependencies

### GraphRunResult

- `output: RunEndT | None` - Final output from End node
- `state: StateT` - Final state after execution

## Mermaid Visualization

The workflow package includes built-in support for visualizing graphs as mermaid diagrams.

### Basic Usage

```python
from workflow import Graph

graph = Graph(nodes=(MyNode, OtherNode))

# Generate mermaid code
mermaid_code = graph.to_mermaid()
print(mermaid_code)

# Generate mermaid.ink URL
url = graph.to_mermaid_ink_url()
print(url)  # Can be opened in browser or embedded in markdown

# Save as image file
graph.save_as_image("graph.png")
graph.save_as_image("graph.svg", format="svg", theme="dark")
```

### Testing with Image Generation

When writing tests, you can generate images for visual inspection:

```python
def test_my_graph(image_output_dir, should_save_images):
    """Test that generates images for manual inspection."""
    graph = Graph(nodes=(MyNode,))
    
    # Save image (will be kept if --save-images flag is used)
    graph.save_as_image(image_output_dir / "my_graph.png")
    
    if should_save_images:
        print(f"Image saved to: {image_output_dir / 'my_graph.png'}")
```

Run tests with image generation:

```bash
# Save images to default directory (test_output/images)
pytest tests/test_graph.py::test_generate_visualization_images --save-images

# Save to custom directory
pytest tests/test_graph.py::test_generate_visualization_images --save-images --image-output-dir=my_images

# Or use environment variable
SAVE_TEST_IMAGES=1 pytest tests/test_graph.py::test_generate_visualization_images
```

Without the `--save-images` flag, images are saved to temporary directories that are automatically cleaned up after tests.