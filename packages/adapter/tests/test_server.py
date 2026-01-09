"""Tests for server module."""

import pytest

from adapter.bridge import Bridge
from adapter.server import create_app


def test_create_app_without_bridge():
    """Test create_app without bridge."""
    app = create_app()

    assert app is not None
    assert app.title == "Prior Adapter"


def test_create_app_with_bridge():
    """Test create_app with bridge."""
    bridge = Bridge()
    app = create_app(bridge)

    assert app is not None
    assert app.title == "Prior Adapter"
