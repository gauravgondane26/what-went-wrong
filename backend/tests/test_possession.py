"""Tests for possession sequence extraction."""
import pytest

from app.services.possession import (
    extract_goal_possession_sequence,
    find_goal_events,
    sequence_length_for_goal,
)


def _event(
    idx: int,
    event_id: str,
    possession: int,
    possession_team_id: int,
    possession_team_name: str,
    team_id: int,
    type_name: str = "Pass",
    shot_outcome: str | None = None,
) -> dict:
    e: dict = {
        "id": event_id,
        "index": idx,
        "possession": possession,
        "possession_team": {"id": possession_team_id, "name": possession_team_name},
        "team": {"id": team_id, "name": "Team"},
        "type": {"name": type_name},
    }
    if shot_outcome:
        e["shot"] = {"outcome": {"name": shot_outcome}, "statsbomb_xg": 0.15}
    return e


TEAM_A = 1
TEAM_B = 2


def _make_match_events():
    """
    Possession 10: Team B has ball (3 events)
    Possession 11: Team A attacks, ends in goal (5 events)
    Possession 11 (continued): GK recovery event after goal (same possession number)
    """
    events = [
        _event(1, "e1", 10, TEAM_B, "Team B", TEAM_B, "Pass"),
        _event(2, "e2", 10, TEAM_B, "Team B", TEAM_B, "Carry"),
        _event(3, "e3", 10, TEAM_B, "Team B", TEAM_B, "Pass"),
        _event(4, "e4", 11, TEAM_A, "Team A", TEAM_A, "Ball Recovery"),
        _event(5, "e5", 11, TEAM_A, "Team A", TEAM_A, "Carry"),
        _event(6, "e6", 11, TEAM_A, "Team A", TEAM_A, "Pass"),
        _event(7, "e7", 11, TEAM_A, "Team A", TEAM_A, "Carry"),
        _event(8, "goal", 11, TEAM_A, "Team A", TEAM_A, "Shot", "Goal"),
        # GK recovery event after goal — same possession but different team
        _event(9, "e9", 11, TEAM_A, "Team A", TEAM_B, "Goal Keeper"),
    ]
    return events


def test_extracts_correct_sequence():
    events = _make_match_events()
    goal_event = next(e for e in events if e["id"] == "goal")
    seq = extract_goal_possession_sequence(events, goal_event)
    event_ids = [e["id"] for e in seq]

    assert event_ids == ["e4", "e5", "e6", "e7", "goal"]


def test_excludes_gk_recovery():
    events = _make_match_events()
    goal_event = next(e for e in events if e["id"] == "goal")
    seq = extract_goal_possession_sequence(events, goal_event)
    assert all(e["id"] != "e9" for e in seq)


def test_sequence_length():
    events = _make_match_events()
    goal_event = next(e for e in events if e["id"] == "goal")
    assert sequence_length_for_goal(events, goal_event) == 5


def test_find_goal_events_normal():
    events = _make_match_events()
    goals = find_goal_events(events)
    assert len(goals) == 1
    assert goals[0]["id"] == "goal"


def test_find_goal_events_no_goals():
    events = [_event(1, "e1", 1, TEAM_A, "Team A", TEAM_A, "Pass")]
    assert find_goal_events(events) == []


def test_own_goal_uses_possession_team():
    """Own goal: team.id is the beneficiary; possession_team.id is the scorer."""
    events = [
        _event(1, "og", 5, TEAM_A, "Team A", TEAM_B, "Own Goal Against"),
    ]
    goal_event = events[0]
    # possession_team is Team A (they played it in), even though team.id is Team B
    seq = extract_goal_possession_sequence(events, goal_event)
    assert len(seq) == 1
    assert seq[0]["id"] == "og"


def test_sequence_sorted_by_index():
    """Ensure results are sorted by event index even if input is out of order."""
    events = _make_match_events()
    events_shuffled = list(reversed(events))
    goal_event = next(e for e in events_shuffled if e["id"] == "goal")
    seq = extract_goal_possession_sequence(events_shuffled, goal_event)
    indices = [e["index"] for e in seq]
    assert indices == sorted(indices)
