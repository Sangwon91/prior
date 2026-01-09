"""Tests for protocol models."""

import pytest

from protocol.models import (
    ControlCommand,
    NodeProgress,
    WorkflowCompleted,
    WorkflowError,
    WorkflowEvent,
    WorkflowStarted,
)


def test_workflow_started():
    """Test WorkflowStarted model."""
    event = WorkflowStarted(workflow_id="test-123")
    assert event.workflow_id == "test-123"
    assert event.timestamp > 0


def test_node_progress():
    """Test NodeProgress model."""
    progress = NodeProgress(
        workflow_id="test-123",
        node_id="node-1",
        state="running",
        progress=0.5,
    )
    assert progress.workflow_id == "test-123"
    assert progress.node_id == "node-1"
    assert progress.state == "running"
    assert progress.progress == 0.5


def test_workflow_event_with_started():
    """Test WorkflowEvent with WorkflowStarted."""
    started = WorkflowStarted(workflow_id="test-123")
    event = WorkflowEvent(
        workflow_id="test-123",
        event_type="started",
        data=started,
    )
    assert event.workflow_id == "test-123"
    assert event.event_type == "started"
    assert isinstance(event.data, WorkflowStarted)


def test_workflow_event_with_progress():
    """Test WorkflowEvent with NodeProgress."""
    progress = NodeProgress(
        workflow_id="test-123",
        node_id="node-1",
        state="running",
    )
    event = WorkflowEvent(
        workflow_id="test-123",
        event_type="progress",
        data=progress,
    )
    assert event.event_type == "progress"
    assert isinstance(event.data, NodeProgress)


def test_control_command():
    """Test ControlCommand model."""
    command = ControlCommand(
        workflow_id="test-123",
        command="cancel",
    )
    assert command.workflow_id == "test-123"
    assert command.command == "cancel"
    assert command.timestamp > 0


def test_json_serialization():
    """Test JSON serialization of models."""
    event = WorkflowEvent(
        workflow_id="test-123",
        event_type="started",
        data=WorkflowStarted(workflow_id="test-123"),
    )
    json_str = event.model_dump_json()
    assert isinstance(json_str, str)
    assert "test-123" in json_str

    # Test deserialization
    parsed = WorkflowEvent.model_validate_json(json_str)
    assert parsed.workflow_id == event.workflow_id
    assert parsed.event_type == event.event_type


def test_json_deserialization():
    """Test JSON deserialization of models."""
    json_str = (
        '{"workflow_id":"test-123","command":"cancel","timestamp":1234567890.0}'
    )
    command = ControlCommand.model_validate_json(json_str)
    assert command.workflow_id == "test-123"
    assert command.command == "cancel"
