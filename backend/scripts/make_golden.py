"""
Regenerate tests/fixtures/golden_sequences.json from live StatsBomb data.

The fixture holds 12 real EURO 2020 goal sequences (the ones the redesign
prototype uses) as built by sequence_builder.build_goal_sequence, with the
bulky render-only fields (pressure_grid, cover_shadows) emptied. Tests use
it to check the normalisation invariant and to snapshot collapse detection,
so a deliberate detection change shows up as an explicit diff.

Usage (from backend/):
    python scripts/make_golden.py
Set STATSBOMB_LOCAL_PATH to read from a local open-data clone instead of HTTP.
"""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

import httpx  # noqa: E402

from app.config import HTTP_TIMEOUT_SECONDS  # noqa: E402
from app.services import data_loader  # noqa: E402
from app.services.sequence_builder import build_goal_sequence, find_goal_event  # noqa: E402

FIXTURE = BACKEND / "tests" / "fixtures" / "golden_sequences.json"

# (match_id, goal_event_id): EURO 2020 goals used by the redesign prototype.
GOALS: list[tuple[int, str]] = [
    (3795220, "51e7dde0-e2e5-4e4e-b00a-98a287e5813d"),
    (3795220, "492b2a06-d434-4fc6-ad8f-e9dd5d6aa7d3"),
    (3795506, "6605af47-8d44-4f52-9b8d-65598a9c0ef1"),
    (3795506, "a221a567-b43e-45d6-97f2-07b1cab75d21"),
    (3788769, "9edcdce4-368c-4ae6-ab24-8b688369d80f"),
    (3788769, "9dd74d3f-6d2c-4051-8a27-0486363458a6"),
    (3788769, "61f2991a-ff91-4779-9d8d-89a104c5edd0"),
    (3788769, "3440b2d2-93e7-4ca4-9b31-cc5a0f762b7d"),
    (3788769, "35f6e898-2432-4dfb-859a-ba824c623f4d"),
    (3795221, "3b50aa84-6168-48ab-9996-9210c30c84a1"),
    (3795221, "ccf0702d-716d-4ca8-926d-126f5d067173"),
    (3795221, "99f94455-a4a3-426d-ab7f-09e31ae65bf7"),
]


async def main() -> None:
    sequences = []
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT_SECONDS) as client:
        for match_id, goal_id in GOALS:
            events = await data_loader.load_events(client, match_id)
            frames360 = await data_loader.load_frames360(client, match_id)
            seq = build_goal_sequence(match_id, events, frames360, find_goal_event(events, goal_id))
            for f in seq.frames:
                f.pressure_grid = []
                f.cover_shadows = []
            sequences.append(seq.model_dump())
            print(f"{match_id} {goal_id[:8]}: {len(seq.frames)} frames, collapse={seq.collapse_frame_index}")

    FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    FIXTURE.write_text(json.dumps({"sequences": sequences}, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {FIXTURE.relative_to(BACKEND)} ({FIXTURE.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    asyncio.run(main())
