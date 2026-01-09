"""Integration tests for CLI."""

import os
from unittest.mock import MagicMock, patch


from prior.cli import main


def test_cli_main_with_model_env():
    """Test CLI main with model environment variable."""
    with patch.dict(os.environ, {"PRIOR_MODEL": "test-model"}):
        with (
            patch("prior.cli.load_dotenv"),
            patch("prior.cli.Agent") as mock_agent_class,
            patch("prior.cli.PriorApp") as mock_app_class,
        ):
            mock_agent = MagicMock()
            mock_app_instance = MagicMock()

            mock_agent_class.return_value = mock_agent
            mock_app_class.return_value = mock_app_instance

            main()

            # Verify Agent was created with correct model
            mock_agent_class.assert_called_once_with(model="test-model")
            # PriorApp is called with just agent, project_root defaults to None
            mock_app_class.assert_called_once_with(mock_agent)
            mock_app_instance.run.assert_called_once()


def test_cli_main_default_model():
    """Test CLI main uses default model."""
    with patch.dict(os.environ, {}, clear=True):
        with (
            patch("prior.cli.load_dotenv"),
            patch("prior.cli.Agent") as mock_agent_class,
            patch("prior.cli.PriorApp") as mock_app_class,
        ):
            mock_agent = MagicMock()
            mock_app_instance = MagicMock()

            mock_agent_class.return_value = mock_agent
            mock_app_class.return_value = mock_app_instance

            main()

            # Verify default model is used
            mock_agent_class.assert_called_once_with(model="claude-sonnet-4-5")


def test_cli_main_loads_dotenv():
    """Test CLI main loads .env file."""
    with (
        patch("prior.cli.load_dotenv") as mock_load_dotenv,
        patch("prior.cli.Agent") as mock_agent_class,
        patch("prior.cli.PriorApp") as mock_app_class,
    ):
        mock_agent = MagicMock()
        mock_app_instance = MagicMock()

        mock_agent_class.return_value = mock_agent
        mock_app_class.return_value = mock_app_instance

        main()

        # Verify load_dotenv was called
        mock_load_dotenv.assert_called_once()
