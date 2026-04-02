"""
Main analysis endpoint: assembles the full GoalSequenceResponse.

Pipeline:
  load events + 360 → find goal event → extract possession sequence
  → for each event: normalize coords + build FrameData with scores
  → detect collapse frame → return GoalSequenceResponse
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from app.models.frame import FrameData, GoalSequenceResponse
from app.services import cache, collapse, data_loader, normalizer, possession, scorer

router = APIRouter(tags=["analysis"])


def _parse_timestamp(ts: str) -> float:
    """Convert "HH:MM:SS.mmm" to total seconds."""
    try:
        parts = ts.split(":")
        h, m, s = int(parts[0]), int(parts[1]), float(parts[2])
        return h * 3600 + m * 60 + s
    except Exception:
        return 0.0


@router.get(
    "/matches/{match_id}/goals/{goal_event_id}/sequence",
    response_model=GoalSequenceResponse,
)
async def get_goal_sequence(
    match_id: int,
    goal_event_id: str,
    request: Request,
) -> GoalSequenceResponse:
    # Check sequence cache first
    cached = cache.get_sequence(match_id, goal_event_id)
    if cached is not None:
        return cached

    # Load raw data
    try:
        events = await data_loader.load_events(request.app.state.http_client, match_id)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Failed to load events: {exc}")

    try:
        frames360 = await data_loader.load_frames360(request.app.state.http_client, match_id)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Failed to load 360 data: {exc}")

    # Find the goal event
    goal_event = next((e for e in events if e["id"] == goal_event_id), None)
    if goal_event is None:
        raise HTTPException(status_code=404, detail=f"Goal event {goal_event_id} not found")

    # Identify teams
    attacking_team_id: int = goal_event["possession_team"]["id"]
    attacking_team_name: str = goal_event["possession_team"]["name"]

    # Defending team = the other team in the match
    all_team_ids = list({e["team"]["id"] for e in events if e.get("team", {}).get("id")})
    defending_team_id: int = next(
        (tid for tid in all_team_ids if tid != attacking_team_id), attacking_team_id
    )
    team_names = {e["team"]["id"]: e["team"]["name"] for e in events if e.get("team", {}).get("id")}
    defending_team_name: str = team_names.get(defending_team_id, "Unknown")

    # Determine attack direction from the goal event shot location
    attacking_toward_120 = normalizer.detect_attack_direction(goal_event)

    # Extract possession sequence
    sequence = possession.extract_goal_possession_sequence(events, goal_event)

    # Build frames
    frames: list[FrameData] = []
    for i, event in enumerate(sequence):
        event_id = event["id"]
        freeze_frame = frames360.get(event_id, [])

        ball_x, ball_y, players = normalizer.normalize_frame(
            event, freeze_frame, defending_team_id, attacking_toward_120
        )

        scores, shadows, pressure_grid = scorer.score_frame(players, ball_x, ball_y)

        defender_count = sum(1 for p in players if not p.is_attacker and not p.keeper)

        frames.append(
            FrameData(
                frame_index=i,
                event_id=event_id,
                event_type=event.get("type", {}).get("name", "Unknown"),
                minute=event.get("minute", 0),
                second=event.get("second", 0),
                period=event.get("period", 1),
                timestamp_seconds=_parse_timestamp(event.get("timestamp", "00:00:00.000")),
                ball_x=round(ball_x, 3),
                ball_y=round(ball_y, 3),
                players=players,
                player_count=len(players),
                scores=scores,
                cover_shadows=shadows,
                pressure_grid=pressure_grid,
                is_collapse_frame=False,  # filled by collapse.detect_collapse
                score_delta=0.0,          # filled by collapse.detect_collapse
            )
        )

    # Annotate collapse frame
    collapse.detect_collapse(frames)
    collapse_idx = collapse.collapse_frame_index(frames)

    response = GoalSequenceResponse(
        match_id=match_id,
        goal_event_id=goal_event_id,
        defending_team_id=defending_team_id,
        defending_team_name=defending_team_name,
        attacking_team_id=attacking_team_id,
        attacking_team_name=attacking_team_name,
        collapse_frame_index=collapse_idx,
        frames=frames,
    )

    cache.set_sequence(match_id, goal_event_id, response)
    return response
