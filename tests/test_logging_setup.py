"""
Tests for logging setup and utilities
"""
import json
import logging
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from src.utils.logging_setup import GhostWriterLogger, log_calls, get_logger


class TestGhostWriterLogger:
    """Test the GhostWriterLogger class"""

    def test_logger_initialization_default_config(self):
        """Test logger initializes with default configuration"""
        logger = GhostWriterLogger("test_logger")
        
        assert logger.name == "test_logger"
        assert logger.config["level"] == "INFO"
        assert logger.config["file_path"] == "data/logs/ghost_writer.log"
        assert logger.logger.name == "test_logger"

    def test_logger_initialization_custom_config(self):
        """Test logger initializes with custom configuration"""
        config = {
            "level": "DEBUG",
            "file_path": "/tmp/test.log",
            "max_file_size": "5MB",
            "backup_count": 3
        }
        
        logger = GhostWriterLogger("custom_logger", config)
        
        assert logger.config["level"] == "DEBUG"
        assert logger.config["file_path"] == "/tmp/test.log"
        assert logger.config["max_file_size"] == "5MB"
        assert logger.config["backup_count"] == 3

    def test_size_parsing(self):
        """Test size string parsing"""
        logger = GhostWriterLogger("test")
        
        assert logger._parse_size("10MB") == 10 * 1024 * 1024
        assert logger._parse_size("5KB") == 5 * 1024
        assert logger._parse_size("1GB") == 1 * 1024 * 1024 * 1024
        assert logger._parse_size("100") == 100

    def test_log_function_call(self):
        """Test function call logging"""
        with patch('src.utils.logging_setup.logging.getLogger') as mock_get_logger:
            mock_logger = MagicMock()
            mock_logger.isEnabledFor.return_value = True
            mock_get_logger.return_value = mock_logger
            
            logger = GhostWriterLogger("test")
            logger.logger = mock_logger
            
            logger.log_function_call("test_function", {"arg1": "value1"}, {"kwarg1": "value2"})
            
            mock_logger.debug.assert_called_once()
            call_args = mock_logger.debug.call_args[0][0]
            assert "CALL test_function" in call_args

    def test_log_function_result(self):
        """Test function result logging"""
        with patch('src.utils.logging_setup.logging.getLogger') as mock_get_logger:
            mock_logger = MagicMock()
            mock_logger.isEnabledFor.return_value = True
            mock_get_logger.return_value = mock_logger
            
            logger = GhostWriterLogger("test")
            logger.logger = mock_logger
            
            result = ["item1", "item2", "item3"]
            logger.log_function_result("test_function", result, 0.5)
            
            mock_logger.debug.assert_called_once()
            call_args = mock_logger.debug.call_args[0][0]
            assert "RESULT test_function" in call_args

    def test_log_performance(self):
        """Test performance logging"""
        with patch('src.utils.logging_setup.logging.getLogger') as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            
            logger = GhostWriterLogger("test")
            logger.logger = mock_logger
            
            logger.log_performance("test_operation", 1.5, 100)
            
            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args[0][0]
            assert "PERFORMANCE" in call_args
            assert "test_operation" in call_args

    def test_log_cost_tracking(self):
        """Test cost tracking logging"""
        with patch('src.utils.logging_setup.logging.getLogger') as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            
            logger = GhostWriterLogger("test")
            logger.logger = mock_logger
            
            logger.log_cost_tracking("openai", 0.05, "text_extraction")
            
            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args[0][0]
            assert "COST" in call_args
            assert "openai" in call_args

    def test_log_error_with_context(self):
        """Test error logging with context"""
        with patch('src.utils.logging_setup.logging.getLogger') as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            
            logger = GhostWriterLogger("test")
            logger.logger = mock_logger
            
            error = ValueError("Test error")
            context = {"operation": "test", "file": "test.txt"}
            
            logger.log_error_with_context(error, context)
            
            mock_logger.error.assert_called_once()
            call_args = mock_logger.error.call_args[0][0]
            assert "ERROR" in call_args
            assert "ValueError" in call_args

    def test_get_logger_method(self):
        """Test getting the underlying logger"""
        logger = GhostWriterLogger("test")
        underlying_logger = logger.get_logger()
        
        assert isinstance(underlying_logger, logging.Logger)
        assert underlying_logger.name == "test"

    def test_debug_vs_normal_formatting(self):
        """Test different formatting for debug vs normal levels"""
        # DEBUG level should use debug format
        debug_config = {"level": "DEBUG"}
        debug_logger = GhostWriterLogger("debug_test", debug_config)
        
        # INFO level should use normal format
        info_config = {"level": "INFO"}
        info_logger = GhostWriterLogger("info_test", info_config)
        
        # Both should initialize without error
        assert debug_logger.config["level"] == "DEBUG"
        assert info_logger.config["level"] == "INFO"


