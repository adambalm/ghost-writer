"""
Tests for debugging utilities and helpers
"""
import time
from unittest.mock import patch, MagicMock
import pytest

from src.utils.debug_helpers import DebugProfiler, StateInspector


class TestDebugProfiler:
    """Test the DebugProfiler class"""

    def test_profiler_initialization(self):
        """Test profiler initializes correctly"""
        profiler = DebugProfiler()
        
        assert profiler.timings == {}
        assert profiler.call_counts == {}

    def test_profile_decorator(self):
        """Test profile decorator functionality"""
        profiler = DebugProfiler()
        
        @profiler.profile
        def test_function(x, y=10):
            time.sleep(0.01)  # Small sleep for measurable time
            return x + y
        
        result = test_function(5, y=15)
        
        assert result == 20
        func_name = f"{test_function.__module__}.{test_function.__name__}"
        assert func_name in profiler.call_counts
        assert profiler.call_counts[func_name] == 1
        assert func_name in profiler.timings

    def test_profile_decorator_multiple_calls(self):
        """Test profile decorator with multiple calls"""
        profiler = DebugProfiler()
        
        @profiler.profile
        def repeated_function():
            return "result"
        
        # Call multiple times
        for _ in range(3):
            repeated_function()
        
        func_name = f"{repeated_function.__module__}.{repeated_function.__name__}"
        assert profiler.call_counts[func_name] == 3
        assert len(profiler.timings[func_name]) == 3

    def test_profile_decorator_with_exception(self):
        """Test profile decorator when function raises exception"""
        profiler = DebugProfiler()
        
        @profiler.profile
        def failing_function():
            raise ValueError("Test error")
        
        with pytest.raises(ValueError):
            failing_function()
        
        func_name = f"{failing_function.__module__}.{failing_function.__name__}"
        assert profiler.call_counts[func_name] == 1
        assert func_name in profiler.timings

    def test_get_stats(self):
        """Test getting profiling statistics"""
        profiler = DebugProfiler()
        
        @profiler.profile
        def stats_test_function():
            time.sleep(0.01)
            return "test"
        
        # Call function a few times
        stats_test_function()
        stats_test_function()
        
        stats = profiler.get_stats()
        
        assert isinstance(stats, dict)
        func_name = f"{stats_test_function.__module__}.{stats_test_function.__name__}"
        assert func_name in stats
        
        func_stats = stats[func_name]
        assert 'calls' in func_stats
        assert 'total_time' in func_stats
        assert 'avg_time' in func_stats
        assert 'min_time' in func_stats
        assert 'max_time' in func_stats
        assert func_stats['calls'] == 2

    def test_print_stats(self):
        """Test printing profiling statistics"""
        profiler = DebugProfiler()
        
        @profiler.profile
        def print_stats_function():
            return "test"
        
        print_stats_function()
        
        # Test that print_stats doesn't crash
        with patch('builtins.print') as mock_print:
            profiler.print_stats()
            mock_print.assert_called()

    def test_reset_stats(self):
        """Test resetting profiling statistics"""
        profiler = DebugProfiler()
        
        @profiler.profile
        def reset_test_function():
            return "test"
        
        reset_test_function()
        
        # Verify stats exist
        assert profiler.call_counts
        assert profiler.timings
        
        # Reset and verify empty
        profiler.reset()
        assert profiler.call_counts == {}
        assert profiler.timings == {}


