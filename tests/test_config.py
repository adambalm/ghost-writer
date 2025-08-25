"""
Tests for configuration management
"""
import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, mock_open

from src.utils.config import Config


class TestConfig:
    """Test the Config class"""

    def test_config_initialization_with_defaults(self):
        """Test Config initializes with default values"""
        config = Config()
        
        assert config.get("database.path") == "data/database/ghost_writer.db"
        assert config.get("ocr.default_provider") == "hybrid"
        assert config.get("embeddings.model_name") == "all-MiniLM-L6-v2"

    def test_config_initialization_with_custom_path(self):
        """Test Config loads from custom path"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
database:
  path: "/tmp/test.db"
ocr:
  default_provider: "google_vision"
""")
            config_path = f.name

        try:
            config = Config(config_path)
            assert config.get("database.path") == "/tmp/test.db"
            assert config.get("ocr.default_provider") == "google_vision"
        finally:
            os.unlink(config_path)

    def test_config_nonexistent_file_uses_defaults(self):
        """Test Config falls back to defaults when file doesn't exist"""
        config = Config("/nonexistent/path/config.yaml")
        assert config.get("database.path") == "data/database/ghost_writer.db"

    def test_config_get_with_default(self):
        """Test getting config values with defaults"""
        config = Config()
        
        # Existing key
        assert config.get("database.path") == "data/database/ghost_writer.db"
        
        # Non-existing key with default
        assert config.get("nonexistent.key", "default_value") == "default_value"
        
        # Non-existing key without default
        assert config.get("nonexistent.key") is None

    def test_config_set_value(self):
        """Test setting config values"""
        config = Config()
        
        config.set("new.nested.value", "test")
        assert config.get("new.nested.value") == "test"

    def test_environment_overrides(self):
        """Test environment variable overrides"""
        with patch.dict(os.environ, {
            'GHOST_WRITER_DB_PATH': '/custom/db/path.db',
            'GHOST_WRITER_LOG_LEVEL': 'DEBUG',
            'GHOST_WRITER_DAILY_BUDGET': '10.50'
        }):
            config = Config()
            assert config.get("database.path") == '/custom/db/path.db'
            assert config.get("logging.level") == 'DEBUG'
            assert config.get("ocr.providers.hybrid.cost_limit_per_day") == 10.50

    def test_invalid_budget_environment_variable(self):
        """Test invalid budget environment variable is ignored"""
        with patch.dict(os.environ, {'GHOST_WRITER_DAILY_BUDGET': 'invalid'}):
            config = Config()
            # Should keep default value
            assert config.get("ocr.providers.hybrid.cost_limit_per_day") == 5.00

    def test_get_database_config(self):
        """Test getting database configuration"""
        config = Config()
        db_config = config.get_database_config()
        
        assert "path" in db_config
        assert db_config["path"] == "data/database/ghost_writer.db"

    def test_get_ocr_config_default_provider(self):
        """Test getting OCR config for default provider"""
        config = Config()
        ocr_config = config.get_ocr_config()
        
        assert ocr_config["provider"] == "hybrid"
        assert isinstance(ocr_config, dict)

    def test_get_ocr_config_specific_provider(self):
        """Test getting OCR config for specific provider"""
        config = Config()
        ocr_config = config.get_ocr_config("tesseract")
        
        assert ocr_config["provider"] == "tesseract"
        assert isinstance(ocr_config, dict)

    def test_get_embedding_config(self):
        """Test getting embedding configuration"""
        config = Config()
        embedding_config = config.get_embedding_config()
        
        assert embedding_config["model_name"] == "all-MiniLM-L6-v2"
        assert embedding_config["dimension"] == 384

    def test_is_debug_mode(self):
        """Test debug mode detection"""
        config = Config()
        
        # Default should be False
        assert not config.is_debug_mode()
        
        # Test with environment variable
        with patch.dict(os.environ, {'GHOST_WRITER_DEBUG': 'true'}):
            assert config.is_debug_mode()
        
        # Test with config setting
        config.set("logging.level", "DEBUG")
        assert config.is_debug_mode()

    def test_validate_config(self):
        """Test config validation"""
        config = Config()
        
        # Should pass validation with defaults
        assert config.validate_config()

    def test_save_config(self):
        """Test saving configuration to file"""
        config = Config()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            temp_path = f.name

        try:
            assert config.save_config(temp_path)
            assert Path(temp_path).exists()
            
            # Load saved config and verify
            new_config = Config(temp_path)
            assert new_config.get("database.path") == config.get("database.path")
        finally:
            if Path(temp_path).exists():
                os.unlink(temp_path)

    def test_config_str_representation(self):
        """Test string representation of config"""
        config = Config()
        str_repr = str(config)
        
        assert "Config(" in str_repr
        assert "hybrid" in str_repr

    def test_yaml_load_error_fallback(self):
        """Test fallback to defaults when YAML loading fails"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: content: [")
            config_path = f.name

        try:
            config = Config(config_path)
            # Should fall back to defaults
            assert config.get("database.path") == "data/database/ghost_writer.db"
        finally:
            os.unlink(config_path)


class TestConfigEdgeCases:
    """Test edge cases and error conditions"""

    def test_deep_nested_get_and_set(self):
        """Test deeply nested config operations"""
        config = Config()
        
        config.set("very.deeply.nested.config.value", "test")
        assert config.get("very.deeply.nested.config.value") == "test"

    def test_config_validation_with_invalid_paths(self):
        """Test validation with invalid directory paths"""
        config = Config()
        
        # Set invalid path that can't be created (permission denied)
        config.set("database.path", "/root/cannot_create/test.db")
        
        # Validation should handle this gracefully
        # (In practice, mkdir with exist_ok=True will create what it can)
        result = config.validate_config()
        # This might pass or fail depending on permissions, but shouldn't crash
        assert isinstance(result, bool)

    def test_get_config_methods_return_empty_dict_on_missing_section(self):
        """Test that config getter methods handle missing sections"""
        config = Config()
        
        # Clear the config to simulate missing sections
        config._config = {}
        
        assert config.get_database_config() == {}
        assert config.get_embedding_config() == {}
        assert config.get_faiss_config() == {}
        assert config.get_llm_config() == {}
        assert config.get_style_config() == {}
        assert config.get_processing_config() == {}
        assert config.get_logging_config() == {}
        assert config.get_cost_config() == {}
        assert config.get_search_config() == {}