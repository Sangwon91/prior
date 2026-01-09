# Protocol Package

Protocol definitions for agent-tui communication using Pydantic models.

This package provides:
- Pydantic models for workflow events and control commands
- Protocol interfaces for event publishing and subscription
- Type-safe message definitions

## Usage

```python
from protocol.models import WorkflowEvent, ControlCommand
from protocol.interfaces import EventPublisher, EventSubscriber

# Create events
event = WorkflowEvent(...)
command = ControlCommand(...)

# Use interfaces
publisher: EventPublisher = ...
subscriber: EventSubscriber = ...
```

