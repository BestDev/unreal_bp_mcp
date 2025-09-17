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
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any
import statistics

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
    """Real-time performance monitoring for MCP server"""

    def __init__(self, server_url: str = "ws://localhost:6277", collection_interval: float = 5.0):
        self.server_url = server_url
        self.collection_interval = collection_interval
        self.running = False

        # Metrics storage
        self.metrics_history: deque = deque(maxlen=1000)  # Store last 1000 metrics
        self.tool_metrics: Dict[str, List[float]] = defaultdict(list)
        self.error_log: List[Dict] = []

        # Connection tracking
        self.active_connections = 0
        self.total_requests = 0
        self.response_times: deque = deque(maxlen=100)

        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    async def start_monitoring(self):
        """Start the performance monitoring"""
        self.running = True
        self.logger.info("Starting performance monitoring...")

        # Start monitoring tasks
        tasks = [
            asyncio.create_task(self._collect_system_metrics()),
            asyncio.create_task(self._monitor_websocket_health()),
            asyncio.create_task(self._performance_reporter())
        ]

        try:
            await asyncio.gather(*tasks)
        except KeyboardInterrupt:
            self.logger.info("Monitoring stopped by user")
        finally:
            await self.stop_monitoring()

    async def stop_monitoring(self):
        """Stop the performance monitoring"""
        self.running = False
        self.logger.info("Performance monitoring stopped")

    async def _collect_system_metrics(self):
        """Collect system-level performance metrics"""
        while self.running:
            try:
                # Get system metrics
                cpu_percent = psutil.cpu_percent(interval=1)
                memory_info = psutil.virtual_memory()
                memory_mb = memory_info.used / (1024 * 1024)

                # Calculate averages
                avg_response_time = statistics.mean(self.response_times) if self.response_times else 0.0
                error_rate = len(self.error_log) / max(self.total_requests, 1) * 100

                # Tool call counts
                tool_counts = {}
                for tool_name, times in self.tool_metrics.items():
                    tool_counts[tool_name] = len(times)

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

                self.metrics_history.append(metrics)

                await asyncio.sleep(self.collection_interval)

            except Exception as e:
                self.logger.error(f"Error collecting system metrics: {e}")
                await asyncio.sleep(self.collection_interval)

    async def _monitor_websocket_health(self):
        """Monitor WebSocket server health"""
        while self.running:
            try:
                # Test connection to MCP server
                start_time = time.time()
                async with websockets.connect(self.server_url, timeout=5) as websocket:
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

                    # Update metrics
                    self.total_requests += 1
                    self.response_times.append(response_time)

                    # Parse response
                    try:
                        parsed_response = json.loads(response)
                        if "error" in parsed_response:
                            self._record_error("WebSocket health check error", parsed_response["error"])
                    except json.JSONDecodeError:
                        self._record_error("WebSocket response parsing error", response)

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
        """Record an error for metrics"""
        error_entry = {
            "timestamp": time.time(),
            "type": error_type,
            "details": str(error_details)
        }
        self.error_log.append(error_entry)

        # Keep only recent errors
        if len(self.error_log) > 100:
            self.error_log = self.error_log[-100:]

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
                    self.tool_metrics[tool_name].append(execution_time)

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
        if not self.metrics_history:
            return

        recent_metrics = list(self.metrics_history)[-10:]  # Last 10 data points

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
        return self.metrics_history[-1] if self.metrics_history else None

    def get_tool_metrics(self, tool_name: str) -> Optional[ToolCallMetrics]:
        """Get metrics for a specific tool"""
        if tool_name not in self.tool_metrics or not self.tool_metrics[tool_name]:
            return None

        times = self.tool_metrics[tool_name]
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
        """Export metrics to JSON file"""
        export_data = {
            "metrics_history": [asdict(m) for m in self.metrics_history],
            "tool_metrics": {tool: times for tool, times in self.tool_metrics.items()},
            "error_log": self.error_log,
            "export_timestamp": time.time()
        }

        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2)

        self.logger.info(f"Metrics exported to {filename}")

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