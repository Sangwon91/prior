# Protocol Package

Protocol definitions for agent-tui communication using Pydantic models.

This package provides:
- Pydantic models for chat messages
- Type-safe message definitions

## Usage

```python
from protocol.models import ChatMessage

# Create chat messages
user_message = ChatMessage(role="user", content="Hello")
assistant_message = ChatMessage(role="assistant", content="Hi there")
system_message = ChatMessage(role="system", content="System prompt")
```
