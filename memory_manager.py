#!/usr/bin/env python3
"""
Memory Management Module for UnrealBlueprintMCP

Provides memory optimization, leak detection, and efficient resource management
for the MCP server with asyncio-safe operations.
"""

import gc
import sys
import weakref
import asyncio
import psutil
import logging
import threading
import tracemalloc
import gzip
import pickle
import hashlib
from datetime import datetime, timedelta
from collections import deque, defaultdict
from typing import Any, Dict, List, Optional, Callable, Union, Set, Tuple, Generic, TypeVar
from dataclasses import dataclass, asdict, field
from contextlib import asynccontextmanager
import json
import time
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class MemoryStats:
    """Memory usage statistics"""
    timestamp: float
    rss_mb: float  # Resident Set Size in MB
    vms_mb: float  # Virtual Memory Size in MB
    percent: float  # Memory percentage
    available_mb: float  # Available system memory in MB
    gc_objects: int  # Number of objects tracked by GC
    gc_collections: Dict[int, int]  # GC collections per generation


@dataclass
class MemoryLeak:
    """Memory leak detection result"""
    timestamp: float
    leak_type: str
    description: str
    size_mb: float
    traceback: Optional[str] = None
    severity: str = "medium"  # low, medium, high, critical


@dataclass
class CacheEntry:
    """TTL cache entry with compression support"""
    value: Any
    created_at: float
    ttl: float
    access_count: int = 0
    last_accessed: float = field(default_factory=time.time)
    compressed: bool = False
    original_size: int = 0
    compressed_size: int = 0


T = TypeVar('T')

class CircularBuffer(Generic[T]):
    """
    Enhanced thread-safe circular buffer with automatic memory management,
    compression support, and intelligent eviction policies.
    """

    def __init__(self, maxlen: int, enable_compression: bool = False,
                 compression_threshold: int = 1024):
        self.maxlen = maxlen
        self.enable_compression = enable_compression
        self.compression_threshold = compression_threshold
        self._data = deque(maxlen=maxlen)
        self._lock = threading.Lock()
        self._access_stats: Dict[int, int] = defaultdict(int)  # Track access frequency
        self._memory_usage = 0
        self._compressed_count = 0

    def append(self, item: T) -> None:
        """Add item to buffer with optional compression"""
        with self._lock:
            processed_item = self._process_item_for_storage(item)
            self._data.append(processed_item)
            self._update_memory_stats()

    def extend(self, items: List[T]) -> None:
        """Add multiple items to buffer"""
        with self._lock:
            processed_items = [self._process_item_for_storage(item) for item in items]
            self._data.extend(processed_items)
            self._update_memory_stats()

    def get_all(self) -> List[T]:
        """Get all items in buffer as list"""
        with self._lock:
            return [self._decompress_item(item) for item in self._data]

    def get_recent(self, count: int) -> List[T]:
        """Get the most recent N items"""
        with self._lock:
            recent_data = list(self._data)[-count:] if len(self._data) >= count else list(self._data)
            return [self._decompress_item(item) for item in recent_data]

    def clear(self) -> None:
        """Clear all items from buffer"""
        with self._lock:
            self._data.clear()
            self._access_stats.clear()
            self._memory_usage = 0
            self._compressed_count = 0

    def __len__(self) -> int:
        with self._lock:
            return len(self._data)

    @property
    def is_full(self) -> bool:
        """Check if buffer is at capacity"""
        with self._lock:
            return len(self._data) == self.maxlen

    @property
    def memory_usage_mb(self) -> float:
        """Get estimated memory usage in MB"""
        with self._lock:
            return self._memory_usage / (1024 * 1024)

    @property
    def compression_ratio(self) -> float:
        """Get compression ratio"""
        with self._lock:
            return self._compressed_count / max(len(self._data), 1)

    def _process_item_for_storage(self, item: T) -> Union[T, bytes]:
        """Process item for storage with optional compression"""
        if not self.enable_compression:
            return item

        # Estimate item size
        item_size = self._estimate_size(item)

        if item_size > self.compression_threshold:
            try:
                # Compress large items
                serialized = pickle.dumps(item)
                compressed = gzip.compress(serialized)

                if len(compressed) < len(serialized) * 0.8:  # Only compress if >20% savings
                    self._compressed_count += 1
                    return compressed
            except Exception as e:
                logger.warning(f"Compression failed for item: {e}")

        return item

    def _decompress_item(self, item: Union[T, bytes]) -> T:
        """Decompress item if it was compressed"""
        if isinstance(item, bytes) and self.enable_compression:
            try:
                decompressed = gzip.decompress(item)
                return pickle.loads(decompressed)
            except Exception as e:
                logger.warning(f"Decompression failed: {e}")
                return item
        return item

    def _estimate_size(self, obj: Any) -> int:
        """Estimate object size in bytes"""
        if hasattr(obj, '__sizeof__'):
            return obj.__sizeof__()
        return sys.getsizeof(obj)

    def _update_memory_stats(self) -> None:
        """Update memory usage statistics"""
        total_size = sum(self._estimate_size(item) for item in self._data)
        self._memory_usage = total_size

    def get_stats(self) -> Dict[str, Any]:
        """Get buffer statistics"""
        with self._lock:
            return {
                "length": len(self._data),
                "maxlen": self.maxlen,
                "memory_usage_mb": self.memory_usage_mb,
                "compression_enabled": self.enable_compression,
                "compression_ratio": self.compression_ratio,
                "compressed_items": self._compressed_count,
                "is_full": self.is_full
            }


