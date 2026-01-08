"""Example workflows for agent tasks."""

from pathlib import Path

from tools.filetree import get_project_tree
from workflow.executor import Executor
from workflow.graph import Graph
from workflow.node import Node
from workflow.state import ExecutionContext


class GetProjectTreeNode(Node):
    """Node that gets project tree structure."""

    def __init__(self, project_root: Path | None = None):
        """
        Initialize node.

        Args:
            project_root: Project root directory
        """
        super().__init__("get_project_tree")
        self.project_root = project_root

    async def execute(self, context: ExecutionContext) -> str:
        """
        Execute node to get project tree.

        Args:
            context: Execution context

        Returns:
            Project tree string
        """
        tree = get_project_tree(self.project_root)
        context.set("project_tree", tree)
        return tree


class AnalyzeProjectNode(Node):
    """Node that analyzes project structure."""

    def __init__(self):
        """Initialize node."""
        super().__init__("analyze_project")

    async def execute(self, context: ExecutionContext) -> dict:
        """
        Analyze project structure from context.

        Args:
            context: Execution context

        Returns:
            Analysis results
        """
        tree = context.get("project_tree", "")
        # Simple analysis: count lines and files
        lines = tree.split("\n")
        file_count = sum(1 for line in lines if "└──" in line or "├──" in line)

        analysis = {
            "total_lines": len(lines),
            "file_count": file_count,
            "tree": tree,
        }
        context.set("analysis", analysis)
        return analysis


def create_project_analysis_workflow(project_root: Path | None = None) -> Graph:
    """
    Create a workflow for analyzing project structure.

    Args:
        project_root: Project root directory

    Returns:
        Configured workflow graph
    """
    graph = Graph()

    # Add nodes
    tree_node = GetProjectTreeNode(project_root)
    analyze_node = AnalyzeProjectNode()

    graph.add_node(tree_node)
    graph.add_node(analyze_node, dependencies=["get_project_tree"])

    return graph


async def execute_project_analysis(project_root: Path | None = None) -> ExecutionContext:
    """
    Execute project analysis workflow.

    Args:
        project_root: Project root directory

    Returns:
        Execution context with results
    """
    graph = create_project_analysis_workflow(project_root)
    executor = Executor()
    context = ExecutionContext()

    return await executor.execute(graph, context)

