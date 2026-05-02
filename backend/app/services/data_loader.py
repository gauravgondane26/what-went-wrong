"""
Async data loader for StatsBomb open data.
Fetches from raw.githubusercontent.com with retry/backoff.
Respects STATSBOMB_LOCAL_PATH env var for local clones.
"""
from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path

import httpx

from app.config import (
    HTTP_MAX_RETRIES,
    STATSBOMB_BASE_URL,
    STATSBOMB_LOCAL_PATH,
)
from app.services import cache


async def _fetch_url(client: httpx.AsyncClient, url: str) -> list | dict:
    """GET with exponential backoff on 429/503."""
    delay = 1.0
    for attempt in range(HTTP_MAX_RETRIES):
        response = await client.get(url)
        if response.status_code in (429, 503):
            if attempt < HTTP_MAX_RETRIES - 1:
                await asyncio.sleep(delay)
                delay *= 2
                continue
        response.raise_for_status()
        return response.json()
    response.raise_for_status()  # final raise if all retries exhausted


def _local_path(relative: str) -> Path | None:
    if not STATSBOMB_LOCAL_PATH:
        return None
    p = Path(STATSBOMB_LOCAL_PATH) / relative
    return p if p.exists() else None


async def _load(client: httpx.AsyncClient, relative: str) -> list | dict:
    local = _local_path(relative)
    if local:
        return json.loads(local.read_text(encoding="utf-8"))
    url = f"{STATSBOMB_BASE_URL}/{relative}"
    return await _fetch_url(client, url)


async def load_competitions(client: httpx.AsyncClient) -> list[dict]:
    return await _load(client, "competitions.json")


async def load_matches(
    client: httpx.AsyncClient, competition_id: int, season_id: int
) -> list[dict]:
    return await _load(client, f"matches/{competition_id}/{season_id}.json")


async def load_events(client: httpx.AsyncClient, match_id: int) -> list[dict]:
    lock = cache.get_fetch_lock("events", str(match_id))
    async with lock:
        cached = cache.get_events(match_id)
        if cached is not None:
            return cached
        data = await _load(client, f"events/{match_id}.json")
        cache.set_events(match_id, data)
        return data


async def load_frames360(client: httpx.AsyncClient, match_id: int) -> dict[str, list]:
    """Returns dict keyed by event_uuid → freeze_frame player list.

    Returns an empty dict if the 360 file doesn't exist for this match
    (some matches report match_status_360='available' in the metadata but
    have no corresponding file on GitHub).
    """
    lock = cache.get_fetch_lock("frames360", str(match_id))
    async with lock:
        cached = cache.get_frames360(match_id)
        if cached is not None:
            return cached

        try:
            data = await _load(client, f"three-sixty/{match_id}.json")
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                # File missing — cache empty dict so we don't retry on every request
                cache.set_frames360(match_id, {})
                return {}
            raise

        # Convert list → dict for O(1) lookup by event UUID
        frames_dict: dict[str, list] = {}
        for entry in data:
            frames_dict[entry["event_uuid"]] = entry.get("freeze_frame", [])
        cache.set_frames360(match_id, frames_dict)
        return frames_dict