class WeakReferenceManager:
    """
    Manages weak references to prevent circular references and memory leaks.
    """

    def __init__(self):
        self._refs: Set[weakref.ref] = set()
        self._callbacks: Dict[int, Callable] = {}

    def add_reference(self, obj: Any, callback: Optional[Callable] = None) -> weakref.ref:
        """Add weak reference to object with optional cleanup callback"""
        def cleanup_ref(ref):
            self._refs.discard(ref)
            if callback:
                try:
                    callback()
                except Exception as e:
                    logger.warning(f"Weak reference cleanup callback failed: {e}")

        ref = weakref.ref(obj, cleanup_ref)
        self._refs.add(ref)
        return ref

    def cleanup_dead_references(self) -> int:
        """Remove dead references and return count of cleaned up refs"""
        alive_refs = set()
        dead_count = 0

        for ref in self._refs:
            if ref() is not None:
                alive_refs.add(ref)
            else:
                dead_count += 1

        self._refs = alive_refs
        return dead_count

    def get_alive_count(self) -> int:
        """Get count of alive references"""
        return sum(1 for ref in self._refs if ref() is not None)


class TTLCache:
    """
    Thread-safe TTL (Time To Live) cache with automatic cleanup and compression.
    """

    def __init__(self, default_ttl: float = 3600.0, max_size: int = 1000,
                 enable_compression: bool = True, cleanup_interval: float = 300.0):
        self.default_ttl = default_ttl
        self.max_size = max_size
        self.enable_compression = enable_compression
        self.cleanup_interval = cleanup_interval

        self._cache: Dict[str, CacheEntry] = {}
        self._lock = threading.RLock()
        self._access_order: deque = deque()  # LRU tracking
        self._cleanup_task: Optional[asyncio.Task] = None
        self._running = False

    async def start(self) -> None:
        """Start the cache cleanup task"""
        if self._running:
            return

        self._running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("TTL Cache started")

    async def stop(self) -> None:
        """Stop the cache and cleanup"""
        self._running = False
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        self.clear()
        logger.info("TTL Cache stopped")

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        with self._lock:
            if key not in self._cache:
                return None

            entry = self._cache[key]
            current_time = time.time()

            # Check if expired
            if current_time - entry.created_at > entry.ttl:
                del self._cache[key]
                return None

            # Update access stats
            entry.access_count += 1
            entry.last_accessed = current_time

            # Move to end of access order (most recently used)
            try:
                self._access_order.remove(key)
            except ValueError:
                pass
            self._access_order.append(key)

            return self._decompress_value(entry)

    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """Set value in cache with TTL"""
        with self._lock:
            if len(self._cache) >= self.max_size and key not in self._cache:
                self._evict_lru()

            ttl = ttl or self.default_ttl
            compressed_value, original_size, compressed_size, is_compressed = self._compress_value(value)

            entry = CacheEntry(
                value=compressed_value,
                created_at=time.time(),
                ttl=ttl,
                compressed=is_compressed,
                original_size=original_size,
                compressed_size=compressed_size
            )

            self._cache[key] = entry

            # Update access order
            try:
                self._access_order.remove(key)
            except ValueError:
                pass
            self._access_order.append(key)

    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                try:
                    self._access_order.remove(key)
                except ValueError:
                    pass
                return True
            return False

    def clear(self) -> None:
        """Clear all cache entries"""
        with self._lock:
            self._cache.clear()
            self._access_order.clear()

    def cleanup_expired(self) -> int:
        """Remove expired entries and return count"""
        with self._lock:
            current_time = time.time()
            expired_keys = []

            for key, entry in self._cache.items():
                if current_time - entry.created_at > entry.ttl:
                    expired_keys.append(key)

            for key in expired_keys:
                del self._cache[key]
                try:
                    self._access_order.remove(key)
                except ValueError:
                    pass

            return len(expired_keys)

    def _evict_lru(self) -> None:
        """Evict least recently used entry"""
        if self._access_order:
            lru_key = self._access_order.popleft()
            self._cache.pop(lru_key, None)

    def _compress_value(self, value: Any) -> Tuple[Any, int, int, bool]:
        """Compress value if beneficial"""
        if not self.enable_compression:
            original_size = sys.getsizeof(value)
            return value, original_size, original_size, False

        try:
            serialized = pickle.dumps(value)
            original_size = len(serialized)

            if original_size > 1024:  # Only compress if >1KB
                compressed = gzip.compress(serialized)
                compressed_size = len(compressed)

                if compressed_size < original_size * 0.8:  # >20% compression
                    return compressed, original_size, compressed_size, True

            return value, original_size, original_size, False
        except Exception as e:
            logger.warning(f"Cache compression failed: {e}")
            original_size = sys.getsizeof(value)
            return value, original_size, original_size, False

    def _decompress_value(self, entry: CacheEntry) -> Any:
        """Decompress cache entry value"""
        if not entry.compressed:
            return entry.value

        try:
            decompressed = gzip.decompress(entry.value)
            return pickle.loads(decompressed)
        except Exception as e:
            logger.warning(f"Cache decompression failed: {e}")
            return entry.value

    async def _cleanup_loop(self) -> None:
        """Periodic cleanup of expired entries"""
        while self._running:
            try:
                await asyncio.sleep(self.cleanup_interval)
                expired_count = self.cleanup_expired()
                if expired_count > 0:
                    logger.debug(f"TTL Cache cleaned up {expired_count} expired entries")
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in TTL cache cleanup: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self._lock:
            total_original_size = sum(entry.original_size for entry in self._cache.values())
            total_compressed_size = sum(entry.compressed_size for entry in self._cache.values())
            compressed_entries = sum(1 for entry in self._cache.values() if entry.compressed)

            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "compressed_entries": compressed_entries,
                "compression_ratio": total_compressed_size / max(total_original_size, 1),
                "memory_saved_mb": (total_original_size - total_compressed_size) / (1024 * 1024),
                "hit_rate": 0.0,  # TODO: Track hits/misses
                "default_ttl": self.default_ttl
            }


