"""CLI entry point for Prior."""

import os

from dotenv import load_dotenv

from .core.agent import Agent
from .tui.app import PriorApp


def main() -> None:
    """Main entry point for Prior CLI."""
    # Load environment variables from .env file
    load_dotenv()

    # Get model from environment (default: claude-sonnet-4-5)
    # LiteLLM will automatically detect API keys from vendor-specific env vars
    # (e.g., OPENAI_API_KEY, ANTHROPIC_API_KEY, etc.)
    model = os.getenv("PRIOR_MODEL", "claude-sonnet-4-5")

    # Initialize agent
    agent = Agent(model=model)

    # Create and run app
    app = PriorApp(agent)
    app.run()


if __name__ == "__main__":
    main()

