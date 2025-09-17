#!/usr/bin/env python3
"""
Performance Monitor for UnrealBlueprintMCP

Monitors MCP server performance, WebSocket connections, and tool execution times.
Provides real-time metrics and performance analysis.
"""

import asyncio
import websockets
import json
import time
import psutil
import logging
import threading
import gc
import weakref
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any
import statistics
import hashlib

# Import memory management utilities
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from memory_manager import (
    MemoryManager, CircularBuffer, MemoryProfiler,
    get_memory_manager, track_memory_usage
)

@dataclass
class PerformanceMetrics:
    """Performance metrics data structure"""
    timestamp: float
    cpu_percent: float
    memory_mb: float
    active_connections: int
    total_requests: int
    avg_response_time: float
    error_rate: float
    tool_call_count: Dict[str, int]

@dataclass
class ToolCallMetrics:
    """Tool call performance metrics"""
    tool_name: str
    call_count: int
    total_time: float
    avg_time: float
    min_time: float
    max_time: float
    error_count: int
    success_rate: float

class PerformanceMonitor:
    """Real-time performance monitoring for MCP server with memory management"""

    def __init__(self, server_url: str = "ws://localhost:6277", collection_interval: float = 5.0):
        self.server_url = server_url
        self.collection_interval = collection_interval
        self.running = False

        # Initialize memory manager
        self.memory_manager = get_memory_manager()

        # Enhanced metrics storage with compression and TTL
        self.metrics_history = CircularBuffer[PerformanceMetrics](
            maxlen=1000, enable_compression=True, compression_threshold=2048
        )
        self.tool_metrics: Dict[str, CircularBuffer] = defaultdict(
            lambda: CircularBuffer(maxlen=500, enable_compression=True)
        )
        self.error_log = CircularBuffer(maxlen=100)

        # Connection pool for WebSocket connections with compression
        self.connection_pool = CircularBuffer(maxlen=10, enable_compression=False)  # Don't compress connections

        # Garbage collection timer
        self._last_gc_time = time.time()
        self._gc_interval = 600.0  # 10 minutes

        # Enhanced connection tracking with weak references
        self.active_connections = 0
        self.total_requests = 0
        self.response_times = CircularBuffer[float](
            maxlen=500, enable_compression=True  # Increased size for better statistics
        )
        self._response_time_stats = {
            "min": float('inf'),
            "max": 0.0,
            "moving_average": 0.0,
            "outlier_threshold": 5.0  # seconds
        }

        # Enhanced connection tracking with automatic cleanup
        self._active_websockets: List[weakref.ref] = []
        self._connection_last_activity: Dict[str, float] = {}
        self._inactive_connection_threshold = 300.0  # 5 minutes
        self._max_inactive_connections = 20  # Max inactive connections to track

        # Enhanced caching for frequently accessed data
        self._response_cache = {}

        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    async def start_monitoring(self):
        """Start the performance monitoring with memory management"""
        self.running = True
        self.logger.info("Starting performance monitoring with memory management...")

        # Start memory manager if not already running
        if not self.memory_manager._running:
            await self.memory_manager.start()

        # Start memory profiler
        await self.memory_profiler.start_monitoring(interval=60.0)  # Monitor every minute

        # Start monitoring tasks
        tasks = [
            asyncio.create_task(self._collect_system_metrics()),
            asyncio.create_task(self._monitor_websocket_health()),
            asyncio.create_task(self._performance_reporter()),
            asyncio.create_task(self._memory_cleanup_task())  # New memory cleanup task
        ]

        try:
            await asyncio.gather(*tasks)
        except KeyboardInterrupt:
            self.logger.info("Monitoring stopped by user")
        finally:
            await self.stop_monitoring()

    async def stop_monitoring(self):
        """Stop the performance monitoring and cleanup resources"""
        self.running = False

        # Stop memory profiler
        await self.memory_profiler.stop_monitoring()

        # Cleanup connections
        await self._cleanup_connections()

        # Force garbage collection
        self.memory_manager.force_garbage_collection()

        self.logger.info("Performance monitoring stopped and resources cleaned up")

    async def _collect_system_metrics(self):
        """Collect system-level performance metrics"""
        while self.running:
            try:
                # Get system metrics
                cpu_percent = psutil.cpu_percent(interval=1)
                memory_info = psutil.virtual_memory()
                memory_mb = memory_info.used / (1024 * 1024)

                # Calculate averages using circular buffer data
                response_times_data = self.response_times.get_all()
                avg_response_time = statistics.mean(response_times_data) if response_times_data else 0.0
                error_rate = len(self.error_log) / max(self.total_requests, 1) * 100

                # Tool call counts from circular buffers
                tool_counts = {}
                for tool_name, times_buffer in self.tool_metrics.items():
                    tool_counts[tool_name] = len(times_buffer)

                # Periodically clean up tool metrics to prevent memory growth
                if time.time() - self._last_gc_time > self._gc_interval:
                    self._cleanup_old_metrics()
                    self._last_gc_time = time.time()

                # Create metrics object
                metrics = PerformanceMetrics(
                    timestamp=time.time(),
                    cpu_percent=cpu_percent,
                    memory_mb=memory_mb,
                    active_connections=self.active_connections,
                    total_requests=self.total_requests,
                    avg_response_time=avg_response_time,
                    error_rate=error_rate,
                    tool_call_count=tool_counts
                )

                # Add memory information to metrics
                memory_stats = self.memory_profiler.collect_memory_stats()
                enhanced_metrics = PerformanceMetrics(
                    timestamp=metrics.timestamp,
                    cpu_percent=metrics.cpu_percent,
                    memory_mb=memory_stats.rss_mb,  # Use profiler's memory data
                    active_connections=metrics.active_connections,
                    total_requests=metrics.total_requests,
                    avg_response_time=metrics.avg_response_time,
                    error_rate=metrics.error_rate,
                    tool_call_count=metrics.tool_call_count
                )

                self.metrics_history.append(enhanced_metrics)

                await asyncio.sleep(self.collection_interval)

            except Exception as e:
                self.logger.error(f"Error collecting system metrics: {e}")
                await asyncio.sleep(self.collection_interval)

    async def _monitor_websocket_health(self):
        """Monitor WebSocket server health with connection management"""
        while self.running:
            websocket = None
            try:
                # Test connection to MCP server with memory management
                start_time = time.time()

                # Use memory manager for connection tracking
                async with self.memory_manager.managed_resource(
                    await websockets.connect(self.server_url, timeout=5)
                ) as websocket:
                    self.active_connections += 1

                    # Send health check request
                    health_request = {
                        "jsonrpc": "2.0",
                        "id": f"health_check_{int(time.time())}",
                        "method": "tools/call",
                        "params": {
                            "name": "get_server_status",
                            "arguments": {}
                        }
                    }

                    await websocket.send(json.dumps(health_request))
                    response = await asyncio.wait_for(websocket.recv(), timeout=5)

                    end_time = time.time()
                    response_time = end_time - start_time

                    # Update metrics in circular buffers
                    self.total_requests += 1
                    self.response_times.append(response_time)

                    # Track this connection weakly
                    if websocket:
                        self._track_connection(websocket)

                    # Parse response
                    try:
                        parsed_response = json.loads(response)
                        if "error" in parsed_response:
                            self._record_error("WebSocket health check error", parsed_response["error"])
                    except json.JSONDecodeError:
                        self._record_error("WebSocket response parsing error", response[:100])  # Truncate long responses

                    self.active_connections -= 1

            except Exception as e:
                self._record_error("WebSocket connection error", str(e))

            await asyncio.sleep(self.collection_interval)

    async def _performance_reporter(self):
        """Generate periodic performance reports"""
        while self.running:
            await asyncio.sleep(30)  # Report every 30 seconds

            if len(self.metrics_history) > 0:
                await self._generate_report()

    def _record_error(self, error_type: str, error_details: Any):
        """Enhanced error recording with categorization and memory safety"""
        error_entry = {
            "timestamp": time.time(),
            "type": error_type,
            "details": str(error_details)[:500],  # Limit error detail length
            "severity": self._categorize_error_severity(error_type),
            "hash": hashlib.md5(f"{error_type}{str(error_details)[:100]}".encode()).hexdigest()[:8]
        }
        self.error_log.append(error_entry)

        # Enhanced error rate monitoring
        recent_errors = self.error_log.get_recent(50)
        critical_errors = [e for e in recent_errors if e.get('severity') == 'critical']

        if len(critical_errors) > 5:
            # Trigger emergency cleanup for critical errors
            asyncio.create_task(self._emergency_error_cleanup())

        # Check for duplicate errors (potential infinite loops)
        error_hashes = [e.get('hash') for e in recent_errors[-10:]]
        if len(set(error_hashes)) < len(error_hashes) * 0.5:  # >50% duplicates
            self.logger.warning("Duplicate error pattern detected - possible infinite loop")

    async def benchmark_tool_performance(self, tool_name: str, arguments: Dict, iterations: int = 10):
        """Benchmark specific tool performance"""
        self.logger.info(f"Benchmarking tool '{tool_name}' with {iterations} iterations...")

        execution_times = []
        errors = 0

        for i in range(iterations):
            try:
                start_time = time.time()

                async with websockets.connect(self.server_url, timeout=10) as websocket:
                    request = {
                        "jsonrpc": "2.0",
                        "id": f"benchmark_{tool_name}_{i}",
                        "method": "tools/call",
                        "params": {
                            "name": tool_name,
                            "arguments": arguments
                        }
                    }

                    await websocket.send(json.dumps(request))
                    response = await asyncio.wait_for(websocket.recv(), timeout=10)

                    end_time = time.time()
                    execution_time = end_time - start_time

                    # Check for errors
                    try:
                        parsed_response = json.loads(response)
                        if "error" in parsed_response:
                            errors += 1
                            continue
                    except json.JSONDecodeError:
                        errors += 1
                        continue

                    execution_times.append(execution_time)
                    self.tool_metrics[tool_name].append(execution_time)  # CircularBuffer handles overflow

            except Exception as e:
                errors += 1
                self.logger.error(f"Benchmark iteration {i} failed: {e}")

            # Small delay between iterations
            await asyncio.sleep(0.1)

        # Calculate metrics
        if execution_times:
            metrics = ToolCallMetrics(
                tool_name=tool_name,
                call_count=len(execution_times),
                total_time=sum(execution_times),
                avg_time=statistics.mean(execution_times),
                min_time=min(execution_times),
                max_time=max(execution_times),
                error_count=errors,
                success_rate=(len(execution_times) / iterations) * 100
            )

            self.logger.info(f"Benchmark results for '{tool_name}':")
            self.logger.info(f"  Average time: {metrics.avg_time:.3f}s")
            self.logger.info(f"  Min time: {metrics.min_time:.3f}s")
            self.logger.info(f"  Max time: {metrics.max_time:.3f}s")
            self.logger.info(f"  Success rate: {metrics.success_rate:.1f}%")

            return metrics
        else:
            self.logger.error(f"No successful executions for tool '{tool_name}'")
            return None

    async def _generate_report(self):
        """Generate performance report"""
        if len(self.metrics_history) == 0:
            return

        recent_metrics = self.metrics_history.get_recent(10)  # Last 10 data points using circular buffer

        # Calculate averages
        avg_cpu = statistics.mean([m.cpu_percent for m in recent_metrics])
        avg_memory = statistics.mean([m.memory_mb for m in recent_metrics])
        avg_response_time = statistics.mean([m.avg_response_time for m in recent_metrics if m.avg_response_time > 0])

        # Current metrics
        current = recent_metrics[-1]

        self.logger.info("=== Performance Report ===")
        self.logger.info(f"CPU Usage: {avg_cpu:.1f}% (current: {current.cpu_percent:.1f}%)")
        self.logger.info(f"Memory Usage: {avg_memory:.1f}MB (current: {current.memory_mb:.1f}MB)")
        self.logger.info(f"Active Connections: {current.active_connections}")
        self.logger.info(f"Total Requests: {current.total_requests}")
        self.logger.info(f"Average Response Time: {avg_response_time:.3f}s")
        self.logger.info(f"Error Rate: {current.error_rate:.2f}%")

        # Tool usage statistics
        if current.tool_call_count:
            self.logger.info("Tool Usage:")
            for tool_name, count in current.tool_call_count.items():
                self.logger.info(f"  {tool_name}: {count} calls")

    def get_current_metrics(self) -> Optional[PerformanceMetrics]:
        """Get current performance metrics"""
        all_metrics = self.metrics_history.get_all()
        return all_metrics[-1] if all_metrics else None

    def get_tool_metrics(self, tool_name: str) -> Optional[ToolCallMetrics]:
        """Get metrics for a specific tool"""
        if tool_name not in self.tool_metrics or len(self.tool_metrics[tool_name]) == 0:
            return None

        times = self.tool_metrics[tool_name].get_all()
        return ToolCallMetrics(
            tool_name=tool_name,
            call_count=len(times),
            total_time=sum(times),
            avg_time=statistics.mean(times),
            min_time=min(times),
            max_time=max(times),
            error_count=0,  # TODO: Track errors per tool
            success_rate=100.0  # TODO: Calculate from error tracking
        )

    def export_metrics(self, filename: str):
        """Export metrics to JSON file with memory management"""
        export_data = {
            "metrics_history": [asdict(m) for m in self.metrics_history.get_all()],
            "tool_metrics": {tool: times_buffer.get_all() for tool, times_buffer in self.tool_metrics.items()},
            "error_log": self.error_log.get_all(),
            "memory_report": self.memory_profiler.get_memory_report(),
            "export_timestamp": time.time()
        }

        # Use context manager for file handling
        try:
            with open(filename, 'w') as f:
                json.dump(export_data, f, indent=2)
            self.logger.info(f"Metrics exported to {filename}")
        except Exception as e:
            self.logger.error(f"Failed to export metrics: {e}")
        finally:
            # Trigger garbage collection after large export
            self.memory_manager.force_garbage_collection()

    def _track_connection(self, websocket) -> None:
        """Track WebSocket connection with weak reference"""
        def cleanup_callback():
            self.logger.debug("WebSocket connection cleaned up automatically")
            if self.active_connections > 0:
                self.active_connections -= 1

        # Add weak reference to prevent memory leaks
        weak_ref = weakref.ref(websocket, cleanup_callback)
        self._active_websockets.append(weak_ref)

        # Clean up dead references periodically
        if len(self._active_websockets) > 50:
            self._cleanup_dead_connections()

    def _cleanup_dead_connections(self) -> None:
        """Remove dead WebSocket connection references"""
        alive_connections = []
        dead_count = 0

        for ref in self._active_websockets:
            if ref() is not None:
                alive_connections.append(ref)
            else:
                dead_count += 1

        self._active_websockets = alive_connections

        if dead_count > 0:
            self.logger.debug(f"Cleaned up {dead_count} dead connection references")

    async def _cleanup_connections(self) -> None:
        """Cleanup all tracked connections"""
        for ref in self._active_websockets[:]:
            connection = ref()
            if connection:
                try:
                    if hasattr(connection, 'close'):
                        await connection.close()
                except Exception as e:
                    self.logger.warning(f"Error closing connection during cleanup: {e}")

        self._active_websockets.clear()
        self.active_connections = 0

    async def _memory_cleanup_task(self) -> None:
        """Periodic memory cleanup task"""
        cleanup_interval = 300.0  # 5 minutes

        while self.running:
            try:
                await asyncio.sleep(cleanup_interval)

                # Cleanup dead connections
                self._cleanup_dead_connections()

                # Cleanup old metrics
                self._cleanup_old_metrics()

                # Force garbage collection
                gc_stats = self.memory_manager.force_garbage_collection()

                # Log memory status
                memory_report = self.memory_profiler.get_memory_report()
                self.logger.info(
                    f"Memory cleanup completed: "
                    f"Memory: {memory_report['current_memory_mb']:.1f}MB, "
                    f"GC collected: {gc_stats['total_collected']} objects"
                )

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in memory cleanup task: {e}")

    def _should_cleanup_metrics(self, current_memory_mb: float) -> bool:
        """Determine if metrics cleanup should be performed based on memory pressure"""
        # Check if we're over memory threshold or time threshold
        time_threshold = time.time() - self._last_gc_time > self._gc_interval
        memory_threshold = current_memory_mb > 500  # 500MB threshold
        connection_threshold = len(self._connection_last_activity) > self._max_inactive_connections

        return time_threshold or memory_threshold or connection_threshold

    def _intelligent_cleanup(self) -> None:
        """Intelligent cleanup based on memory pressure and usage patterns"""
        cleanup_count = 0

        # Clean up empty tool metric entries
        empty_tools = []
        for tool_name, metrics_buffer in self.tool_metrics.items():
            if len(metrics_buffer) == 0:
                empty_tools.append(tool_name)

        for tool_name in empty_tools:
            del self.tool_metrics[tool_name]
            cleanup_count += 1

        # Clean up inactive connections
        current_time = time.time()
        inactive_connections = []
        for conn_id, last_activity in self._connection_last_activity.items():
            if current_time - last_activity > self._inactive_connection_threshold:
                inactive_connections.append(conn_id)

        for conn_id in inactive_connections:
            del self._connection_last_activity[conn_id]
            cleanup_count += 1

        # Clean up old cache entries
        if hasattr(self, '_response_cache'):
            old_cache_entries = []
            for key, (value, timestamp) in self._response_cache.items():
                if current_time - timestamp > 3600:  # 1 hour old
                    old_cache_entries.append(key)

            for key in old_cache_entries:
                del self._response_cache[key]
                cleanup_count += 1

        if cleanup_count > 0:
            self.logger.debug(f"Intelligent cleanup completed: {cleanup_count} items cleaned")

    def _update_response_time_stats(self, response_times: List[float]) -> None:
        """Update response time statistics for anomaly detection"""
        if not response_times:
            return

        current_min = min(response_times)
        current_max = max(response_times)
        current_avg = statistics.mean(response_times)

        # Update running statistics
        self._response_time_stats["min"] = min(self._response_time_stats["min"], current_min)
        self._response_time_stats["max"] = max(self._response_time_stats["max"], current_max)

        # Update moving average (simple exponential smoothing)
        alpha = 0.1  # Smoothing factor
        if self._response_time_stats["moving_average"] == 0.0:
            self._response_time_stats["moving_average"] = current_avg
        else:
            self._response_time_stats["moving_average"] = (
                alpha * current_avg + (1 - alpha) * self._response_time_stats["moving_average"]
            )

        # Dynamic outlier threshold based on moving average
        self._response_time_stats["outlier_threshold"] = max(
            self._response_time_stats["moving_average"] * 3,  # 3x moving average
            5.0  # Minimum 5 seconds
        )

    def _get_real_active_connections(self) -> int:
        """Get real count of active connections by cleaning up dead references"""
        self._cleanup_dead_connections()
        return self.active_connections

    def _track_connection_intelligent(self, websocket, response_time: float) -> None:
        """Intelligently track connection with performance metrics"""
        connection_id = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"

        # Standard weak reference tracking
        self._track_connection(websocket)

        # Performance-based connection quality scoring
        if not hasattr(self, '_connection_quality'):
            self._connection_quality = {}

        if connection_id not in self._connection_quality:
            self._connection_quality[connection_id] = {
                "total_requests": 0,
                "total_response_time": 0.0,
                "error_count": 0,
                "quality_score": 1.0
            }

        conn_stats = self._connection_quality[connection_id]
        conn_stats["total_requests"] += 1
        conn_stats["total_response_time"] += response_time

        # Calculate quality score (lower is better)
        avg_response_time = conn_stats["total_response_time"] / conn_stats["total_requests"]
        error_rate = conn_stats["error_count"] / conn_stats["total_requests"]
        conn_stats["quality_score"] = avg_response_time * (1 + error_rate * 2)

    def _categorize_error_severity(self, error_type: str) -> str:
        """Categorize error severity for intelligent handling"""
        critical_patterns = [
            "websocket connection error", "timeout", "memory", "leak", "critical"
        ]
        high_patterns = [
            "parsing error", "protocol error", "overloaded", "refused"
        ]

        error_lower = error_type.lower()

        if any(pattern in error_lower for pattern in critical_patterns):
            return "critical"
        elif any(pattern in error_lower for pattern in high_patterns):
            return "high"
        elif "outlier" in error_lower:
            return "medium"
        else:
            return "low"

    async def _emergency_error_cleanup(self) -> None:
        """Emergency cleanup when critical error rate is detected"""
        self.logger.warning("Emergency error cleanup triggered due to high critical error rate")

        # Force garbage collection
        if hasattr(self.memory_manager, 'force_garbage_collection'):
            gc_stats = self.memory_manager.force_garbage_collection()
            self.logger.info(f"Emergency GC: {gc_stats.get('total_collected', 0)} objects collected")

        # Clear error log to prevent memory buildup
        self.error_log.clear()

        # Reset connection quality tracking
        if hasattr(self, '_connection_quality'):
            self._connection_quality.clear()

    def _update_metrics_cache(self, metrics: PerformanceMetrics) -> None:
        """Update frequently accessed metrics cache"""
        current_time = time.time()

        # Cache current metrics for quick access
        self._response_cache["current_metrics"] = (metrics, current_time)

        # Cache aggregated statistics
        if len(self.metrics_history) >= 10:
            recent_metrics = self.metrics_history.get_recent(10)
            avg_cpu = statistics.mean([m.cpu_percent for m in recent_metrics])
            avg_memory = statistics.mean([m.memory_mb for m in recent_metrics])

            self._response_cache["aggregated_stats"] = ({
                "avg_cpu_10min": avg_cpu,
                "avg_memory_10min": avg_memory,
                "total_requests": metrics.total_requests,
                "current_error_rate": metrics.error_rate
            }, current_time)

    def _update_tool_cache(self, cache_key: str, execution_time: float) -> None:
        """Update tool performance cache"""
        current_time = time.time()

        if cache_key not in self._response_cache:
            self._response_cache[cache_key] = ({
                "count": 0,
                "total_time": 0.0,
                "min_time": float('inf'),
                "max_time": 0.0
            }, current_time)

        cached_data, _ = self._response_cache[cache_key]
        cached_data["count"] += 1
        cached_data["total_time"] += execution_time
        cached_data["min_time"] = min(cached_data["min_time"], execution_time)
        cached_data["max_time"] = max(cached_data["max_time"], execution_time)
        cached_data["avg_time"] = cached_data["total_time"] / cached_data["count"]

        self._response_cache[cache_key] = (cached_data, current_time)

    @track_memory_usage
    def get_memory_status(self) -> Dict[str, Any]:
        """Get comprehensive memory status for the monitor"""
        return {
            "performance_monitor": {
                "metrics_history": self.metrics_history.get_stats(),
                "tool_metrics_count": len(self.tool_metrics),
                "error_log": self.error_log.get_stats(),
                "active_websockets": len(self._active_websockets),
                "tracked_connections": self.active_connections,
                "response_times": self.response_times.get_stats(),
                "response_time_stats": self._response_time_stats,
                "cache_size": len(getattr(self, '_response_cache', {})),
                "inactive_connections": len(self._connection_last_activity)
            },
            "memory_manager": self.memory_manager.get_status()
        }

async def main():
    """Main monitoring function"""
    import argparse

    parser = argparse.ArgumentParser(description="UnrealBlueprintMCP Performance Monitor")
    parser.add_argument('--server-url', default="ws://localhost:6277", help="MCP server WebSocket URL")
    parser.add_argument('--interval', type=float, default=5.0, help="Collection interval in seconds")
    parser.add_argument('--benchmark', help="Benchmark specific tool")
    parser.add_argument('--benchmark-args', default="{}", help="Benchmark tool arguments (JSON)")
    parser.add_argument('--iterations', type=int, default=10, help="Benchmark iterations")
    parser.add_argument('--export', help="Export metrics to file")

    args = parser.parse_args()

    monitor = PerformanceMonitor(args.server_url, args.interval)

    try:
        if args.benchmark:
            # Run benchmark
            benchmark_args = json.loads(args.benchmark_args)
            metrics = await monitor.benchmark_tool_performance(
                args.benchmark, benchmark_args, args.iterations
            )

            if metrics and args.export:
                monitor.export_metrics(args.export)

        else:
            # Run continuous monitoring
            await monitor.start_monitoring()

    except KeyboardInterrupt:
        print("\nMonitoring stopped by user")
    except Exception as e:
        print(f"Monitoring failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())