class MemoryProfiler:
    """
    Advanced memory profiler with intelligent leak detection and reporting.
    """

    def __init__(self, enable_tracemalloc: bool = True):
        self.enable_tracemalloc = enable_tracemalloc
        self.memory_history = CircularBuffer[MemoryStats](maxlen=1000, enable_compression=True)
        self.leak_history = CircularBuffer[MemoryLeak](maxlen=100)
        self.baseline_memory: Optional[float] = None
        self.last_gc_stats: Optional[Dict[int, int]] = None
        self._monitoring = False
        self._monitor_task: Optional[asyncio.Task] = None
        self._leak_detection_sensitivity = 1.5  # Memory growth multiplier for leak detection
        self._consecutive_growth_threshold = 3  # Number of consecutive growth periods
        self._consecutive_growth_count = 0

        if enable_tracemalloc and not tracemalloc.is_tracing():
            tracemalloc.start()

    async def start_monitoring(self, interval: float = 30.0) -> None:
        """Start continuous memory monitoring"""
        if self._monitoring:
            return

        self._monitoring = True
        self._monitor_task = asyncio.create_task(self._monitor_loop(interval))
        logger.info("Memory monitoring started")

    async def stop_monitoring(self) -> None:
        """Stop memory monitoring"""
        self._monitoring = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("Memory monitoring stopped")

    async def _monitor_loop(self, interval: float) -> None:
        """Main monitoring loop"""
        while self._monitoring:
            try:
                stats = self.collect_memory_stats()
                self.memory_history.append(stats)

                # Check for memory leaks
                leak = self.detect_memory_leak(stats)
                if leak:
                    self.leak_history.append(leak)
                    logger.warning(f"Memory leak detected: {leak.description}")

                await asyncio.sleep(interval)
            except Exception as e:
                logger.error(f"Error in memory monitoring loop: {e}")
                await asyncio.sleep(interval)

    def collect_memory_stats(self) -> MemoryStats:
        """Collect current memory statistics"""
        process = psutil.Process()
        memory_info = process.memory_info()
        system_memory = psutil.virtual_memory()

        # Get GC statistics
        gc_stats = {}
        for i in range(3):  # Python has 3 GC generations
            gc_stats[i] = gc.get_count()[i]

        return MemoryStats(
            timestamp=time.time(),
            rss_mb=memory_info.rss / (1024 * 1024),
            vms_mb=memory_info.vms / (1024 * 1024),
            percent=process.memory_percent(),
            available_mb=system_memory.available / (1024 * 1024),
            gc_objects=len(gc.get_objects()),
            gc_collections=gc_stats
        )

    def detect_memory_leak(self, current_stats: MemoryStats) -> Optional[MemoryLeak]:
        """Intelligent memory leak detection with multiple algorithms"""
        if self.baseline_memory is None:
            self.baseline_memory = current_stats.rss_mb
            return None

        # Algorithm 1: Absolute growth detection
        memory_growth = current_stats.rss_mb - self.baseline_memory
        if memory_growth > 100:  # Increased threshold to 100MB
            severity = "critical" if memory_growth > 500 else "high"
            leak = MemoryLeak(
                timestamp=current_stats.timestamp,
                leak_type="absolute_growth",
                description=f"Memory grew by {memory_growth:.1f}MB since baseline",
                size_mb=memory_growth,
                severity=severity
            )
            self.baseline_memory = current_stats.rss_mb
            return leak

        # Algorithm 2: Trend-based detection
        if len(self.memory_history) >= 5:
            recent_stats = self.memory_history.get_recent(5)
            memory_trend = [s.rss_mb for s in recent_stats]

            # Check for consistent growth
            is_growing = all(memory_trend[i] <= memory_trend[i + 1] for i in range(len(memory_trend) - 1))

            if is_growing:
                self._consecutive_growth_count += 1
                growth_rate = (memory_trend[-1] - memory_trend[0]) / len(memory_trend)

                if (self._consecutive_growth_count >= self._consecutive_growth_threshold and
                    growth_rate > 5):  # >5MB per monitoring cycle

                    severity = "high" if growth_rate > 20 else "medium"
                    leak = MemoryLeak(
                        timestamp=current_stats.timestamp,
                        leak_type="trend_growth",
                        description=f"Consistent memory growth: {growth_rate:.1f}MB/cycle for {self._consecutive_growth_count} cycles",
                        size_mb=growth_rate * self._consecutive_growth_count,
                        severity=severity
                    )
                    self._consecutive_growth_count = 0
                    return leak
            else:
                self._consecutive_growth_count = 0

        # Algorithm 3: GC object explosion detection
        if len(self.memory_history) > 10:
            recent_stats = self.memory_history.get_recent(10)
            avg_objects = sum(s.gc_objects for s in recent_stats) / len(recent_stats)
            object_growth_ratio = current_stats.gc_objects / max(avg_objects, 1)

            if object_growth_ratio > self._leak_detection_sensitivity:
                severity = "critical" if object_growth_ratio > 3.0 else "high"

                # Get traceback if tracemalloc is enabled
                traceback_info = None
                if self.enable_tracemalloc and tracemalloc.is_tracing():
                    try:
                        current_traces = tracemalloc.take_snapshot()
                        top_stats = current_traces.statistics('traceback')[:3]
                        traceback_info = '\n'.join(str(stat) for stat in top_stats)
                    except Exception as e:
                        logger.warning(f"Failed to get traceback: {e}")

                return MemoryLeak(
                    timestamp=current_stats.timestamp,
                    leak_type="object_explosion",
                    description=f"GC objects exploded: {current_stats.gc_objects} (avg: {avg_objects:.0f}, ratio: {object_growth_ratio:.2f})",
                    size_mb=0,
                    severity=severity,
                    traceback=traceback_info
                )

        # Algorithm 4: Memory percentage threshold
        if current_stats.percent > 85:  # >85% system memory usage
            return MemoryLeak(
                timestamp=current_stats.timestamp,
                leak_type="high_memory_usage",
                description=f"High system memory usage: {current_stats.percent:.1f}%",
                size_mb=current_stats.rss_mb,
                severity="critical"
            )

        return None

    def get_memory_report(self) -> Dict[str, Any]:
        """Generate comprehensive memory report"""
        current_stats = self.collect_memory_stats()
        recent_stats = self.memory_history.get_recent(10)

        if recent_stats:
            avg_memory = sum(s.rss_mb for s in recent_stats) / len(recent_stats)
            peak_memory = max(s.rss_mb for s in recent_stats)
        else:
            avg_memory = current_stats.rss_mb
            peak_memory = current_stats.rss_mb

        return {
            "current_memory_mb": current_stats.rss_mb,
            "average_memory_mb": avg_memory,
            "peak_memory_mb": peak_memory,
            "memory_percent": current_stats.percent,
            "available_memory_mb": current_stats.available_mb,
            "gc_objects": current_stats.gc_objects,
            "memory_history_count": len(self.memory_history),
            "detected_leaks": len(self.leak_history),
            "recent_leaks": [asdict(leak) for leak in self.leak_history.get_recent(5)]
        }


