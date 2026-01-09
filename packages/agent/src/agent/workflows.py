"""Example workflows for agent tasks."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from tools.filetree import get_project_tree
from workflow import BaseNode, End, Graph, GraphRunContext
from workflow.types import NodeState

from .event_publisher import AgentEventPublisher


@dataclass
class ProjectState:
    """State for project analysis workflow."""

    project_tree: str = ""
    analysis: dict | None = None


@dataclass
class GetProjectTree(BaseNode[ProjectState, None, dict]):
    """Node that gets project tree structure."""

    project_root: Path | None = None

    async def run(self, ctx: GraphRunContext[ProjectState]) -> AnalyzeProject:
        """
        Execute node to get project tree.

        Args:
            ctx: Graph run context

        Returns:
            Next node to execute
        """
        tree = get_project_tree(self.project_root)
        ctx.state.project_tree = tree
        return AnalyzeProject()


@dataclass
class AnalyzeProject(BaseNode[ProjectState, None, dict]):
    """Node that analyzes project structure."""

    async def run(self, ctx: GraphRunContext[ProjectState]) -> End[dict]:
        """
        Analyze project structure from context.

        Args:
            ctx: Graph run context

        Returns:
            End node with analysis results
        """
        tree = ctx.state.project_tree
        # Simple analysis: count lines and files
        lines = tree.split("\n")
        file_count = sum(1 for line in lines if "└──" in line or "├──" in line)

        analysis = {
            "total_lines": len(lines),
            "file_count": file_count,
            "tree": tree,
        }
        ctx.state.analysis = analysis
        return End(analysis)


def create_project_analysis_workflow() -> Graph[ProjectState, None, dict]:
    """
    Create a workflow for analyzing project structure.

    Returns:
        Configured workflow graph
    """
    return Graph(nodes=(GetProjectTree, AnalyzeProject))


async def execute_project_analysis(
    project_root: Path | None = None,
    event_publisher: AgentEventPublisher | None = None,
) -> dict:
    """
    Execute project analysis workflow.

    Args:
        project_root: Project root directory
        event_publisher: Optional event publisher for workflow events

    Returns:
        Analysis results dictionary
    """
    graph = create_project_analysis_workflow()
    state = ProjectState()
    workflow_id = (
        event_publisher.generate_workflow_id()
        if event_publisher
        else "workflow-unknown"
    )

    try:
        if event_publisher:
            await event_publisher.publish_workflow_started(workflow_id)

        result = await graph.run(
            GetProjectTree(project_root=project_root), state=state
        )

        if event_publisher:
            await event_publisher.publish_workflow_completed(
                workflow_id, result.output
            )

        return result.output
    except Exception as e:
        if event_publisher:
            await event_publisher.publish_workflow_error(
                workflow_id,
                str(e),
                {"type": type(e).__name__},
            )
        raise
