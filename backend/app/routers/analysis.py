"""
Main analysis endpoint: load match data, build the GoalSequenceResponse, cache it.

The pipeline itself lives in app/services/sequence_builder.py.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from app.models.frame import GoalSequenceResponse
from app.services import cache, data_loader
from app.services.sequence_builder import (
    GoalNotFoundError,
    No360DataError,
    build_goal_sequence,
    find_goal_event,
)

router = APIRouter(tags=["analysis"])


@router.get(
    "/matches/{match_id}/goals/{goal_event_id}/sequence",
    response_model=GoalSequenceResponse,
)
async def get_goal_sequence(
    match_id: int,
    goal_event_id: str,
    request: Request,
) -> GoalSequenceResponse:
    cached = cache.get_sequence(match_id, goal_event_id)
    if cached is not None:
        return cached

    try:
        events = await data_loader.load_events(request.app.state.http_client, match_id)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Failed to load events: {exc}")

    try:
        frames360 = await data_loader.load_frames360(request.app.state.http_client, match_id)
    except Exception:
        frames360 = {}  # 360 file missing or unavailable — proceed with no player positions

    try:
        goal_event = find_goal_event(events, goal_event_id)
        response = build_goal_sequence(match_id, events, frames360, goal_event)
    except (GoalNotFoundError, No360DataError) as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    cache.set_sequence(match_id, goal_event_id, response)
    return response
