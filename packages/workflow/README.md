# Workflow Package

Graph-based workflow execution engine for complex agent tasks.

## Overview

This package provides a DAG (Directed Acyclic Graph) based execution engine for orchestrating complex workflows with dependencies, parallel execution, and error handling.

## Features

- **DAG-based execution**: Define workflows as graphs with nodes and dependencies
- **Parallel execution**: Automatically execute independent nodes in parallel
- **Error handling**: Configurable error handling strategies
- **Conditional branching**: Support for conditional node execution
- **State management**: Shared execution context across nodes

## Basic Usage

```python
from workflow import Graph, Node, Executor, ExecutionContext

class MyNode(Node):
    def __init__(self, node_id: str):
        super().__init__(node_id)
    
    async def execute(self, context: ExecutionContext):
        # Your logic here
        return "result"

# Create graph
graph = Graph()
node1 = MyNode("node1")
node2 = MyNode("node2")

graph.add_node(node1)
graph.add_node(node2, dependencies=["node1"])

# Execute
executor = Executor()
context = ExecutionContext()
result_context = await executor.execute(graph, context)
```

## Advanced Features

### Conditional Nodes

```python
from workflow.nodes.conditional import ConditionalNode

def condition(ctx):
    return ctx.get("flag", False)

cond_node = ConditionalNode(
    "cond",
    condition,
    true_node_id="node_true",
    false_node_id="node_false"
)
```

### Error Handling

```python
# Continue execution even if nodes fail
executor = Executor(continue_on_error=True)
```

### Parallel Execution Control

```python
# Limit parallel execution
executor = Executor(max_parallel=4)
```

