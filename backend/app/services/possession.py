"""
Extracts the possession sequence leading to a goal event.

StatsBomb possession model:
- `possession` is a monotonically increasing integer; all events with the same
  value belong to one sequence.
- `possession_team` identifies which team holds the ball for that sequence.
- We use `possession_team.id` (NOT `team.id`) so that own goals are handled
  correctly — for an own goal, `team.id` is the team that benefited, but
  `possession_team.id` is the team that played the ball into their own net.
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


def find_goal_events(events: list[dict]) -> list[dict]:
    """
    Returns all shot events where the outcome is a goal.
    Includes own goals (type.name == "Own Goal Against") as a separate entry.
    """
    goals = []
    for e in events:
        type_name = e.get("type", {}).get("name", "")
        if type_name == "Shot":
            outcome = (e.get("shot") or {}).get("outcome", {}).get("name", "")
            if outcome == "Goal":
                goals.append(e)
        elif type_name == "Own Goal Against":
            goals.append(e)
    goals.sort(key=lambda e: e["index"])
    return goals


def sequence_length_for_goal(events: list[dict], goal_event: dict) -> int:
    return len(extract_goal_possession_sequence(events, goal_event))
