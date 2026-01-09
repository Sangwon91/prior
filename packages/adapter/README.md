# Adapter Package

WebSocket adapter implementation for agent-tui communication using FastAPI.

This package provides:
- FastAPI WebSocket server
- JSON message serialization/deserialization
- Bridge between Agent and TUI

## Usage

```python
from adapter.server import create_app
from adapter.bridge import Bridge

app = create_app()
bridge = Bridge()
```