class TestStateInspector:
    """Test the StateInspector class"""

    def test_log_function_args(self):
        """Test function arguments logging"""
        with patch('src.utils.debug_helpers.logger') as mock_logger:
            args = ("arg1", 42, "arg3")
            kwargs = {"key1": "value1", "key2": 100}
            
            StateInspector.log_function_args("test_function", args, kwargs)
            
            mock_logger.debug.assert_called_once()
            call_args = mock_logger.debug.call_args[0][0]
            assert "ARGS test_function" in call_args

    def test_log_variable_state_simple_value(self):
        """Test variable state logging with simple value"""
        with patch('src.utils.debug_helpers.logger') as mock_logger:
            StateInspector.log_variable_state("test_var", "simple_value", "test_context")
            
            mock_logger.debug.assert_called_once()
            call_args = mock_logger.debug.call_args[0][0]
            assert "VAR test_var" in call_args

    def test_log_variable_state_with_list(self):
        """Test variable state logging with list value"""
        with patch('src.utils.debug_helpers.logger') as mock_logger:
            test_list = ["item1", "item2", "item3", "item4", "item5"]
            
            StateInspector.log_variable_state("test_list", test_list, "list_context")
            
            mock_logger.debug.assert_called_once()
            call_args = mock_logger.debug.call_args[0][0]
            assert "VAR test_list" in call_args

    def test_log_variable_state_with_dict(self):
        """Test variable state logging with dictionary value"""
        with patch('src.utils.debug_helpers.logger') as mock_logger:
            test_dict = {"key1": "value1", "key2": "value2", "key3": "value3", "key4": "value4"}
            
            StateInspector.log_variable_state("test_dict", test_dict, "dict_context")
            
            mock_logger.debug.assert_called_once()
            call_args = mock_logger.debug.call_args[0][0]
            assert "VAR test_dict" in call_args

    def test_log_variable_state_with_long_string(self):
        """Test variable state logging with long string"""
        with patch('src.utils.debug_helpers.logger') as mock_logger:
            long_string = "a" * 150  # String longer than 100 chars
            
            StateInspector.log_variable_state("long_string", long_string, "string_context")
            
            mock_logger.debug.assert_called_once()
            call_args = mock_logger.debug.call_args[0][0]
            assert "VAR long_string" in call_args

    def test_log_variable_state_with_short_value(self):
        """Test variable state logging with short value that gets stored directly"""
        with patch('src.utils.debug_helpers.logger') as mock_logger:
            short_value = "short"
            
            StateInspector.log_variable_state("short_var", short_value)
            
            mock_logger.debug.assert_called_once()
            call_args = mock_logger.debug.call_args[0][0]
            assert "VAR short_var" in call_args

    @patch('src.utils.debug_helpers.psutil')
    @patch('src.utils.debug_helpers.os')
    def test_log_system_state(self, mock_os, mock_psutil):
        """Test system state logging"""
        # Mock psutil functions
        mock_psutil.cpu_percent.return_value = 50.0
        mock_psutil.virtual_memory.return_value.percent = 60.0
        mock_psutil.disk_usage.return_value.percent = 70.0
        
        # Mock os functions
        mock_os.getpid.return_value = 12345
        mock_os.getcwd.return_value = "/test/directory"
        
        with patch('src.utils.debug_helpers.logger') as mock_logger:
            StateInspector.log_system_state()
            
            mock_logger.info.assert_called()
            call_args = mock_logger.info.call_args[0][0]
            assert "SYSTEM" in call_args

    def test_log_variable_state_with_none(self):
        """Test variable state logging with None value"""
        with patch('src.utils.debug_helpers.logger') as mock_logger:
            StateInspector.log_variable_state("none_var", None)
            
            mock_logger.debug.assert_called_once()
            call_args = mock_logger.debug.call_args[0][0]
            assert "VAR none_var" in call_args

    def test_log_variable_state_empty_collections(self):
        """Test variable state logging with empty collections"""
        with patch('src.utils.debug_helpers.logger') as mock_logger:
            # Empty list
            StateInspector.log_variable_state("empty_list", [])
            
            # Empty dict
            StateInspector.log_variable_state("empty_dict", {})
            
            # Empty string
            StateInspector.log_variable_state("empty_string", "")
            
            assert mock_logger.debug.call_count == 3

    def test_log_function_args_empty(self):
        """Test logging function args when empty"""
        with patch('src.utils.debug_helpers.logger') as mock_logger:
            StateInspector.log_function_args("test_function", (), {})
            
            mock_logger.debug.assert_called_once()
            call_args = mock_logger.debug.call_args[0][0]
            assert "ARGS test_function" in call_args


class TestDebugHelpersEdgeCases:
    """Test edge cases and error conditions"""

    def test_profiler_with_nested_calls(self):
        """Test profiler with nested function calls"""
        profiler = DebugProfiler()
        
        @profiler.profile
        def outer_function():
            return inner_function() + 1
        
        @profiler.profile
        def inner_function():
            return 5
        
        result = outer_function()
        
        assert result == 6
        outer_name = f"{outer_function.__module__}.{outer_function.__name__}"
        inner_name = f"{inner_function.__module__}.{inner_function.__name__}"
        
        assert profiler.call_counts[outer_name] == 1
        assert profiler.call_counts[inner_name] == 1

    def test_profiler_preserves_function_metadata(self):
        """Test that profiler preserves original function metadata"""
        profiler = DebugProfiler()
        
        @profiler.profile
        def documented_function():
            """This function has documentation"""
            return "result"
        
        # Function name and docstring should be preserved
        assert documented_function.__name__ == "documented_function"
        assert documented_function.__doc__ == "This function has documentation"

    def test_state_inspector_with_complex_objects(self):
        """Test state inspector with complex nested objects"""
        with patch('src.utils.debug_helpers.logger') as mock_logger:
            complex_obj = {
                "nested": {
                    "list": [1, 2, 3, {"deep": "value"}],
                    "string": "test_string"
                },
                "top_level": "value"
            }
            
            StateInspector.log_variable_state("complex_obj", complex_obj)
            
            mock_logger.debug.assert_called_once()

    def test_variable_state_with_tuple(self):
        """Test variable state logging with tuple"""
        with patch('src.utils.debug_helpers.logger') as mock_logger:
            test_tuple = ("item1", "item2", "item3", "item4")
            
            StateInspector.log_variable_state("test_tuple", test_tuple)
            
            mock_logger.debug.assert_called_once()
            call_args = mock_logger.debug.call_args[0][0]
            assert "VAR test_tuple" in call_args

    def test_profiler_get_stats_empty(self):
        """Test getting stats when no functions have been profiled"""
        profiler = DebugProfiler()
        stats = profiler.get_stats()
        
        assert isinstance(stats, dict)
        assert len(stats) == 0

    def test_profiler_function_with_return_value_and_exception(self):
        """Test profiler captures timing even when function has complex behavior"""
        profiler = DebugProfiler()
        
        @profiler.profile
        def sometimes_failing_function(should_fail=False):
            if should_fail:
                raise RuntimeError("Intentional failure")
            return "success"
        
        # Successful call
        result = sometimes_failing_function(False)
        assert result == "success"
        
        # Failing call
        with pytest.raises(RuntimeError):
            sometimes_failing_function(True)
        
        func_name = f"{sometimes_failing_function.__module__}.{sometimes_failing_function.__name__}"
        assert profiler.call_counts[func_name] == 2
        assert len(profiler.timings[func_name]) == 2