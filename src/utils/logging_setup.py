"""
Comprehensive logging setup for Ghost Writer with file output and debugging support
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional, Dict, Any
import json
from datetime import datetime


class GhostWriterLogger:
    def __init__(self, name: str = "ghost_writer", config: Optional[dict] = None):
        self.name = name
        self.config = config or self._get_default_config()
        self.logger = logging.getLogger(name)
        self._setup_logging()

    def _get_default_config(self) -> dict:
        return {
            "level": "INFO",
            "file_path": "data/logs/ghost_writer.log",
            "max_file_size": "10MB",
            "backup_count": 5,
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "debug_format": "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s() - %(message)s"
        }

    def _setup_logging(self):
        """Set up comprehensive logging with file rotation and console output"""
        # Clear any existing handlers
        self.logger.handlers = []
        self.logger.setLevel(getattr(logging, self.config["level"].upper()))

        # Create logs directory
        log_path = Path(self.config["file_path"])
        log_path.parent.mkdir(parents=True, exist_ok=True)

        # File handler with rotation
        file_handler = logging.handlers.RotatingFileHandler(
            log_path,
            maxBytes=self._parse_size(self.config["max_file_size"]),
            backupCount=self.config["backup_count"]
        )
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)

        # Different formats for debug vs normal
        if self.config["level"].upper() == "DEBUG":
            formatter = logging.Formatter(self.config["debug_format"])
        else:
            formatter = logging.Formatter(self.config["format"])

        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

        # Log system startup
        self.logger.info(f"Logging initialized - Level: {self.config['level']}")

    def _parse_size(self, size_str: str) -> int:
        """Parse size string like '10MB' to bytes"""
        size_str = size_str.upper()
        if size_str.endswith('MB'):
            return int(size_str[:-2]) * 1024 * 1024
        elif size_str.endswith('KB'):
            return int(size_str[:-2]) * 1024
        elif size_str.endswith('GB'):
            return int(size_str[:-2]) * 1024 * 1024 * 1024
        else:
            return int(size_str)

    def log_function_call(self, func_name: str, args: Optional[Dict[Any, Any]] = None, kwargs: Optional[Dict[Any, Any]] = None):
        """Log function calls with parameters for debugging"""
        if self.logger.isEnabledFor(logging.DEBUG):
            params = {}
            if args:
                params['args'] = args
            if kwargs:
                params['kwargs'] = kwargs
            self.logger.debug(f"CALL {func_name} - {json.dumps(params, default=str)}")

    def log_function_result(self, func_name: str, result: Any = None, duration: Optional[float] = None):
        """Log function results and timing"""
        if self.logger.isEnabledFor(logging.DEBUG):
            result_info: Dict[str, Any] = {"result_type": type(result).__name__}
            if duration:
                result_info["duration_ms"] = round(duration * 1000, 2)
            if hasattr(result, '__len__') and not isinstance(result, str):
                result_info["result_length"] = len(result)
            self.logger.debug(f"RESULT {func_name} - {json.dumps(result_info, default=str)}")

    def log_performance(self, operation: str, duration: float, items_processed: Optional[int] = None):
        """Log performance metrics"""
        perf_info = {
            "operation": operation,
            "duration_ms": round(duration * 1000, 2),
        }
        if items_processed:
            perf_info["items_processed"] = items_processed
            perf_info["items_per_second"] = round(items_processed / duration, 2)
        
        self.logger.info(f"PERFORMANCE - {json.dumps(perf_info)}")

    def log_cost_tracking(self, provider: str, cost: float, operation: str):
        """Log cost information for monitoring"""
        cost_info = {
            "provider": provider,
            "cost": cost,
            "operation": operation,
            "timestamp": datetime.now().isoformat()
        }
        self.logger.info(f"COST - {json.dumps(cost_info)}")

    def log_error_with_context(self, error: Exception, context: Optional[Dict[Any, Any]] = None):
        """Log errors with additional context"""
        error_info = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context or {}
        }
        self.logger.error(f"ERROR - {json.dumps(error_info, default=str)}", exc_info=True)

    def get_logger(self) -> logging.Logger:
        """Get the underlying logger instance"""
        return self.logger


# Decorator for automatic function logging
def log_calls(logger_name: str = "ghost_writer"):
    def decorator(func):
        def wrapper(*args, **kwargs):
            import time
            logger = logging.getLogger(logger_name)
            
            start_time = time.time()
            try:
                # Log function call
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(f"CALL {func.__name__} - args: {len(args)}, kwargs: {list(kwargs.keys())}")
                
                result = func(*args, **kwargs)
                
                # Log successful result
                duration = time.time() - start_time
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(f"SUCCESS {func.__name__} - duration: {duration:.3f}s")
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                logger.error(f"FAILED {func.__name__} - duration: {duration:.3f}s - error: {e}", exc_info=True)
                raise
        
        return wrapper
    return decorator


# Global logger instance
def get_logger(name: str = "ghost_writer") -> GhostWriterLogger:
    """Get or create a logger instance"""
    return GhostWriterLogger(name)


# Initialize default logger
default_logger = get_logger()
logger = default_logger.get_logger()