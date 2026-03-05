"""Tests for CLI utility functions."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from myscout.cli import _default_profile, CONFIG_DIR


class TestDefaultProfile:
    """Tests for _default_profile() — profile.yml vs example.profile.yml resolution."""

    @patch.object(Path, "exists")
    def test_prefers_profile_yml_when_exists(self, mock_exists):
        mock_exists.return_value = True
        result = _default_profile()
        assert result == str(CONFIG_DIR / "profile.yml")

    @patch.object(Path, "exists")
    def test_falls_back_to_example_when_no_profile(self, mock_exists):
        mock_exists.return_value = False
        result = _default_profile()
        assert result == str(CONFIG_DIR / "example.profile.yml")

    def test_returns_string_path(self):
        result = _default_profile()
        assert isinstance(result, str)

    def test_config_dir_is_correct(self):
        """CONFIG_DIR should point to the config/ directory at repo root."""
        assert CONFIG_DIR.name == "config"
        assert CONFIG_DIR.parent.name == "myscout"