class JSONStreamProcessor:
    """
    High-performance JSON message streaming processor with memory optimization.
    """

    def __init__(self, chunk_size: int = 8192, max_message_size: int = 50 * 1024 * 1024):
        self.chunk_size = chunk_size
        self.max_message_size = max_message_size
        self._buffer = BytesIO()
        self._executor = ThreadPoolExecutor(max_workers=2)

    async def process_large_json(self, data: Union[str, bytes]) -> Dict[str, Any]:
        """Process large JSON data with streaming to avoid memory spikes"""
        if isinstance(data, str):
            data = data.encode('utf-8')

        if len(data) > self.max_message_size:
            raise ValueError(f"Message too large: {len(data)} bytes > {self.max_message_size}")

        # For very large messages, use streaming parsing
        if len(data) > self.chunk_size * 10:
            return await self._stream_parse_json(data)
        else:
            # Regular parsing for smaller messages
            return json.loads(data.decode('utf-8'))

    async def _stream_parse_json(self, data: bytes) -> Dict[str, Any]:
        """Stream parse large JSON to reduce memory usage"""
        loop = asyncio.get_event_loop()

        def parse_in_thread():
            try:
                # Use a more memory-efficient approach for large JSON
                # This is a simplified streaming parser - in production you might use
                # libraries like ijson for true streaming JSON parsing
                return json.loads(data.decode('utf-8'))
            except Exception as e:
                logger.error(f"JSON streaming parse failed: {e}")
                raise

        return await loop.run_in_executor(self._executor, parse_in_thread)

    async def compress_json_response(self, data: Dict[str, Any],
                                   compression_threshold: int = 1024) -> Union[str, bytes]:
        """Compress JSON response if it exceeds threshold"""
        json_str = json.dumps(data)
        json_bytes = json_str.encode('utf-8')

        if len(json_bytes) > compression_threshold:
            loop = asyncio.get_event_loop()

            def compress_in_thread():
                return gzip.compress(json_bytes)

            compressed = await loop.run_in_executor(self._executor, compress_in_thread)
            if len(compressed) < len(json_bytes) * 0.8:  # >20% compression
                logger.debug(f"JSON compressed: {len(json_bytes)} -> {len(compressed)} bytes")
                return compressed

        return json_str

    def cleanup(self):
        """Cleanup resources"""
        self._buffer.close()
        self._executor.shutdown(wait=False)


