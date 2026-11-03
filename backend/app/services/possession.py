"""
Extracts the possession sequence leading to a goal event.

StatsBomb possession model:
- `possession` is a monotonically increasing integer; all events with the same
  value belong to one sequence.
- `possession_team` identifies which team holds the ball for that sequence.
- `possession_team` is NOT the scoring team in general: for an own goal it is
  usually the team that benefits, but not always (e.g. a back-pass into the
  own net), and a goal scored straight after winning the ball keeps the
  conceding team's possession. Use `goal_teams` to identify scorer/conceder.
"""
from __future__ import annotations


def extract_goal_possession_sequence(
    events: list[dict],
    goal_event: dict,
) -> list[dict]:
    """
    Returns the ordered list of events from the start of possession through
    the goal (inclusive).

    Includes the defending team's events inside the possession (Pressure,
    tackles, blocks, clearances, ...): they are the defensive actions the
    analysis is about. StatsBomb keeps one possession number while the
    defending team presses or briefly touches the ball.

    Trims trailing goalkeeper-recovery events that StatsBomb sometimes tags
    with the same possession number after the shot.
    """
    target_possession: int = goal_event["possession"]

    # possession_team is constant within a possession (0 of 19,998 possessions
    # in EURO 2020 + WC 2022 differ), so the possession number alone selects it.
    sequence = [e for e in events if e["possession"] == target_possession]
    sequence.sort(key=lambda e: e["index"])

    # Trim at the goal event (inclusive)
    goal_idx = next(
        (i for i, e in enumerate(sequence) if e["id"] == goal_event["id"]),
        len(sequence) - 1,
    )
    return sequence[: goal_idx + 1]


SHOOTOUT_PERIOD = 5


def find_goal_events(events: list[dict]) -> list[dict]:
    """
    Returns all shot events where the outcome is a goal.
    Includes own goals (type.name == "Own Goal Against") as a separate entry.
    Excludes penalty-shootout kicks (period 5): they have no build-up to analyse.
    """
    goals = []
    for e in events:
        if e.get("period") == SHOOTOUT_PERIOD:
            continue
        type_name = e.get("type", {}).get("name", "")
        if type_name == "Shot":
            outcome = (e.get("shot") or {}).get("outcome", {}).get("name", "")
            if outcome == "Goal":
                goals.append(e)
        elif type_name == "Own Goal Against":
            goals.append(e)
    goals.sort(key=lambda e: e["index"])
    return goals


def frame_events(sequence: list[dict], frames360: dict[str, list]) -> list[dict]:
    """Events of the sequence that become frames: every event with a non-empty
    360 freeze frame, in sequence order.

    Ball Receipt* events are included. They used to be skipped on the belief
    that they re-use the preceding pass's freeze frame and appear rotated 180°;
    in EURO 2020 data none is a copy of its pass frame, and the ~7% that are
    stored rotated are handled by the normalizer like any other event.
    """
    return [e for e in sequence if frames360.get(e["id"])]


def goal_teams(events: list[dict], goal_event: dict) -> tuple[dict, dict]:
    """Return (scoring_team, conceding_team) as {"id", "name"} dicts.

    - Shot: the scorer is `team` (not `possession_team` — a goal straight
      after winning the ball keeps the conceding team's possession number;
      5 of 300 non-shootout goals in EURO 2020 + WC 2022).
    - Own Goal Against: `team` is the side that put it in its own net, so the
      scoring team is the other one.
    """
    teams: dict[int, str] = {}
    for e in events:
        t = e.get("team") or {}
        if t.get("id") is not None:
            teams[t["id"]] = t.get("name", "Unknown")

    actor = goal_event["team"]["id"]
    other = next((tid for tid in teams if tid != actor), actor)
    if goal_event.get("type", {}).get("name") == "Own Goal Against":
        scoring_id, conceding_id = other, actor
    else:
        scoring_id, conceding_id = actor, other
    return (
        {"id": scoring_id, "name": teams.get(scoring_id, "Unknown")},
        {"id": conceding_id, "name": teams.get(conceding_id, "Unknown")},
    )


def is_penalty_goal(goal_event: dict) -> bool:
    """True for an in-game penalty kick (shot.type == "Penalty")."""
    return ((goal_event.get("shot") or {}).get("type") or {}).get("name") == "Penalty"


def sequence_length_for_goal(events: list[dict], goal_event: dict) -> int:
    return len(extract_goal_possession_sequence(events, goal_event))
