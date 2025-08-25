"""
Debugging utilities and development helpers for Ghost Writer
"""

import functools
import time
import sys
import json
from typing import Any, Dict, List, Callable
import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class DebugProfiler:
    """Performance profiler for debugging"""
    
    def __init__(self):
        self.timings = {}
        self.call_counts = {}
        
    def profile(self, func: Callable) -> Callable:
        """Decorator to profile function execution"""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            func_name = f"{func.__module__}.{func.__name__}"
            
            # Track call count
            self.call_counts[func_name] = self.call_counts.get(func_name, 0) + 1
            
            # Time execution
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                # Track timing stats
                if func_name not in self.timings:
                    self.timings[func_name] = []
                self.timings[func_name].append(duration)
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                logger.error(f"PROFILED_ERROR {func_name} - {duration:.3f}s - {e}", exc_info=True)
                raise
                
        return wrapper
    
    def get_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        stats = {}
        for func_name, times in self.timings.items():
            stats[func_name] = {
                'calls': self.call_counts.get(func_name, 0),
                'total_time': sum(times),
                'avg_time': sum(times) / len(times),
                'min_time': min(times),
                'max_time': max(times)
            }
        return stats
    
    def print_stats(self):
        """Print formatted performance statistics"""
        stats = self.get_stats()
        print("\n=== PERFORMANCE PROFILE ===")
        print(f"{'Function':<40} {'Calls':<8} {'Total':<8} {'Avg':<8} {'Min':<8} {'Max':<8}")
        print("-" * 80)
        
        for func_name, data in sorted(stats.items(), key=lambda x: x[1]['total_time'], reverse=True):
            print(f"{func_name:<40} {data['calls']:<8} {data['total_time']:<8.3f} "
                  f"{data['avg_time']:<8.3f} {data['min_time']:<8.3f} {data['max_time']:<8.3f}")


class StateInspector:
    """Inspect and log system state for debugging"""
    
    @staticmethod
    def log_function_args(func_name: str, args: tuple, kwargs: dict):
        """Log function arguments for debugging"""
        arg_info = {
            'function': func_name,
            'args': [str(type(arg).__name__) for arg in args],
            'kwargs': {k: str(type(v).__name__) for k, v in kwargs.items()}
        }
        logger.debug(f"ARGS {func_name} - {json.dumps(arg_info)}")
    
    @staticmethod 
    def log_variable_state(var_name: str, value: Any, context: str = ""):
        """Log variable state with type and value info"""
        info: Dict[str, Any] = {
            'variable': var_name,
            'type': type(value).__name__,
            'context': context
        }
        
        # Add size/length info for collections
        if hasattr(value, '__len__') and not isinstance(value, str):
            info['length'] = len(value)
        
        # Add sample data for large structures
        if isinstance(value, (list, tuple)) and len(value) > 3:
            info['sample'] = [str(x) for x in value[:3]]
        elif isinstance(value, dict) and len(value) > 3:
            info['sample_keys'] = list(value.keys())[:3]
        elif isinstance(value, str) and len(value) > 100:
            info['preview'] = value[:100] + "..."
        else:
            info['value'] = str(value)
            
        logger.debug(f"VAR {var_name} - {json.dumps(info, default=str)}")
    
    @staticmethod
    def log_system_state():
        """Log current system state"""
        import psutil
        import os
        
        state = {
            'memory_mb': psutil.Process().memory_info().rss / 1024 / 1024,
            'cpu_percent': psutil.Process().cpu_percent(),
            'open_files': len(psutil.Process().open_files()),
            'cwd': os.getcwd(),
            'python_version': sys.version.split()[0]
        }
        logger.info(f"SYSTEM_STATE - {json.dumps(state)}")


@contextmanager
def debug_context(operation_name: str, log_args: bool = False, log_result: bool = False):
    """Context manager for debugging operations"""
    start_time = time.time()
    logger.debug(f"START {operation_name}")
    
    try:
        yield
        duration = time.time() - start_time
        logger.debug(f"SUCCESS {operation_name} - {duration:.3f}s")
        
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"FAILED {operation_name} - {duration:.3f}s - {e}", exc_info=True)
        raise