class IntelligentGarbageCollector:
    """
    Intelligent garbage collector that adapts to application load and memory patterns.
    """

    def __init__(self, baseline_interval: float = 600.0):
        self.baseline_interval = baseline_interval
        self.dynamic_interval = baseline_interval
        self.memory_pressure_threshold = 0.8  # 80% memory usage
        self.recent_gc_stats: List[Dict[str, int]] = []
        self.last_gc_time = time.time()
        self.adaptive_mode = True

    def should_run_gc(self, memory_stats: MemoryStats) -> bool:
        """Determine if GC should run based on intelligent analysis"""
        current_time = time.time()
        time_since_last = current_time - self.last_gc_time

        # Always run if we've exceeded the maximum interval
        if time_since_last > self.baseline_interval * 2:
            return True

        # High memory pressure - run GC more frequently
        if memory_stats.percent > self.memory_pressure_threshold * 100:
            return time_since_last > self.dynamic_interval * 0.5

        # Normal conditions - use adaptive interval
        return time_since_last > self.dynamic_interval

    def run_intelligent_gc(self, memory_stats: MemoryStats) -> Dict[str, int]:
        """Run garbage collection with intelligence"""
        start_time = time.time()
        collected = {}

        # Run incremental GC first (generation 0)
        collected[0] = gc.collect(0)

        # Run higher generations based on memory pressure
        if memory_stats.percent > 70:  # High memory usage
            collected[1] = gc.collect(1)
            if memory_stats.percent > 85:  # Critical memory usage
                collected[2] = gc.collect(2)
        else:
            # Light GC for lower memory usage
            if time.time() - start_time < 0.1:  # Only if quick
                collected[1] = gc.collect(1)

        total_collected = sum(collected.values())
        gc_duration = time.time() - start_time

        # Adapt interval based on GC effectiveness
        if self.adaptive_mode:
            self._adapt_gc_interval(total_collected, gc_duration, memory_stats)

        self.last_gc_time = time.time()
        self.recent_gc_stats.append({
            "timestamp": self.last_gc_time,
            "duration": gc_duration,
            "collected": total_collected
        })

        # Keep only recent stats
        if len(self.recent_gc_stats) > 10:
            self.recent_gc_stats.pop(0)

        logger.info(f"Intelligent GC completed: {total_collected} objects in {gc_duration:.3f}s")
        return collected

    def _adapt_gc_interval(self, objects_collected: int, duration: float, memory_stats: MemoryStats):
        """Adapt GC interval based on performance and effectiveness"""
        # If GC collected many objects, increase frequency slightly
        if objects_collected > 1000:
            self.dynamic_interval = max(self.dynamic_interval * 0.9, self.baseline_interval * 0.5)
        # If GC collected few objects and memory is stable, decrease frequency
        elif objects_collected < 100 and memory_stats.percent < 50:
            self.dynamic_interval = min(self.dynamic_interval * 1.1, self.baseline_interval * 1.5)

        # If GC is taking too long, increase interval
        if duration > 1.0:  # GC taking >1 second
            self.dynamic_interval = min(self.dynamic_interval * 1.2, self.baseline_interval * 2)


