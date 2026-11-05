"""Tests for event_action and normalize_point (end locations share the ball's flip)."""
from __future__ import annotations

import pytest

from app.services.actions import event_action
from app.services.normalizer import normalize_frame, normalize_point

DEF = 1  # defending team id
ATT = 2


def _event(kind: str, team: int, detail: dict | None = None, **extra) -> dict:
    e = {"id": "e1", "type": {"name": kind}, "team": {"id": team}, "location": [50.0, 30.0], **extra}
    if detail is not None:
        e[kind.lower()] = detail
    return e


def test_normalize_point_flips_for_attacking_actor():
    assert normalize_point(_event("Pass", ATT), DEF, 100.0, 20.0) == (20.0, 60.0)


def test_normalize_point_keeps_defending_actor():
    assert normalize_point(_event("Pass", DEF), DEF, 100.0, 20.0) == (100.0, 20.0)


def test_normalize_point_clamps():
    assert normalize_point(_event("Pass", DEF), DEF, 121.5, -0.4) == (120.0, 0.0)


@pytest.mark.parametrize("team", [ATT, DEF])
def test_end_point_uses_same_flip_as_ball(team: int):
    """A pass's end location must land where the ball would if it were the location."""
    e = _event("Pass", team, {"end_location": [90.0, 12.0]})
    ball_x, ball_y, _ = normalize_frame({**e, "location": [90.0, 12.0]}, [], DEF)
    action = event_action(e, DEF)
    assert (action.end_x, action.end_y) == (ball_x, ball_y)


def test_cross_pass_flags():
    e = _event(
        "Pass", ATT,
        {"end_location": [114.0, 40.0], "cross": True, "height": {"name": "High Pass"}},
        under_pressure=True,
    )
    a = event_action(e, DEF)
    assert a.kind == "Pass"
    assert (a.end_x, a.end_y) == (6.0, 40.0)  # flipped: near the defended goal
    assert a.cross and a.under_pressure
    assert a.height == "High Pass"
    assert not (a.through_ball or a.cut_back or a.switch)
    assert a.set_piece is None


@pytest.mark.parametrize(
    "detail",
    [{"through_ball": True}, {"technique": {"name": "Through Ball"}}],
)
def test_through_ball_either_encoding(detail: dict):
    a = event_action(_event("Pass", ATT, {"end_location": [100.0, 40.0], **detail}), DEF)
    assert a.through_ball


@pytest.mark.parametrize(
    "pass_type, expected",
    [("Corner", "Corner"), ("Throw-in", "Throw-in"), ("Recovery", None), ("Interception", None)],
)
def test_set_piece_only_for_restarts(pass_type: str, expected: str | None):
    e = _event("Pass", ATT, {"end_location": [100.0, 40.0], "type": {"name": pass_type}})
    assert event_action(e, DEF).set_piece == expected


def test_shot_end_location_ignores_height():
    a = event_action(_event("Shot", ATT, {"end_location": [120.0, 38.0, 1.2]}), DEF)
    assert (a.kind, a.end_x, a.end_y) == ("Shot", 0.0, 42.0)


def test_carry_and_dribble():
    carry = event_action(_event("Carry", ATT, {"end_location": [70.0, 30.0]}), DEF)
    assert (carry.end_x, carry.end_y) == (50.0, 50.0)
    dribble = event_action(_event("Dribble", ATT, {"outcome": {"name": "Complete"}}), DEF)
    assert dribble.kind == "Dribble" and dribble.end_x is None


@pytest.mark.parametrize("kind", ["Pressure", "Ball Receipt*", "Duel", "Clearance", "Goal Keeper"])
def test_non_ball_moving_events_have_no_action(kind: str):
    assert event_action(_event(kind, DEF), DEF) is None
