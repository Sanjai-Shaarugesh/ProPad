"""Tests for configuration module."""

import unittest
from pathlib import Path
from src import config


class TestConfig(unittest.TestCase):
    """Test configuration paths and constants."""

    def test_app_id(self):
        """Test app ID is set correctly."""
        self.assertEqual(config.APP_ID, "io.github.sanjai.ProPad")

    def test_paths_exist(self):
        """Test that path objects are Path instances."""
        self.assertIsInstance(config.APP_DIR, Path)
        self.assertIsInstance(config.UI_DIR, Path)
        self.assertIsInstance(config.DATA_DIR, Path)

    def test_ui_dir_exists_in_dev(self):
        """Test UI directory exists in development mode."""
        if not Path("/app/share/ProPad").exists():
            # In development mode
            self.assertTrue(config.UI_DIR.parent.exists())


class TestUtils(unittest.TestCase):
    """Test utility functions."""

    def test_example(self):
        """Example test case."""
        self.assertTrue(True)