class MemoryManager:
    """
    Comprehensive memory management system for asyncio applications with advanced optimization.

    Features:
    - Intelligent garbage collection
    - Memory leak detection with multiple algorithms
    - Connection pool management with automatic cleanup
    - Resource cleanup with context managers
    - TTL caching with compression
    - Large JSON message streaming
    - Memory compression and optimization
    """

    def __init__(self,
                 max_connections: int = 100,
                 gc_interval: float = 600.0,  # 10 minutes
                 monitor_interval: float = 30.0,
                 enable_compression: bool = True,
                 enable_ttl_cache: bool = True):
        self.max_connections = max_connections
        self.gc_interval = gc_interval
        self.monitor_interval = monitor_interval
        self.enable_compression = enable_compression
        self.enable_ttl_cache = enable_ttl_cache

        # Core components
        self.profiler = MemoryProfiler(enable_tracemalloc=True)
        self.weak_refs = WeakReferenceManager()
        self.intelligent_gc = IntelligentGarbageCollector(gc_interval)
        self.json_processor = JSONStreamProcessor()

        # Resource tracking
        self.active_connections: Set[weakref.ref] = set()
        self.resource_pools: Dict[str, CircularBuffer] = {}

        # TTL Cache
        self.ttl_cache: Optional[TTLCache] = None
        if enable_ttl_cache:
            self.ttl_cache = TTLCache(
                default_ttl=3600.0,  # 1 hour
                max_size=1000,
                enable_compression=enable_compression
            )

        # Background tasks
        self._gc_task: Optional[asyncio.Task] = None
        self._running = False
        self._memory_pressure_mode = False

        logger.info(f"MemoryManager initialized with max_connections={max_connections}, "
                   f"compression={enable_compression}, ttl_cache={enable_ttl_cache}")

    async def start(self) -> None:
        """Start memory management services"""
        if self._running:
            return

        self._running = True

        # Start TTL cache
        if self.ttl_cache:
            await self.ttl_cache.start()

        # Start monitoring and garbage collection
        await self.profiler.start_monitoring(self.monitor_interval)
        self._gc_task = asyncio.create_task(self._intelligent_gc_loop())

        logger.info("Enhanced MemoryManager started with intelligent GC and compression")

    async def stop(self) -> None:
        """Stop memory management services"""
        self._running = False

        await self.profiler.stop_monitoring()

        if self.ttl_cache:
            await self.ttl_cache.stop()

        if self._gc_task:
            self._gc_task.cancel()
            try:
                await self._gc_task
            except asyncio.CancelledError:
                pass

        # Cleanup JSON processor
        self.json_processor.cleanup()

        # Final cleanup
        self.cleanup_all_resources()
        logger.info("Enhanced MemoryManager stopped")

    async def _intelligent_gc_loop(self) -> None:
        """Intelligent periodic garbage collection loop"""
        while self._running:
            try:
                # Dynamic sleep based on memory pressure
                sleep_interval = self.intelligent_gc.dynamic_interval
                if self._memory_pressure_mode:
                    sleep_interval *= 0.5  # More frequent GC under pressure

                await asyncio.sleep(sleep_interval)

                # Get current memory stats for intelligent decisions
                current_stats = self.profiler.collect_memory_stats()

                # Update memory pressure mode
                self._memory_pressure_mode = current_stats.percent > 75

                # Run intelligent GC if needed
                if self.intelligent_gc.should_run_gc(current_stats):
                    self.intelligent_gc.run_intelligent_gc(current_stats)

                    # Check for memory leaks after GC
                    leak = self.profiler.detect_memory_leak(current_stats)
                    if leak and leak.severity in ['high', 'critical']:
                        logger.warning(f"Critical memory leak detected: {leak.description}")
                        # Emergency cleanup
                        await self._emergency_cleanup()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in intelligent garbage collection loop: {e}")

    def force_garbage_collection(self) -> Dict[str, int]:
        """Force immediate garbage collection and return statistics"""
        # Clean up weak references first
        dead_refs = self.weak_refs.cleanup_dead_references()

        # Use intelligent GC
        current_stats = self.profiler.collect_memory_stats()
        collected = self.intelligent_gc.run_intelligent_gc(current_stats)

        total_collected = sum(collected.values())

        logger.info(f"Garbage collection completed: {total_collected} objects collected, "
                   f"{dead_refs} dead references cleaned")

        return {
            "collected_objects": collected,
            "total_collected": total_collected,
            "dead_references": dead_refs,
            "gc_interval": self.intelligent_gc.dynamic_interval
        }

    def register_connection(self, connection: Any) -> bool:
        """Register a new connection with automatic cleanup"""
        if len(self.active_connections) >= self.max_connections:
            logger.warning(f"Connection limit reached ({self.max_connections}), rejecting new connection")
            return False

        # Add weak reference with cleanup callback
        def cleanup_callback():
            logger.debug("Connection automatically cleaned up via weak reference")

        ref = self.weak_refs.add_reference(connection, cleanup_callback)
        self.active_connections.add(ref)

        logger.debug(f"Connection registered. Active: {len(self.active_connections)}")
        return True

    def unregister_connection(self, connection: Any) -> None:
        """Unregister a connection"""
        # Find and remove the weak reference
        to_remove = None
        for ref in self.active_connections:
            if ref() is connection:
                to_remove = ref
                break

        if to_remove:
            self.active_connections.discard(to_remove)
            logger.debug(f"Connection unregistered. Active: {len(self.active_connections)}")

    def get_resource_pool(self, name: str, maxlen: int = 1000) -> CircularBuffer:
        """Get or create a resource pool with enhanced circular buffer"""
        if name not in self.resource_pools:
            self.resource_pools[name] = CircularBuffer(
                maxlen=maxlen,
                enable_compression=self.enable_compression,
                compression_threshold=1024
            )
        return self.resource_pools[name]

    async def _emergency_cleanup(self) -> None:
        """Emergency cleanup when critical memory leaks are detected"""
        logger.warning("Performing emergency memory cleanup")

        # Clean up TTL cache
        if self.ttl_cache:
            expired_count = self.ttl_cache.cleanup_expired()
            logger.info(f"Emergency: cleaned {expired_count} expired cache entries")

        # Clean up resource pools
        total_cleared = 0
        for name, pool in self.resource_pools.items():
            pool_size = len(pool)
            pool.clear()
            total_cleared += pool_size
            logger.debug(f"Emergency: cleared resource pool '{name}' ({pool_size} items)")

        # Force aggressive GC
        collected = self.force_garbage_collection()

        logger.warning(f"Emergency cleanup completed: {total_cleared} pool items cleared, "
                      f"{collected['total_collected']} objects collected")

    # Enhanced cache methods
    def cache_set(self, key: str, value: Any, ttl: Optional[float] = None) -> bool:
        """Set value in TTL cache if enabled"""
        if self.ttl_cache:
            self.ttl_cache.set(key, value, ttl)
            return True
        return False

    def cache_get(self, key: str) -> Optional[Any]:
        """Get value from TTL cache if enabled"""
        if self.ttl_cache:
            return self.ttl_cache.get(key)
        return None

    def cache_delete(self, key: str) -> bool:
        """Delete key from TTL cache if enabled"""
        if self.ttl_cache:
            return self.ttl_cache.delete(key)
        return False

    async def process_large_json(self, data: Union[str, bytes]) -> Dict[str, Any]:
        """Process large JSON with streaming optimization"""
        return await self.json_processor.process_large_json(data)

    async def compress_json_response(self, data: Dict[str, Any]) -> Union[str, bytes]:
        """Compress JSON response if beneficial"""
        return await self.json_processor.compress_json_response(data)

    def cleanup_all_resources(self) -> None:
        """Clean up all managed resources"""
        # Clear resource pools
        for pool in self.resource_pools.values():
            pool.clear()

        # Clear connection references
        self.active_connections.clear()

        # Force garbage collection
        self.force_garbage_collection()

        logger.info("All resources cleaned up")

    @asynccontextmanager
    async def managed_resource(self, resource: Any):
        """Context manager for automatic resource cleanup"""
        try:
            # Register resource if it's a connection-like object
            if hasattr(resource, 'close') or hasattr(resource, 'disconnect'):
                self.register_connection(resource)
            yield resource
        finally:
            # Cleanup resource
            try:
                if hasattr(resource, 'close'):
                    if asyncio.iscoroutinefunction(resource.close):
                        await resource.close()
                    else:
                        resource.close()
                elif hasattr(resource, 'disconnect'):
                    if asyncio.iscoroutinefunction(resource.disconnect):
                        await resource.disconnect()
                    else:
                        resource.disconnect()
            except Exception as e:
                logger.warning(f"Error cleaning up resource: {e}")
            finally:
                self.unregister_connection(resource)

    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive memory manager status"""
        status = {
            "running": self._running,
            "memory_pressure_mode": self._memory_pressure_mode,
            "active_connections": len(self.active_connections),
            "max_connections": self.max_connections,
            "alive_weak_refs": self.weak_refs.get_alive_count(),
            "resource_pools": {
                name: pool.get_stats() for name, pool in self.resource_pools.items()
            },
            "memory_report": self.profiler.get_memory_report(),
            "intelligent_gc": {
                "baseline_interval": self.intelligent_gc.baseline_interval,
                "dynamic_interval": self.intelligent_gc.dynamic_interval,
                "adaptive_mode": self.intelligent_gc.adaptive_mode,
                "recent_stats_count": len(self.intelligent_gc.recent_gc_stats)
            },
            "monitor_interval_seconds": self.monitor_interval,
            "compression_enabled": self.enable_compression
        }

        # Add TTL cache stats if enabled
        if self.ttl_cache:
            status["ttl_cache"] = self.ttl_cache.get_stats()

        return status


# Global memory manager instance
_memory_manager: Optional[MemoryManager] = None


def get_memory_manager() -> MemoryManager:
    """Get the global memory manager instance"""
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = MemoryManager()
    return _memory_manager


async def initialize_memory_management() -> MemoryManager:
    """Initialize and start the global memory manager"""
    manager = get_memory_manager()
    await manager.start()
    return manager


async def cleanup_memory_management() -> None:
    """Stop and cleanup the global memory manager"""
    global _memory_manager
    if _memory_manager:
        await _memory_manager.stop()
        _memory_manager = None


# Utility functions for easy usage
def create_circular_buffer(maxlen: int) -> CircularBuffer:
    """Create a new circular buffer"""
    return CircularBuffer(maxlen)


def track_memory_usage(func: Callable) -> Callable:
    """Decorator to track memory usage of a function"""
    def wrapper(*args, **kwargs):
        manager = get_memory_manager()
        before = manager.profiler.collect_memory_stats()

        try:
            result = func(*args, **kwargs)
            return result
        finally:
            after = manager.profiler.collect_memory_stats()
            memory_diff = after.rss_mb - before.rss_mb
            if abs(memory_diff) > 1.0:  # Log if memory changed by >1MB
                logger.debug(f"Function {func.__name__} memory change: {memory_diff:+.1f}MB")

    return wrapper


if __name__ == "__main__":
    # Test the memory manager
    async def test_memory_manager():
        manager = await initialize_memory_management()

        # Test for 30 seconds
        await asyncio.sleep(30)

        print("Memory Manager Status:")
        print(json.dumps(manager.get_status(), indent=2))

        await cleanup_memory_management()

    asyncio.run(test_memory_manager())