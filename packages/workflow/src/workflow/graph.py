"""Graph definition for workflow execution."""

from collections import defaultdict

from .node import Node


class Graph:
    """Workflow graph with nodes and dependencies."""

    def __init__(self):
        """Initialize empty graph."""
        self._nodes: dict[str, Node] = {}
        self._dependencies: dict[str, set[str]] = defaultdict(set)
        self._dependents: dict[str, set[str]] = defaultdict(set)

    def add_node(self, node: Node, dependencies: list[str] | None = None) -> None:
        """
        Add a node to the graph.

        Args:
            node: Node to add
            dependencies: List of node IDs this node depends on
        """
        if node.id in self._nodes:
            raise ValueError(f"Node {node.id} already exists in graph")

        self._nodes[node.id] = node

        if dependencies:
            for dep_id in dependencies:
                if dep_id not in self._nodes:
                    raise ValueError(f"Dependency {dep_id} not found in graph")
                self._dependencies[node.id].add(dep_id)
                self._dependents[dep_id].add(node.id)

    def add_edge(self, from_node: str, to_node: str) -> None:
        """
        Add an edge (dependency) between nodes.

        Args:
            from_node: Source node ID
            to_node: Target node ID
        """
        if from_node not in self._nodes:
            raise ValueError(f"Node {from_node} not found in graph")
        if to_node not in self._nodes:
            raise ValueError(f"Node {to_node} not found in graph")

        self._dependencies[to_node].add(from_node)
        self._dependents[from_node].add(to_node)

    def get_node(self, node_id: str) -> Node | None:
        """
        Get a node by ID.

        Args:
            node_id: Node identifier

        Returns:
            Node or None if not found
        """
        return self._nodes.get(node_id)

    def get_dependencies(self, node_id: str) -> set[str]:
        """
        Get dependencies of a node.

        Args:
            node_id: Node identifier

        Returns:
            Set of dependency node IDs
        """
        return self._dependencies.get(node_id, set()).copy()

    def get_dependents(self, node_id: str) -> set[str]:
        """
        Get nodes that depend on this node.

        Args:
            node_id: Node identifier

        Returns:
            Set of dependent node IDs
        """
        return self._dependents.get(node_id, set()).copy()

    def get_all_nodes(self) -> dict[str, Node]:
        """
        Get all nodes in the graph.

        Returns:
            Dictionary of node ID to Node
        """
        return self._nodes.copy()

    def validate(self) -> tuple[bool, str | None]:
        """
        Validate the graph (check for cycles).

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check for cycles using DFS
        visited: set[str] = set()
        rec_stack: set[str] = set()

        def has_cycle(node_id: str) -> bool:
            visited.add(node_id)
            rec_stack.add(node_id)

            for dep_id in self._dependencies.get(node_id, set()):
                if dep_id not in visited:
                    if has_cycle(dep_id):
                        return True
                elif dep_id in rec_stack:
                    return True

            rec_stack.remove(node_id)
            return False

        for node_id in self._nodes:
            if node_id not in visited:
                if has_cycle(node_id):
                    return False, f"Cycle detected involving node {node_id}"

        return True, None

    def get_execution_order(self) -> list[list[str]]:
        """
        Get topological sort order for execution.

        Returns:
            List of layers, where each layer can be executed in parallel
        """
        # Kahn's algorithm for topological sort
        in_degree: dict[str, int] = {
            node_id: len(self._dependencies.get(node_id, set()))
            for node_id in self._nodes
        }

        layers: list[list[str]] = []
        queue: list[str] = [node_id for node_id, degree in in_degree.items() if degree == 0]

        while queue:
            layer: list[str] = []
            next_queue: list[str] = []

            for node_id in queue:
                layer.append(node_id)
                for dependent_id in self._dependents.get(node_id, set()):
                    in_degree[dependent_id] -= 1
                    if in_degree[dependent_id] == 0:
                        next_queue.append(dependent_id)

            layers.append(layer)
            queue = next_queue

        # Check if all nodes were processed
        if sum(len(layer) for layer in layers) != len(self._nodes):
            raise ValueError("Graph has cycles, cannot determine execution order")

        return layers

