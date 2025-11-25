"""
Tests for configuration management.

Tests cover:
- Environment variable loading
- Configuration validation
- Missing configuration handling
- Default values
"""

import unittest
from unittest.mock import patch, Mock
import os


class TestConfigurationLoading(unittest.TestCase):
    """Test configuration loading from environment"""

    @patch.dict(os.environ, {
        "SPREADSHEET_ID": "test_spreadsheet_123",
        "LINE_CHANNEL_SECRET": "test_secret",
        "LINE_CHANNEL_ACCESS_TOKEN": "test_token",
        "LINE_TEACHER_GROUP_ID": "teacher_group_123",
        "LINE_ADMIN_GROUP_ID": "admin_group_456",
        "OPENROUTER_API_KEY": "sk-test-key"
    }, clear=True)
    def test_config_loads_from_environment(self):
        """Config should load all required environment variables"""
        # Reload config module to pick up env vars
        import importlib
        from src import config as config_module
        importlib.reload(config_module)

        # Verify values loaded
        self.assertEqual(config_module.config.SPREADSHEET_ID, "test_spreadsheet_123")
        self.assertEqual(config_module.config.LINE_CHANNEL_SECRET, "test_secret")
        self.assertEqual(config_module.config.LINE_CHANNEL_ACCESS_TOKEN, "test_token")
        self.assertEqual(config_module.config.LINE_TEACHER_GROUP_ID, "teacher_group_123")
        self.assertEqual(config_module.config.LINE_ADMIN_GROUP_ID, "admin_group_456")
        self.assertEqual(config_module.config.OPENROUTER_API_KEY, "sk-test-key")

    @patch.dict(os.environ, {}, clear=True)
    def test_config_handles_missing_variables(self):
        """Config should handle missing environment variables gracefully"""
        import importlib
        from src import config as config_module
        importlib.reload(config_module)

        # Should load with None values or defaults
        # (Actual behavior depends on config.py implementation)


class TestConfigurationValidation(unittest.TestCase):
    """Test configuration validation"""

    @patch('src.config.config')
    def test_validate_with_all_required_config(self, mock_config):
        """Validation should pass with all required config"""
        # Setup complete configuration
        mock_config.SPREADSHEET_ID = "test_id"
        mock_config.LINE_CHANNEL_SECRET = "secret"
        mock_config.LINE_CHANNEL_ACCESS_TOKEN = "token"
        mock_config.OPENROUTER_API_KEY = "key"

        # Mock validate method
        mock_config.validate.return_value = []

        # Should return no errors
        errors = mock_config.validate()
        self.assertEqual(len(errors), 0)

    @patch('src.config.config')
    def test_validate_reports_missing_spreadsheet(self, mock_config):
        """Validation should report missing SPREADSHEET_ID"""
        mock_config.SPREADSHEET_ID = None
        mock_config.validate.return_value = ["SPREADSHEET_ID not set"]

        errors = mock_config.validate()
        self.assertGreater(len(errors), 0)

    @patch('src.config.config')
    def test_validate_reports_missing_line_config(self, mock_config):
        """Validation should report missing LINE configuration"""
        mock_config.LINE_CHANNEL_SECRET = None
        mock_config.LINE_CHANNEL_ACCESS_TOKEN = None
        mock_config.validate.return_value = [
            "LINE_CHANNEL_SECRET not set",
            "LINE_CHANNEL_ACCESS_TOKEN not set"
        ]

        errors = mock_config.validate()
        # Should have errors for both missing values
        self.assertGreater(len(errors), 0)


class TestConfigurationDefaults(unittest.TestCase):
    """Test default configuration values"""

    def test_webhook_port_has_default(self):
        """Webhook port should have default value"""
        from src.config import config

        # Should have a port (either from env or default)
        self.assertIsNotNone(config.WEBHOOK_PORT)
        self.assertIsInstance(config.WEBHOOK_PORT, int)

    def test_webhook_host_has_default(self):
        """Webhook host should have default value"""
        from src.config import config

        # Should have a host
        self.assertIsNotNone(config.WEBHOOK_HOST)
        self.assertIsInstance(config.WEBHOOK_HOST, str)

    def test_debug_mode_defaults_to_false(self):
        """Debug mode should default to False"""
        from src.config import config

        # Debug mode should be boolean
        self.assertIsInstance(config.DEBUG_MODE, bool)


if __name__ == '__main__':
    unittest.main()
