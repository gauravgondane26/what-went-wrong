"""
Build a GoalSequenceResponse from already-loaded match data.

Pipeline:
  find goal event → extract possession sequence
  → for each event with a 360 frame: normalize coords + score → FrameData
  → detect collapse frame → GoalSequenceResponse

Pure with respect to I/O: callers load events / 360 data (and cache the
result). This lets the sequence route, match/team reports and the offline
eval script share one implementation.
"""
from __future__ import annotations

from app.models.frame import FrameData, GoalSequenceResponse
from app.services import collapse, normalizer, possession, scorer


class GoalNotFoundError(LookupError):
    """The goal event id is not in this match's events."""


class No360DataError(LookupError):
    """No event in the goal's possession sequence has a 360 freeze frame."""


NO_360_DETAIL = (
    "No 360 freeze-frame data is available for this match. "
    "The match is listed in StatsBomb metadata with 360 coverage "
    "but the data file has not been published to the open-data repository."
)


def parse_timestamp(ts: str) -> float:
    """Convert "HH:MM:SS.mmm" to total seconds."""
    try:
        parts = ts.split(":")
        h, m, s = int(parts[0]), int(parts[1]), float(parts[2])
        return h * 3600 + m * 60 + s
    except Exception:
        return 0.0


def find_goal_event(events: list[dict], goal_event_id: str) -> dict:
    goal_event = next((e for e in events if e["id"] == goal_event_id), None)
    if goal_event is None:
        raise GoalNotFoundError(f"Goal event {goal_event_id} not found")
    return goal_event


def build_goal_sequence(
    match_id: int,
    events: list[dict],
    frames360: dict,
    goal_event: dict,
) -> GoalSequenceResponse:
    """Score every distinct 360 frame in the goal's possession and mark the collapse."""
    # Identify teams: attacking = the team the goal counts for
    scoring, conceding = possession.goal_teams(events, goal_event)
    defending_team_id: int = conceding["id"]

    sequence = possession.extract_goal_possession_sequence(events, goal_event)
    events_with_360 = possession.frame_events(sequence, frames360)
    if not events_with_360:
        raise No360DataError(NO_360_DETAIL)

    events_by_id = {e["id"]: e for e in events}
    frames: list[FrameData] = []

    for event in events_with_360:
        event_id = event["id"]
        freeze_frame = frames360[event_id]

        copied_labels = normalizer.copied_labels_hint(
            event, freeze_frame, events_by_id, frames360
        )
        ball_x, ball_y, players = normalizer.normalize_frame(
            event, freeze_frame, defending_team_id, copied_labels
        )

        # Consecutive events often carry the same snapshot (a Carry repeats the
        # Ball Receipt* before it); keep only the first so every frame is new.
        if frames and normalizer.same_snapshot(frames[-1].players, players):
            continue

        scores, shadows, pressure_grid = scorer.score_frame(players, ball_x, ball_y)

        frames.append(
            FrameData(
                frame_index=len(frames),
                event_id=event_id,
                event_type=event.get("type", {}).get("name", "Unknown"),
                minute=event.get("minute", 0),
                second=event.get("second", 0),
                period=event.get("period", 1),
                timestamp_seconds=parse_timestamp(event.get("timestamp", "00:00:00.000")),
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

    collapse.detect_collapse(frames)

    return GoalSequenceResponse(
        match_id=match_id,
        goal_event_id=goal_event["id"],
        defending_team_id=defending_team_id,
        defending_team_name=conceding["name"],
        attacking_team_id=scoring["id"],
        attacking_team_name=scoring["name"],
        collapse_frame_index=collapse.collapse_frame_index(frames),
        frames=frames,
    )
