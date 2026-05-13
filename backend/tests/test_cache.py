"""Tests for TTL LRU cache and module-level cache helpers."""
from unittest.mock import patch

from app.services.cache import (
    TTLLRUCache,
    get_events,
    get_frames360,
    get_sequence,
    set_events,
    set_frames360,
    set_sequence,
)


def test_cache_miss_returns_none():
    cache = TTLLRUCache()
    assert cache.get("nonexistent") is None


def test_set_then_get():
    cache = TTLLRUCache()
    cache.set("key1", [1, 2, 3])
    assert cache.get("key1") == [1, 2, 3]


def test_evicts_oldest_when_at_capacity():
    cache = TTLLRUCache(max_size=2)
    cache.set("a", 1)
    cache.set("b", 2)
    cache.set("c", 3)  # "a" is the oldest, evicted
    assert cache.get("a") is None
    assert cache.get("b") == 2
    assert cache.get("c") == 3


def test_lru_reordering_prevents_eviction():
    cache = TTLLRUCache(max_size=2)
    cache.set("a", 1)
    cache.set("b", 2)
    cache.get("a")     # promote "a" → "b" becomes least-recently-used
    cache.set("c", 3)  # "b" should be evicted
    assert cache.get("a") == 1
    assert cache.get("b") is None
    assert cache.get("c") == 3


def test_overwrite_existing_key():
    cache = TTLLRUCache()
    cache.set("k", "first")
    cache.set("k", "second")
    assert cache.get("k") == "second"


def test_expired_entry_returns_none():
    cache = TTLLRUCache(max_size=5, ttl_seconds=10)
    with patch("app.services.cache.time", return_value=1000.0):
        cache.set("k", "v")
    with patch("app.services.cache.time", return_value=1015.0):  # 15s later, past TTL
        result = cache.get("k")
    assert result is None


def test_len_reflects_entry_count():
    cache = TTLLRUCache(max_size=5)
    assert len(cache) == 0
    cache.set("x", 1)
    cache.set("y", 2)
    assert len(cache) == 2


def test_events_cache_roundtrip():
    payload = [{"id": "evt_99999", "type": "Carry"}]
    set_events(99999, payload)
    assert get_events(99999) == payload


def test_frames360_cache_roundtrip():
    payload = {"evt_abc": [{"location": [60.0, 40.0], "teammate": True}]}
    set_frames360(99998, payload)
    assert get_frames360(99998) == payload


def test_sequence_cache_roundtrip():
    set_sequence(99997, "goal-test-abc", {"frames": [], "collapse_frame_index": 0})
    assert get_sequence(99997, "goal-test-abc") == {"frames": [], "collapse_frame_index": 0}
    assert get_sequence(99997, "goal-test-xyz") is None
