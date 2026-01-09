"""Pytest configuration and fixtures for workflow tests."""

from __future__ import annotations

import os
from pathlib import Path

import pytest


def pytest_addoption(parser):
    """Add custom pytest options."""
    parser.addoption(
        "--save-images",
        action="store_true",
        default=False,
        help="Save generated mermaid images to test output directory",
    )
    parser.addoption(
        "--image-output-dir",
        type=str,
        default="test_output/images",
        help="Directory to save test images (default: test_output/images)",
    )


@pytest.fixture
def image_output_dir(request, tmp_path):
    """
    Fixture that provides directory for saving test images.

    If --save-images is set, saves to the specified output directory.
    Otherwise, uses temporary directory that will be cleaned up.

    Usage:
        def test_my_graph(image_output_dir):
            graph.save_as_image(image_output_dir / "my_graph.png")
    """
    save_images = request.config.getoption("--save-images")

    if save_images:
        # Use specified output directory (or default)
        output_dir = Path(request.config.getoption("--image-output-dir"))
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir
    else:
        # Use temporary directory (will be cleaned up)
        return tmp_path / "images"


@pytest.fixture
def should_save_images(request):
    """
    Fixture that returns whether images should be saved.

    Checks both --save-images flag and SAVE_TEST_IMAGES environment variable.
    """
    save_flag = request.config.getoption("--save-images")
    env_var = os.getenv("SAVE_TEST_IMAGES", "").lower() in ("1", "true", "yes")
    return save_flag or env_var
