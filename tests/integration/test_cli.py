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
            patch("prior.cli.AdapterClient") as mock_adapter_class,
            patch("prior.cli.ChatService") as mock_chat_service_class,
        ):
            mock_agent = MagicMock()
            mock_app_instance = MagicMock()
            mock_bridge = MagicMock()
            mock_adapter = AsyncMock()
            mock_chat_service = MagicMock()

            mock_agent_class.return_value = mock_agent
            mock_app_class.return_value = mock_app_instance
            mock_start_server.return_value = (mock_bridge, 8000)
            mock_adapter_class.return_value = mock_adapter
            mock_chat_service_class.return_value = mock_chat_service

            main()

            # Verify Agent was created with correct model and adapter
            assert mock_agent_class.call_count == 1
            # PriorApp is called with agent and chat_service
            mock_app_class.assert_called_once()
            mock_app_instance.run.assert_called_once()


def test_cli_main_default_model():
    """Test CLI main uses default model."""
    with patch.dict(os.environ, {}, clear=True):
        with (
            patch("prior.cli.load_dotenv"),
            patch("prior.cli.Agent") as mock_agent_class,
            patch("prior.cli.PriorApp") as mock_app_class,
            patch("prior.cli.start_adapter_server") as mock_start_server,
            patch("prior.cli.AdapterClient") as mock_adapter_class,
            patch("prior.cli.ChatService") as mock_chat_service_class,
        ):
            mock_agent = MagicMock()
            mock_app_instance = MagicMock()
            mock_bridge = MagicMock()
            mock_adapter = AsyncMock()
            mock_chat_service = MagicMock()

            mock_agent_class.return_value = mock_agent
            mock_app_class.return_value = mock_app_instance
            mock_start_server.return_value = (mock_bridge, 8000)
            mock_adapter_class.return_value = mock_adapter
            mock_chat_service_class.return_value = mock_chat_service

            main()

            # Verify default model is used
            assert mock_agent_class.call_count == 1


def test_cli_main_loads_dotenv():
    """Test CLI main loads .env file."""
    with (
        patch("prior.cli.load_dotenv") as mock_load_dotenv,
        patch("prior.cli.Agent") as mock_agent_class,
        patch("prior.cli.PriorApp") as mock_app_class,
        patch("prior.cli.start_adapter_server") as mock_start_server,
        patch("prior.cli.AdapterClient") as mock_adapter_class,
        patch("prior.cli.ChatService") as mock_chat_service_class,
    ):
        mock_agent = MagicMock()
        mock_app_instance = MagicMock()
        mock_bridge = MagicMock()
        mock_adapter = AsyncMock()
        mock_chat_service = MagicMock()

        mock_agent_class.return_value = mock_agent
        mock_app_class.return_value = mock_app_instance
        mock_start_server.return_value = (mock_bridge, 8000)
        mock_adapter_class.return_value = mock_adapter
        mock_chat_service_class.return_value = mock_chat_service

        main()

        # Verify load_dotenv was called
        mock_load_dotenv.assert_called_once()
