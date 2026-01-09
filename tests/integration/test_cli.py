"""Integration tests for CLI."""

import asyncio
import os
from unittest.mock import AsyncMock, MagicMock, patch

from prior.cli import main


def test_cli_main_with_model_env():
    """Test CLI main with model environment variable."""
    with patch.dict(os.environ, {"PRIOR_MODEL": "test-model"}):
        with (
            patch("prior.cli.load_dotenv"),
            patch("prior.cli.Agent") as mock_agent_class,
            patch("prior.cli.PriorApp") as mock_app_class,
            patch("prior.cli.start_adapter_server") as mock_start_server,
            patch("prior.cli.WebSocketEventPublisher") as mock_pub_class,
            patch("prior.cli.WebSocketEventSubscriber") as mock_sub_class,
            patch("prior.cli.AgentEventPublisher") as mock_ep_class,
            patch("prior.cli.TuiEventSubscriber") as mock_es_class,
        ):
            mock_agent = MagicMock()
            mock_app_instance = MagicMock()
            mock_bridge = MagicMock()
            mock_publisher = AsyncMock()
            mock_subscriber = AsyncMock()

            mock_agent_class.return_value = mock_agent
            mock_app_class.return_value = mock_app_instance
            mock_start_server.return_value = (mock_bridge, 8000)
            mock_pub_class.return_value = mock_publisher
            mock_sub_class.return_value = mock_subscriber
            mock_ep_class.return_value = MagicMock()
            mock_es_class.return_value = MagicMock()

            main()

            # Verify Agent was created with correct model
            mock_agent_class.assert_called_once_with(model="test-model")
            # PriorApp is called with just agent
            mock_app_class.assert_called_once_with(mock_agent)
            mock_app_instance.run.assert_called_once()


def test_cli_main_default_model():
    """Test CLI main uses default model."""
    with patch.dict(os.environ, {}, clear=True):
        with (
            patch("prior.cli.load_dotenv"),
            patch("prior.cli.Agent") as mock_agent_class,
            patch("prior.cli.PriorApp") as mock_app_class,
            patch("prior.cli.start_adapter_server") as mock_start_server,
            patch("prior.cli.WebSocketEventPublisher") as mock_pub_class,
            patch("prior.cli.WebSocketEventSubscriber") as mock_sub_class,
            patch("prior.cli.AgentEventPublisher") as mock_ep_class,
            patch("prior.cli.TuiEventSubscriber") as mock_es_class,
        ):
            mock_agent = MagicMock()
            mock_app_instance = MagicMock()
            mock_bridge = MagicMock()
            mock_publisher = AsyncMock()
            mock_subscriber = AsyncMock()

            mock_agent_class.return_value = mock_agent
            mock_app_class.return_value = mock_app_instance
            mock_start_server.return_value = (mock_bridge, 8000)
            mock_pub_class.return_value = mock_publisher
            mock_sub_class.return_value = mock_subscriber
            mock_ep_class.return_value = MagicMock()
            mock_es_class.return_value = MagicMock()

            main()

            # Verify default model is used
            mock_agent_class.assert_called_once_with(model="claude-sonnet-4-5")


def test_cli_main_loads_dotenv():
    """Test CLI main loads .env file."""
    with (
        patch("prior.cli.load_dotenv") as mock_load_dotenv,
        patch("prior.cli.Agent") as mock_agent_class,
        patch("prior.cli.PriorApp") as mock_app_class,
        patch("prior.cli.start_adapter_server") as mock_start_server,
        patch("prior.cli.WebSocketEventPublisher") as mock_pub_class,
        patch("prior.cli.WebSocketEventSubscriber") as mock_sub_class,
        patch("prior.cli.AgentEventPublisher") as mock_ep_class,
        patch("prior.cli.TuiEventSubscriber") as mock_es_class,
    ):
        mock_agent = MagicMock()
        mock_app_instance = MagicMock()
        mock_bridge = MagicMock()
        mock_publisher = AsyncMock()
        mock_subscriber = AsyncMock()

        mock_agent_class.return_value = mock_agent
        mock_app_class.return_value = mock_app_instance
        mock_start_server.return_value = (mock_bridge, 8000)
        mock_pub_class.return_value = mock_publisher
        mock_sub_class.return_value = mock_subscriber
        mock_ep_class.return_value = MagicMock()
        mock_es_class.return_value = MagicMock()

        main()

        # Verify load_dotenv was called
        mock_load_dotenv.assert_called_once()
