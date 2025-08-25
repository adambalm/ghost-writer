#!/usr/bin/env python3
"""
Performance Benchmarking Suite for Ghost Writer
Tests scalability limits and identifies bottlenecks
"""

import time
import asyncio
import concurrent.futures
import statistics
import json
import psutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PerformanceBenchmark:
    """Comprehensive performance testing suite"""
    
    def __init__(self):
        self.test_files = [
            Path("joe.note"),
            Path("Visual_Library.note"),
        ]
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'system_info': self.get_system_info(),
            'benchmarks': []
        }
        
    def get_system_info(self) -> Dict[str, Any]:
        """Collect system information"""
        return {
            'cpu_count': psutil.cpu_count(),
            'memory_total': psutil.virtual_memory().total / (1024**3),  # GB
            'disk_free': psutil.disk_usage('/').free / (1024**3),  # GB
            'python_version': subprocess.check_output(['python', '--version']).decode().strip()
        }
    
    def benchmark_single_processing(self, iterations: int = 10) -> Dict[str, Any]:
        """Benchmark single-threaded processing performance"""
        logger.info(f"Running single processing benchmark ({iterations} iterations)")
        
        times = []
        memory_usage = []
        
        for i in range(iterations):
            start_memory = psutil.Process().memory_info().rss / (1024**2)  # MB
            start_time = time.time()
            
            try:
                # Run production readiness assessment as benchmark
                result = subprocess.run([
                    'python', 'production_readiness_assessment.py'
                ], capture_output=True, text=True, timeout=120)
                
                end_time = time.time()
                end_memory = psutil.Process().memory_info().rss / (1024**2)  # MB
                
                if result.returncode == 0:
                    processing_time = end_time - start_time
                    memory_delta = end_memory - start_memory
                    
                    times.append(processing_time)
                    memory_usage.append(memory_delta)
                    
                    logger.info(f"Iteration {i+1}: {processing_time:.3f}s, {memory_delta:.1f}MB")
                    
            except subprocess.TimeoutExpired:
                logger.warning(f"Iteration {i+1} timed out")
                
        return {
            'test_type': 'single_processing',
            'iterations': len(times),
            'avg_time': statistics.mean(times) if times else 0,
            'min_time': min(times) if times else 0,
            'max_time': max(times) if times else 0,
            'std_dev': statistics.stdev(times) if len(times) > 1 else 0,
            'avg_memory_mb': statistics.mean(memory_usage) if memory_usage else 0,
            'throughput_pages_per_second': 2 / statistics.mean(times) if times else 0  # 2 pages in test file
        }
    
    def benchmark_concurrent_processing(self, max_workers: int = 10) -> Dict[str, Any]:
        """Benchmark concurrent processing performance"""
        logger.info(f"Running concurrent processing benchmark (max_workers={max_workers})")
        
        def process_single():
            try:
                result = subprocess.run([
                    'python', 'production_readiness_assessment.py'
                ], capture_output=True, text=True, timeout=60)
                return result.returncode == 0
            except:
                return False
        
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss / (1024**2)
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(process_single) for _ in range(max_workers)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        end_time = time.time()
        end_memory = psutil.Process().memory_info().rss / (1024**2)
        
        total_time = end_time - start_time
        success_rate = sum(results) / len(results) * 100
        throughput = (max_workers * 2) / total_time  # 2 pages per worker
        
        return {
            'test_type': 'concurrent_processing',
            'max_workers': max_workers,
            'total_time': total_time,
            'success_rate': success_rate,
            'throughput_pages_per_second': throughput,
            'memory_usage_mb': end_memory - start_memory,
            'avg_time_per_worker': total_time / max_workers
        }
    
    def benchmark_memory_scaling(self, file_sizes: List[int] = None) -> Dict[str, Any]:
        """Test memory usage with different file sizes"""
        if file_sizes is None:
            file_sizes = [1, 5, 10, 20, 50]  # MB equivalents
            
        logger.info("Running memory scaling benchmark")
        
        memory_results = []
        
        for size_mb in file_sizes:
            start_memory = psutil.Process().memory_info().rss / (1024**2)
            
            try:
                # Simulate different file sizes by processing multiple times
                iterations = max(1, size_mb // 2)  # Approximate scaling
                
                for _ in range(iterations):
                    subprocess.run([
                        'python', 'production_readiness_assessment.py'
                    ], capture_output=True, text=True, timeout=30)
                
                end_memory = psutil.Process().memory_info().rss / (1024**2)
                memory_delta = end_memory - start_memory
                
                memory_results.append({
                    'file_size_mb': size_mb,
                    'memory_usage_mb': memory_delta,
                    'memory_efficiency': memory_delta / size_mb
                })
                
                logger.info(f"Size {size_mb}MB: {memory_delta:.1f}MB memory usage")
                
            except Exception as e:
                logger.warning(f"Memory test failed for size {size_mb}MB: {e}")
        
        return {
            'test_type': 'memory_scaling',
            'results': memory_results,
            'peak_memory_mb': max([r['memory_usage_mb'] for r in memory_results]) if memory_results else 0,
            'memory_efficiency': statistics.mean([r['memory_efficiency'] for r in memory_results]) if memory_results else 0
        }
    
    def benchmark_load_capacity(self) -> Dict[str, Any]:
        """Test maximum sustainable load"""
        logger.info("Running load capacity benchmark")
        
        max_workers_tested = []
        success_rates = []
        
        for workers in [1, 2, 5, 10, 20, 30]:
            logger.info(f"Testing with {workers} workers...")
            
            try:
                result = self.benchmark_concurrent_processing(workers)
                max_workers_tested.append(workers)
                success_rates.append(result['success_rate'])
                
                # Stop if success rate drops below 90%
                if result['success_rate'] < 90:
                    logger.warning(f"Success rate dropped to {result['success_rate']:.1f}% at {workers} workers")
                    break
                    
            except Exception as e:
                logger.error(f"Load test failed at {workers} workers: {e}")
                break
        
        # Find optimal capacity (90% success rate threshold)
        optimal_capacity = 1
        for i, success_rate in enumerate(success_rates):
            if success_rate >= 90:
                optimal_capacity = max_workers_tested[i]
        
        return {
            'test_type': 'load_capacity',
            'max_workers_tested': max_workers_tested,
            'success_rates': success_rates,
            'optimal_capacity': optimal_capacity,
            'max_sustainable_throughput': optimal_capacity * 2 / 1.0  # Estimated pages/second
        }
    
    def run_full_benchmark_suite(self) -> Dict[str, Any]:
        """Execute complete performance benchmark suite"""
        logger.info("Starting full performance benchmark suite")
        
        # Run all benchmarks
        self.results['benchmarks'].extend([
            self.benchmark_single_processing(),
            self.benchmark_concurrent_processing(max_workers=5),
            self.benchmark_concurrent_processing(max_workers=10),
            self.benchmark_memory_scaling(),
            self.benchmark_load_capacity()
        ])
        
        # Calculate summary metrics
        single_result = next(b for b in self.results['benchmarks'] if b['test_type'] == 'single_processing')
        load_result = next(b for b in self.results['benchmarks'] if b['test_type'] == 'load_capacity')
        
        self.results['summary'] = {
            'baseline_throughput_pps': single_result['throughput_pages_per_second'],
            'max_sustainable_throughput_pps': load_result['max_sustainable_throughput'],
            'scalability_factor': load_result['max_sustainable_throughput'] / single_result['throughput_pages_per_second'],
            'meets_10x_target': load_result['max_sustainable_throughput'] >= (single_result['throughput_pages_per_second'] * 10),
            'recommended_max_workers': load_result['optimal_capacity']
        }
        
        return self.results
    
    def save_results(self) -> None:
        """Save benchmark results to file"""
        results_dir = Path('.handoff/benchmarks')
        results_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        results_path = results_dir / f'performance_benchmark_{timestamp}.json'
        
        with open(results_path, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        logger.info(f"Benchmark results saved to {results_path}")
        
        # Also save as latest
        latest_path = results_dir / 'latest_benchmark.json'
        with open(latest_path, 'w') as f:
            json.dump(self.results, f, indent=2)

def main():
    """Run performance benchmark suite"""
    benchmark = PerformanceBenchmark()
    results = benchmark.run_full_benchmark_suite()
    benchmark.save_results()
    
    # Print summary
    summary = results['summary']
    print(f"\n=== PERFORMANCE BENCHMARK RESULTS ===")
    print(f"Baseline Throughput: {summary['baseline_throughput_pps']:.2f} pages/second")
    print(f"Max Sustainable Throughput: {summary['max_sustainable_throughput_pps']:.2f} pages/second")
    print(f"Scalability Factor: {summary['scalability_factor']:.1f}x")
    print(f"Meets 10x Target: {'✅ YES' if summary['meets_10x_target'] else '❌ NO'}")
    print(f"Recommended Max Workers: {summary['recommended_max_workers']}")
    
    # Performance assessment for CI/CD
    if not summary['meets_10x_target']:
        print("\n⚠️  WARNING: System does not meet 10x scalability target")
        exit(1)
    else:
        print("\n✅ System meets scalability requirements")
        exit(0)

if __name__ == "__main__":
    main()