class TestLogCallsDecorator:
    """Test the log_calls decorator"""

    def test_log_calls_decorator_success(self):
        """Test decorator logs successful function calls"""
        with patch('src.utils.logging_setup.logging.getLogger') as mock_get_logger:
            mock_logger = MagicMock()
            mock_logger.isEnabledFor.return_value = True
            mock_get_logger.return_value = mock_logger
            
            @log_calls("test_logger")
            def test_function(x, y=10):
                return x + y
            
            result = test_function(5, y=15)
            
            assert result == 20
            assert mock_logger.debug.call_count == 2  # Call and success logs

    def test_log_calls_decorator_exception(self):
        """Test decorator logs function exceptions"""
        with patch('src.utils.logging_setup.logging.getLogger') as mock_get_logger:
            mock_logger = MagicMock()
            mock_logger.isEnabledFor.return_value = True
            mock_get_logger.return_value = mock_logger
            
            @log_calls("test_logger")
            def failing_function():
                raise ValueError("Test error")
            
            with pytest.raises(ValueError):
                failing_function()
            
            mock_logger.error.assert_called_once()
            error_call = mock_logger.error.call_args[0][0]
            assert "FAILED failing_function" in error_call


class TestGetLoggerFunction:
    """Test the get_logger function"""

    def test_get_logger_default_name(self):
        """Test getting logger with default name"""
        logger = get_logger()
        
        assert isinstance(logger, GhostWriterLogger)
        assert logger.name == "ghost_writer"

    def test_get_logger_custom_name(self):
        """Test getting logger with custom name"""
        logger = get_logger("custom_logger")
        
        assert isinstance(logger, GhostWriterLogger)
        assert logger.name == "custom_logger"


class TestDefaultLogger:
    """Test the default logger instance"""

    def test_default_logger_exists(self):
        """Test that default logger is created"""
        from src.utils.logging_setup import default_logger, logger
        
        assert default_logger is not None
        assert logger is not None
        assert isinstance(logger, logging.Logger)


class TestLoggingEdgeCases:
    """Test edge cases and error conditions"""

    def test_logging_with_none_values(self):
        """Test logging functions handle None values gracefully"""
        with patch('src.utils.logging_setup.logging.getLogger') as mock_get_logger:
            mock_logger = MagicMock()
            mock_logger.isEnabledFor.return_value = True
            mock_get_logger.return_value = mock_logger
            
            logger = GhostWriterLogger("test")
            logger.logger = mock_logger
            
            # Should not crash with None values
            logger.log_function_call("test", None, None)
            logger.log_function_result("test", None, None)
            logger.log_performance("test", 1.0, None)
            logger.log_error_with_context(Exception("test"), None)
            
            # Should have made calls
            assert mock_logger.debug.call_count >= 2
            assert mock_logger.info.call_count >= 1
            assert mock_logger.error.call_count >= 1

    def test_performance_logging_no_items_processed(self):
        """Test performance logging without items processed"""
        with patch('src.utils.logging_setup.logging.getLogger') as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            
            logger = GhostWriterLogger("test")
            logger.logger = mock_logger
            
            logger.log_performance("test_operation", 2.0)
            
            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args[0][0]
            assert "test_operation" in call_args
            # Should not include items_per_second when no items provided

    def test_function_result_with_different_types(self):
        """Test function result logging with different data types"""
        with patch('src.utils.logging_setup.logging.getLogger') as mock_get_logger:
            mock_logger = MagicMock()
            mock_logger.isEnabledFor.return_value = True
            mock_get_logger.return_value = mock_logger
            
            logger = GhostWriterLogger("test")
            logger.logger = mock_logger
            
            # Test with string (should not include length)
            logger.log_function_result("test", "string_result", 0.1)
            
            # Test with list (should include length)
            logger.log_function_result("test", [1, 2, 3], 0.2)
            
            # Test with dict (should include length)
            logger.log_function_result("test", {"key": "value"}, 0.3)
            
            assert mock_logger.debug.call_count == 3