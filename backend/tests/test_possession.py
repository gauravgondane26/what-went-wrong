"""Tests for possession sequence extraction."""
import pytest

from app.services.possession import (
    extract_goal_possession_sequence,
    find_goal_events,
    goal_teams,
    is_penalty_goal,
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


def test_own_goal_sequence_is_its_possession():
    """Own goal: the sequence is the possession the own goal happened in."""
    events = [
        _event(1, "og", 5, TEAM_A, "Team A", TEAM_B, "Own Goal Against"),
    ]
    goal_event = events[0]
    seq = extract_goal_possession_sequence(events, goal_event)
    assert len(seq) == 1
    assert seq[0]["id"] == "og"


def _two_team_events(goal: dict) -> list[dict]:
    return [
        {**_event(1, "a", 1, TEAM_A, "Team A", TEAM_A), "team": {"id": TEAM_A, "name": "Team A"}},
        {**_event(2, "b", 2, TEAM_B, "Team B", TEAM_B), "team": {"id": TEAM_B, "name": "Team B"}},
        goal,
    ]


def test_goal_teams_own_goal_benefiting_team_had_possession():
    """Own Goal Against is the conceding team's event; the other team scores."""
    og = {**_event(3, "og", 3, TEAM_A, "Team A", TEAM_B, "Own Goal Against"),
          "team": {"id": TEAM_B, "name": "Team B"}}
    scoring, conceding = goal_teams(_two_team_events(og), og)
    assert (scoring["id"], conceding["id"]) == (TEAM_A, TEAM_B)


def test_goal_teams_own_goal_conceding_team_had_possession():
    """Real case: Croatia v Spain, EURO 2020 19' — Pedri's back-pass own goal
    during Spain's possession. Croatia scores; possession_team is Spain."""
    og = {**_event(3, "og", 3, TEAM_B, "Team B", TEAM_B, "Own Goal Against"),
          "team": {"id": TEAM_B, "name": "Team B"}}
    scoring, conceding = goal_teams(_two_team_events(og), og)
    assert (scoring["id"], conceding["id"]) == (TEAM_A, TEAM_B)
    assert scoring["name"] == "Team A"


def test_goal_teams_shot_uses_team_not_possession_team():
    """A goal straight after winning the ball keeps the conceding team's
    possession number — the scorer is the shot's team."""
    shot = {**_event(3, "g", 3, TEAM_B, "Team B", TEAM_A, "Shot", "Goal"),
            "team": {"id": TEAM_A, "name": "Team A"}}
    scoring, conceding = goal_teams(_two_team_events(shot), shot)
    assert (scoring["id"], conceding["id"]) == (TEAM_A, TEAM_B)


def test_sequence_sorted_by_index():
    """Ensure results are sorted by event index even if input is out of order."""
    events = _make_match_events()
    events_shuffled = list(reversed(events))
    goal_event = next(e for e in events_shuffled if e["id"] == "goal")
    seq = extract_goal_possession_sequence(events_shuffled, goal_event)
    indices = [e["index"] for e in seq]
    assert indices == sorted(indices)


def test_find_goal_events_excludes_saved_shot():
    events = [
        _event(1, "saved", 1, TEAM_A, "Team A", TEAM_A, "Shot", "Saved"),
        _event(2, "goal", 2, TEAM_A, "Team A", TEAM_A, "Shot", "Goal"),
    ]
    goals = find_goal_events(events)
    assert len(goals) == 1
    assert goals[0]["id"] == "goal"


def test_find_goal_events_sorted_by_index():
    # Feed events out of order; result must be sorted ascending by index
    events = [
        _event(5, "g2", 2, TEAM_A, "Team A", TEAM_A, "Shot", "Goal"),
        _event(2, "g1", 1, TEAM_A, "Team A", TEAM_A, "Shot", "Goal"),
    ]
    goals = find_goal_events(events)
    assert goals[0]["id"] == "g1"
    assert goals[1]["id"] == "g2"


def test_find_goal_events_excludes_shootout_kicks():
    """Penalty-shootout kicks (period 5) have no build-up and are not listed."""
    in_game = _event(1, "g", 1, TEAM_A, "Team A", TEAM_A, "Shot", "Goal")
    shootout = _event(2, "so", 2, TEAM_A, "Team A", TEAM_A, "Shot", "Goal")
    shootout["period"] = 5
    assert [g["id"] for g in find_goal_events([in_game, shootout])] == ["g"]


def test_is_penalty_goal_uses_shot_type():
    """In-game penalties are flagged by shot.type, not by period."""
    pen = _event(1, "pen", 1, TEAM_A, "Team A", TEAM_A, "Shot", "Goal")
    pen["period"] = 1
    pen["shot"]["type"] = {"name": "Penalty"}
    open_play = _event(2, "op", 2, TEAM_A, "Team A", TEAM_A, "Shot", "Goal")
    open_play["shot"]["type"] = {"name": "Open Play"}
    assert is_penalty_goal(pen) is True
    assert is_penalty_goal(open_play) is False
    assert is_penalty_goal(_event(3, "og", 3, TEAM_A, "Team A", TEAM_B, "Own Goal Against")) is False


def test_extract_sequence_when_goal_is_first_event():
    """Goal is the first (and only) event of the possession — sequence length is 1."""
    events = [
        _event(1, "goal", 5, TEAM_A, "Team A", TEAM_A, "Shot", "Goal"),
        _event(2, "e2", 6, TEAM_B, "Team B", TEAM_B, "Pass"),
    ]
    goal_event = events[0]
    seq = extract_goal_possession_sequence(events, goal_event)
    assert len(seq) == 1
    assert seq[0]["id"] == "goal"