def debug_decorator(log_args: bool = False, log_result: bool = False, profile: bool = False):
    """Comprehensive debugging decorator"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            func_name = f"{func.__module__}.{func.__name__}"
            
            if log_args:
                StateInspector.log_function_args(func_name, args, kwargs)
            
            with debug_context(func_name):
                start_time = time.time()
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                if log_result:
                    StateInspector.log_variable_state(f"{func_name}_result", result)
                
                if profile:
                    logger.info(f"PERF {func_name} - {duration:.3f}s")
                    
                return result
                
        return wrapper
    return decorator


class MemoryTracker:
    """Track memory usage for debugging memory leaks"""
    
    def __init__(self):
        self.snapshots = {}
    
    def take_snapshot(self, label: str):
        """Take a memory snapshot"""
        import psutil
        import gc
        
        # Force garbage collection
        gc.collect()
        
        process = psutil.Process()
        self.snapshots[label] = {
            'rss_mb': process.memory_info().rss / 1024 / 1024,
            'vms_mb': process.memory_info().vms / 1024 / 1024,
            'timestamp': time.time()
        }
        logger.debug(f"MEMORY_SNAPSHOT {label} - {self.snapshots[label]['rss_mb']:.1f}MB RSS")
    
    def compare_snapshots(self, label1: str, label2: str):
        """Compare two memory snapshots"""
        if label1 not in self.snapshots or label2 not in self.snapshots:
            logger.warning(f"Cannot compare snapshots: {label1}, {label2}")
            return
        
        snap1 = self.snapshots[label1]
        snap2 = self.snapshots[label2]
        
        rss_diff = snap2['rss_mb'] - snap1['rss_mb']
        vms_diff = snap2['vms_mb'] - snap1['vms_mb']
        
        logger.info(f"MEMORY_DIFF {label1} -> {label2} - RSS: {rss_diff:+.1f}MB, VMS: {vms_diff:+.1f}MB")


class TestDataValidator:
    """Validate test data and system state"""
    
    @staticmethod
    def validate_ocr_result(result: dict) -> bool:
        """Validate OCR result structure"""
        required_fields = ['text', 'confidence', 'provider']
        return all(field in result for field in required_fields)
    
    @staticmethod
    def validate_embedding(embedding: Any) -> bool:
        """Validate embedding vector"""
        import numpy as np
        if not isinstance(embedding, np.ndarray):
            return False
        return embedding.dtype == np.float32 and len(embedding.shape) == 1
    
    @staticmethod
    def validate_database_state(db_manager) -> List[str]:
        """Validate database state and return any issues"""
        issues = []
        
        try:
            db_manager.get_database_stats()
            
            # Check for orphaned records
            with db_manager.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM embeddings e 
                    LEFT JOIN notes n ON e.note_id = n.note_id 
                    WHERE n.note_id IS NULL
                """)
                orphaned_embeddings = cursor.fetchone()[0]
                if orphaned_embeddings > 0:
                    issues.append(f"{orphaned_embeddings} orphaned embeddings")
                
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM expansions e 
                    LEFT JOIN notes n ON e.note_id = n.note_id 
                    WHERE n.note_id IS NULL
                """)
                orphaned_expansions = cursor.fetchone()[0]
                if orphaned_expansions > 0:
                    issues.append(f"{orphaned_expansions} orphaned expansions")
                    
        except Exception as e:
            issues.append(f"Database validation error: {e}")
            
        return issues


# Global instances for easy access
profiler = DebugProfiler()
memory_tracker = MemoryTracker()
validator = TestDataValidator()


# Convenience functions
def start_profiling():
    """Start profiling mode"""
    global profiler
    profiler = DebugProfiler()
    logger.info("Profiling started")


def stop_profiling():
    """Stop profiling and show results"""
    profiler.print_stats()
    logger.info("Profiling stopped")


def quick_debug(obj: Any, name: str = "object"):
    """Quick debug helper - log object info"""
    StateInspector.log_variable_state(name, obj, "quick_debug")


def assert_performance(func: Callable, max_duration: float, *args, **kwargs):
    """Assert function completes within time limit"""
    start = time.time()
    result = func(*args, **kwargs)
    duration = time.time() - start
    
    if duration > max_duration:
        raise AssertionError(f"{func.__name__} took {duration:.3f}s, expected < {max_duration}s")
    
    return result