from __future__ import annotations

import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CODING_DIR = PROJECT_ROOT / "Coding"
if str(CODING_DIR) not in sys.path:
    sys.path.insert(0, str(CODING_DIR))

from cache import LRUCache
from schemas import CacheEntry, CacheStats


def test_cache_entry_schema_validates_values() -> None:
    entry = CacheEntry[str, int](key="alpha", value=1)

    assert entry.key == "alpha"
    assert entry.value == 1


def test_eviction_order_at_capacity_and_access_recency() -> None:
    cache: LRUCache[str, str] = LRUCache(capacity=2)

    cache.put("a", "alpha")
    cache.put("b", "bravo")
    assert cache.get("a") == "alpha"

    cache.put("c", "charlie")
    assert cache.get("b") is None
    assert cache.get("a") == "alpha"
    assert cache.get("c") == "charlie"

    cache.put("d", "delta")
    assert cache.get("a") is None
    assert cache.get("c") == "charlie"
    assert cache.get("d") == "delta"


def test_updates_replace_values_and_refresh_recency() -> None:
    cache: LRUCache[str, int] = LRUCache(capacity=2)

    cache.put("x", 1)
    cache.put("y", 2)
    cache.put("x", 3)
    cache.put("z", 4)

    assert cache.get("y") is None
    assert cache.get("x") == 3
    assert cache.get("z") == 4


def test_hits_misses_stats_are_reported_correctly() -> None:
    cache: LRUCache[int, str] = LRUCache(capacity=3)

    cache.put(1, "one")
    cache.put(2, "two")

    assert cache.get(1) == "one"
    assert cache.get(3) is None
    assert cache.get(2) == "two"

    stats = cache.get_stats()

    assert isinstance(stats, CacheStats)
    assert stats.hits == 2
    assert stats.misses == 1
    assert stats.current_size == 2
    assert stats.capacity == 3
    assert stats.hit_rate == pytest.approx(2 / 3)
    assert stats.miss_rate == pytest.approx(1 / 3)


def test_clear_empties_cache_and_resets_stats() -> None:
    cache: LRUCache[str, str] = LRUCache(capacity=2)

    cache.put("first", "one")
    cache.get("first")
    cache.get("missing")

    cache.clear()

    assert cache.get("first") is None

    stats = cache.get_stats()
    assert stats.hits == 0
    assert stats.misses == 1
    assert stats.current_size == 0
    assert stats.capacity == 2
    assert stats.hit_rate == 0.0
    assert stats.miss_rate == 1.0


def test_zero_capacity_behaves_as_always_empty_cache() -> None:
    cache: LRUCache[str, str] = LRUCache(capacity=0)

    cache.put("a", "alpha")

    assert cache.get("a") is None

    stats = cache.get_stats()
    assert stats.current_size == 0
    assert stats.capacity == 0
    assert stats.hits == 0
    assert stats.misses == 1
    assert stats.hit_rate == 0.0
    assert stats.miss_rate == 1.0


def test_cache_stats_reject_incoherent_values() -> None:
    with pytest.raises(ValidationError, match="current_size cannot exceed capacity"):
        CacheStats(
            hits=1,
            misses=1,
            hit_rate=0.5,
            miss_rate=0.5,
            current_size=3,
            capacity=2,
        )

    with pytest.raises(ValidationError, match="hit_rate must match hits / total_requests"):
        CacheStats(
            hits=2,
            misses=1,
            hit_rate=0.25,
            miss_rate=0.75,
            current_size=1,
            capacity=2,
        )


def test_negative_capacity_is_rejected() -> None:
    with pytest.raises(ValueError, match="greater than or equal to zero"):
        LRUCache(capacity=-1)
