from __future__ import annotations

from collections import OrderedDict
from threading import RLock
from typing import Generic, Hashable, Optional, TypeVar

try:  # pragma: no cover - import style depends on how the module is loaded.
    from .schemas import CacheEntry, CacheStats
except ImportError:  # pragma: no cover - fallback for direct module imports.
    from schemas import CacheEntry, CacheStats

KeyT = TypeVar("KeyT", bound=Hashable)
ValueT = TypeVar("ValueT")


class LRUCache(Generic[KeyT, ValueT]):
    def __init__(self, capacity: int) -> None:
        if capacity < 0:
            raise ValueError("capacity must be greater than or equal to zero")

        self._capacity = capacity
        self._entries: OrderedDict[KeyT, CacheEntry[KeyT, ValueT]] = OrderedDict()
        self._hits = 0
        self._misses = 0
        self._lock = RLock()

    @property
    def capacity(self) -> int:
        return self._capacity

    def get(self, key: KeyT) -> Optional[ValueT]:
        with self._lock:
            entry = self._entries.get(key)
            if entry is None:
                self._misses += 1
                return None

            self._entries.move_to_end(key)
            self._hits += 1
            return entry.value

    def put(self, key: KeyT, value: ValueT) -> None:
        with self._lock:
            if self._capacity == 0:
                return

            self._entries[key] = CacheEntry(key=key, value=value)
            self._entries.move_to_end(key)

            while len(self._entries) > self._capacity:
                self._entries.popitem(last=False)

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()
            self._hits = 0
            self._misses = 0

    def get_stats(self) -> CacheStats:
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = self._hits / total_requests if total_requests else 0.0
            miss_rate = self._misses / total_requests if total_requests else 0.0

            return CacheStats(
                hits=self._hits,
                misses=self._misses,
                hit_rate=hit_rate,
                miss_rate=miss_rate,
                current_size=len(self._entries),
                capacity=self._capacity,
            )
