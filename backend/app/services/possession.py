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

    Trims trailing goalkeeper-recovery events that StatsBomb sometimes tags
    with the same possession number after the shot.
    """
    target_possession: int = goal_event["possession"]
    attacking_team_id: int = goal_event["possession_team"]["id"]

    sequence = [
        e
        for e in events
        if e["possession"] == target_possession
        and e["possession_team"]["id"] == attacking_team_id
    ]
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
