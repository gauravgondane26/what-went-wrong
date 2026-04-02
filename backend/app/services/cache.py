"""
In-process TTL LRU cache. No external dependencies.
Three module-level singletons: events, frames360, sequences.
Thread safety: asyncio is single-threaded, but we use asyncio.Lock per key
to prevent duplicate in-flight fetches (see data_loader.py).
"""
from __future__ import annotations

import asyncio
from collections import OrderedDict
from time import time
from typing import Any


class TTLLRUCache:
    def __init__(self, max_size: int = 20, ttl_seconds: int = 3600) -> None:
        self._cache: OrderedDict[str, tuple[Any, float]] = OrderedDict()
        self._max_size = max_size
        self._ttl = ttl_seconds

    def get(self, key: str) -> Any | None:
        if key not in self._cache:
            return None
        value, expires_at = self._cache[key]
        if time() > expires_at:
            del self._cache[key]
            return None
        self._cache.move_to_end(key)
        return value

    def set(self, key: str, value: Any) -> None:
        if key in self._cache:
            self._cache.move_to_end(key)
        self._cache[key] = (value, time() + self._ttl)
        if len(self._cache) > self._max_size:
            self._cache.popitem(last=False)

    def __len__(self) -> int:
        return len(self._cache)


_events_cache = TTLLRUCache(max_size=20, ttl_seconds=3600)
_frames360_cache = TTLLRUCache(max_size=20, ttl_seconds=3600)
_sequence_cache = TTLLRUCache(max_size=50, ttl_seconds=3600)

# Per-key asyncio locks to prevent duplicate concurrent fetches
_fetch_locks: dict[str, asyncio.Lock] = {}


def _lock_key(prefix: str, key: str) -> str:
    return f"{prefix}:{key}"


def get_fetch_lock(prefix: str, key: str) -> asyncio.Lock:
    k = _lock_key(prefix, key)
    if k not in _fetch_locks:
        _fetch_locks[k] = asyncio.Lock()
    return _fetch_locks[k]


def get_events(match_id: int) -> list | None:
    return _events_cache.get(str(match_id))


def set_events(match_id: int, events: list) -> None:
    _events_cache.set(str(match_id), events)


def get_frames360(match_id: int) -> dict | None:
    return _frames360_cache.get(str(match_id))


def set_frames360(match_id: int, frames: dict) -> None:
    _frames360_cache.set(str(match_id), frames)


def get_sequence(match_id: int, goal_event_id: str) -> Any | None:
    return _sequence_cache.get(f"{match_id}:{goal_event_id}")


def set_sequence(match_id: int, goal_event_id: str, value: Any) -> None:
    _sequence_cache.set(f"{match_id}:{goal_event_id}", value)


def total_entries() -> int:
    return len(_events_cache) + len(_frames360_cache) + len(_sequence_cache)
