"""Example workflows for agent tasks."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from protocol.models import ChatMessage
from tools.filetree import get_project_tree
from typing import TYPE_CHECKING

from workflow import BaseNode, End, Graph, GraphRunContext

if TYPE_CHECKING:
    from adapter import AdapterClient
    from agent import Agent


@dataclass
class ProjectState:
    """State for project analysis workflow."""

    project_tree: str = ""
    analysis: dict | None = None


@dataclass
class GetProjectTree(BaseNode[ProjectState, None, dict]):
    """Node that gets project tree structure."""

    project_root: Path | None = None

    async def run(
        self, ctx: GraphRunContext[ProjectState]
    ) -> AnalyzeProject:
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

    async def run(
        self, ctx: GraphRunContext[ProjectState]
    ) -> End[dict]:
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
        file_count = sum(
            1 for line in lines if "└──" in line or "├──" in line
        )

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


@dataclass
class ChatState:
    """State for chat workflow."""

    message_history: list[dict[str, str]] = None
    current_message: ChatMessage | None = None
    project_context: str = ""

    def __post_init__(self):
        """Initialize message_history if None."""
        if self.message_history is None:
            self.message_history = []


@dataclass
class ChatDeps:
    """Dependencies for chat workflow."""

    agent: "Agent"
    project_root: Path | None = None


@dataclass
class ReceiveMessage(BaseNode[ChatState, ChatDeps, None]):
    """Node that receives user messages from adapter."""

    async def run(
        self, ctx: GraphRunContext[ChatState, ChatDeps]
    ) -> "ProcessChat":
        """
        Receive a user message from adapter.

        Args:
            ctx: Graph run context

        Returns:
            Next node to execute
        """
        if not ctx.adapter:
            # No adapter, skip processing
            return End(None)

        # Wait for user message
        async for message in ctx.adapter.receive():
            if message.role == "user":
                ctx.state.current_message = message
                # Add to history
                ctx.state.message_history.append(
                    {"role": "user", "content": message.content}
                )
                return ProcessChat()

        # Should not reach here, but return End if no message
        return End(None)


@dataclass
class ProcessChat(BaseNode[ChatState, ChatDeps, None]):
    """Node that processes chat with agent."""

    async def run(
        self, ctx: GraphRunContext[ChatState, ChatDeps]
    ) -> "ReceiveMessage | End[None]":
        """
        Process chat message with agent.

        Args:
            ctx: Graph run context

        Returns:
            Next node to execute
        """
        if not ctx.deps or not ctx.deps.agent:
            return End(None)

        if not ctx.state.current_message:
            return End(None)

        # Get project context if available
        project_context = ctx.state.project_context
        if not project_context and ctx.deps.project_root:
            from tools.filetree import get_project_tree

            project_context = get_project_tree(ctx.deps.project_root)

        # Convert message history to format expected by agent
        messages = [
            {"role": msg["role"], "content": msg["content"]}
            for msg in ctx.state.message_history
        ]

        # Call agent to generate response
        # Agent will send response chunks via its adapter
        # But we need to ensure adapter is set correctly
        # Since agent's adapter might be different, we'll use ctx.adapter
        # by temporarily setting it on the agent
        original_adapter = ctx.deps.agent.adapter
        if ctx.adapter:
            ctx.deps.agent.adapter = ctx.adapter

        try:
            # Stream response from agent
            response_content = ""
            async for chunk in ctx.deps.agent.chat_stream(
                messages, project_context=project_context
            ):
                response_content += chunk

            # Add assistant response to history
            if response_content:
                ctx.state.message_history.append(
                    {"role": "assistant", "content": response_content}
                )
        finally:
            # Restore original adapter
            ctx.deps.agent.adapter = original_adapter

        # Continue listening for more messages
        return ReceiveMessage()


def create_chat_workflow() -> Graph[ChatState, ChatDeps, None]:
    """
    Create a workflow for processing chat messages.

    Returns:
        Configured workflow graph
    """
    return Graph(nodes=(ReceiveMessage, ProcessChat))
