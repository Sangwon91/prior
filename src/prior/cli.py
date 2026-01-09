"""CLI entry point for Prior."""

import asyncio
import os
import socket
from contextlib import asynccontextmanager

import uvicorn
from dotenv import load_dotenv

from adapter import Bridge, create_app
from adapter.client import (
    WebSocketEventPublisher,
    WebSocketEventSubscriber,
)
from agent import Agent, AgentEventPublisher
from tui.app import PriorApp
from tui.event_subscriber import TuiEventSubscriber


def find_available_port(
    host: str = "localhost", start_port: int = 8000, max_attempts: int = 100
) -> int:
    """
    Find an available port starting from start_port.

    Args:
        host: Host to bind to
        start_port: Starting port number
        max_attempts: Maximum number of ports to try

    Returns:
        Available port number

    Raises:
        OSError: If no available port is found
    """
    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind((host, port))
                return port
        except OSError:
            continue

    raise OSError(
        f"No available port found in range "
        f"{start_port}-{start_port + max_attempts - 1}"
    )


async def start_adapter_server(
    host: str = "localhost", port: int = 8000
) -> tuple[Bridge, int]:
    """
    Start adapter server in background.

    Finds an available port if the requested port is in use.

    Args:
        host: Server host
        port: Preferred server port (will find available if in use)

    Returns:
        Tuple of (Bridge instance, actual port used)
    """
    # Find available port
    actual_port = find_available_port(host, port)

    bridge = Bridge()
    app = create_app(bridge)

    config = uvicorn.Config(
        app, host=host, port=actual_port, log_level="warning"
    )
    server = uvicorn.Server(config)

    # Start server in background
    asyncio.create_task(server.serve())

    # Wait a bit for server to start
    await asyncio.sleep(0.1)

    return bridge, actual_port


def main() -> None:
    """Main entry point for Prior CLI."""
    # Load environment variables from .env file
    load_dotenv()

    # Get model from environment (default: claude-sonnet-4-5)
    # LiteLLM will automatically detect API keys from vendor-specific env vars
    # (e.g., OPENAI_API_KEY, ANTHROPIC_API_KEY, etc.)
    model = os.getenv("PRIOR_MODEL", "claude-sonnet-4-5")

    # Get adapter server settings
    adapter_host = os.getenv("PRIOR_ADAPTER_HOST", "localhost")
    adapter_port = int(os.getenv("PRIOR_ADAPTER_PORT", "8000"))

    # Initialize agent
    agent = Agent(model=model)

    # Setup adapter and WebSocket connections
    async def setup_connections():
        # Start adapter server (finds available port if needed)
        bridge, actual_port = await start_adapter_server(
            adapter_host, adapter_port
        )

        # Create WebSocket clients with actual port
        agent_ws_uri = f"ws://{adapter_host}:{actual_port}/ws/agent"
        tui_ws_uri = f"ws://{adapter_host}:{actual_port}/ws/tui"

        # Setup Agent event publisher
        agent_publisher = WebSocketEventPublisher(agent_ws_uri)
        await agent_publisher.connect()

        event_publisher = AgentEventPublisher(agent_publisher)

        # Setup TUI event subscriber
        tui_subscriber = WebSocketEventSubscriber(tui_ws_uri)
        await tui_subscriber.connect()

        event_subscriber = TuiEventSubscriber(tui_subscriber)

        return agent, event_publisher, event_subscriber

    # Run setup in async context
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    agent, event_publisher, event_subscriber = loop.run_until_complete(
        setup_connections()
    )

    # Create and run app
    app = PriorApp(agent)
    app.run()


if __name__ == "__main__":
    main()
