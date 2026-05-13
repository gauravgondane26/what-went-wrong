"""
Tests for coordinate normalization.

StatsBomb 360 convention (confirmed against real open data): both `event.location`
(ball) and 360 freeze frame player positions are actor-relative — the event actor's
team ALWAYS attacks toward x=120 in that space.

This means consecutive events from different teams mirror each other:
  - Attacker event: do_flip=True  → flip to put defending goal (at x=120) at x=0
  - Defender event: do_flip=False → actor-relative already has defending goal at x=0

Key invariant after normalization: mean(defender.x) < mean(attacker.x)
"""
import pytest

from app.services.normalizer import normalize_frame


def _make_freeze_frame(
    attackers: list[tuple[float, float]],
    defenders: list[tuple[float, float]],
    actor_is_attacker: bool = True,
) -> list[dict]:
    """Build a synthetic freeze frame with actor-relative positions."""
    frame = []
    for x, y in attackers:
        frame.append(
            {
                "location": [x, y],
                "teammate": actor_is_attacker,
                "actor": False,
                "keeper": False,
            }
        )
    for x, y in defenders:
        frame.append(
            {
                "location": [x, y],
                "teammate": not actor_is_attacker,
                "actor": False,
                "keeper": False,
            }
        )
    return frame


# ---------------------------------------------------------------------------
# Attacker performs event; attacking toward x=120 (absolute).
# actor-relative == absolute in this case (both point the same direction).
# do_flip=True flips to put defending goal (at x=120 in actor-relative) at x=0.
# ---------------------------------------------------------------------------
def test_attacker_event_attacking_toward_120():
    """Attacker event, attack toward x=120: flip puts defending goal at x=0."""
    attacking_team_id = 1
    defending_team_id = 2

    event = {
        "team": {"id": attacking_team_id},
        "location": [85.0, 40.0],
        "type": {"name": "Carry"},
    }

    # Actor-relative (== absolute here): defenders near x=90–110, attackers at x=60–85.
    defenders_raw = [(90.0, 30.0), (95.0, 45.0), (100.0, 55.0), (110.0, 40.0)]
    attackers_raw = [(60.0, 35.0), (75.0, 50.0), (85.0, 40.0)]
    freeze_frame = _make_freeze_frame(attackers_raw, defenders_raw, actor_is_attacker=True)

    ball_x, ball_y, players = normalize_frame(event, freeze_frame, defending_team_id)

    # Ball flipped: 120 - 85 = 35
    assert ball_x == pytest.approx(35.0)
    assert ball_y == pytest.approx(40.0)

    atk_players = [p for p in players if p.is_attacker]
    def_players = [p for p in players if not p.is_attacker and not p.keeper]

    assert len(atk_players) == 3
    assert len(def_players) == 4

    mean_atk_x = sum(p.x for p in atk_players) / len(atk_players)
    mean_def_x = sum(p.x for p in def_players) / len(def_players)

    # After flip: defenders at x=10–30, attackers at x=35–60 → invariant holds
    assert mean_def_x < mean_atk_x, (
        f"Invariant violated: mean defender x ({mean_def_x:.1f}) >= mean attacker x ({mean_atk_x:.1f})"
    )


# ---------------------------------------------------------------------------
# Defender performs event; attacking team attacks toward x=120 (absolute).
# Defending team therefore attacks toward x=0 in absolute → their actor-relative
# space mirrors absolute (x_rel = 120 - x_abs, y_rel = 80 - y_abs).
# do_flip=False: actor-relative already has defending goal at x=0.
# ---------------------------------------------------------------------------
def test_defender_event_attacking_toward_120():
    """Defender event, attack toward x=120: actor-relative already normalized; no flip."""
    attacking_team_id = 1
    defending_team_id = 2

    # Ball actor-relative x=50 (absolute: 120-50=70); no flip → ball_x=50.
    event = {
        "team": {"id": defending_team_id},
        "location": [50.0, 40.0],
        "type": {"name": "Pressure"},
    }

    # Actor-relative for defending-team event (their space mirrors absolute):
    #   Absolute defenders x=90–110 → actor-relative (120-x, 80-y): x=10–30
    #   Absolute attackers x=60–85  → actor-relative (120-x, 80-y): x=35–60
    defenders_raw = [(30.0, 50.0), (25.0, 35.0), (20.0, 25.0), (10.0, 40.0)]
    attackers_raw = [(60.0, 45.0), (45.0, 30.0), (35.0, 40.0)]
    freeze_frame = _make_freeze_frame(attackers_raw, defenders_raw, actor_is_attacker=False)

    ball_x, ball_y, players = normalize_frame(event, freeze_frame, defending_team_id)

    # No flip: ball stays at actor-relative x=50.
    assert ball_x == pytest.approx(50.0)
    assert ball_y == pytest.approx(40.0)

    atk_players = [p for p in players if p.is_attacker]
    def_players = [p for p in players if not p.is_attacker and not p.keeper]

    assert len(atk_players) == 3
    assert len(def_players) == 4

    mean_atk_x = sum(p.x for p in atk_players) / len(atk_players)
    mean_def_x = sum(p.x for p in def_players) / len(def_players)

    # No flip: defenders at x=10–30, attackers at x=35–60 → invariant holds.
    assert mean_def_x < mean_atk_x, (
        f"Invariant violated: mean defender x ({mean_def_x:.1f}) >= mean attacker x ({mean_atk_x:.1f})"
    )


# ---------------------------------------------------------------------------
# Attacker performs event; attacking toward x=0 (absolute, second-half orientation).
# Actor-relative still has attacker toward x=120, so x_rel = 120 - x_abs.
# do_flip=True (always for attacker events): both flips cancel → normalized.
# ---------------------------------------------------------------------------
def test_attacker_event_attacking_toward_x0():
    """Attacker event, attack toward x=0 (reversed half): flip still applied correctly."""
    attacking_team_id = 1
    defending_team_id = 2

    # Absolute ball at x=35 (near defending goal at x=0).
    # Actor-relative (attacker always toward x=120): 120-35=85.
    event = {
        "team": {"id": attacking_team_id},
        "location": [85.0, 40.0],
        "type": {"name": "Shot"},
    }

    # Absolute: defenders x=5–20 (guarding goal at x=0), attackers x=25–40.
    # Actor-relative (120-x, 80-y): defenders x=100–115, attackers x=80–95.
    defenders_raw = [(115.0, 50.0), (110.0, 35.0), (105.0, 25.0), (100.0, 40.0)]
    attackers_raw = [(95.0, 45.0), (87.0, 30.0), (80.0, 40.0)]
    freeze_frame = _make_freeze_frame(attackers_raw, defenders_raw, actor_is_attacker=True)

    ball_x, ball_y, players = normalize_frame(event, freeze_frame, defending_team_id)

    # Ball flip applied (attacker event): 120-85=35.
    assert ball_x == pytest.approx(35.0)
    assert ball_y == pytest.approx(40.0)

    atk_players = [p for p in players if p.is_attacker]
    def_players = [p for p in players if not p.is_attacker and not p.keeper]

    assert len(atk_players) == 3
    assert len(def_players) == 4

    mean_atk_x = sum(p.x for p in atk_players) / len(atk_players)
    mean_def_x = sum(p.x for p in def_players) / len(def_players)

    # After flip: defenders at x=5–20, attackers at x=25–40 → invariant holds.
    assert mean_def_x < mean_atk_x, (
        f"Invariant violated: mean defender x ({mean_def_x:.1f}) >= mean attacker x ({mean_atk_x:.1f})"
    )


# ---------------------------------------------------------------------------
# Defender performs event; attacking toward x=0 (absolute).
# Defending team attacks toward x=120 in absolute → actor-relative == absolute.
# do_flip=False: absolute coords already have defending goal at x=0.
# ---------------------------------------------------------------------------
def test_defender_event_attacking_toward_x0():
    """Defender event, attack toward x=0: actor-relative == absolute; no flip needed."""
    attacking_team_id = 1
    defending_team_id = 2

    # Ball actor-relative x=50 (== absolute here); no flip → ball_x=50.
    event = {
        "team": {"id": defending_team_id},
        "location": [50.0, 40.0],
        "type": {"name": "Pressure"},
    }

    # Actor-relative == absolute (defending team attacks toward x=120 in absolute).
    defenders_raw = [(5.0, 30.0), (10.0, 45.0), (15.0, 55.0), (20.0, 40.0)]
    attackers_raw = [(25.0, 35.0), (33.0, 50.0), (40.0, 40.0)]
    freeze_frame = _make_freeze_frame(attackers_raw, defenders_raw, actor_is_attacker=False)

    ball_x, ball_y, players = normalize_frame(event, freeze_frame, defending_team_id)

    assert ball_x == pytest.approx(50.0)
    assert ball_y == pytest.approx(40.0)

    atk_players = [p for p in players if p.is_attacker]
    def_players = [p for p in players if not p.is_attacker and not p.keeper]

    assert len(atk_players) == 3
    assert len(def_players) == 4

    mean_atk_x = sum(p.x for p in atk_players) / len(atk_players)
    mean_def_x = sum(p.x for p in def_players) / len(def_players)
    assert mean_def_x < mean_atk_x, (
        f"Invariant violated: mean defender x ({mean_def_x:.1f}) >= mean attacker x ({mean_atk_x:.1f})"
    )


def test_empty_freeze_frame_attacker():
    """No players — attacker event ball is flipped (actor-relative → normalized)."""
    event = {"team": {"id": 1}, "location": [80.0, 40.0], "type": {"name": "Carry"}}
    ball_x, ball_y, players = normalize_frame(event, [], defending_team_id=2)
    assert ball_x == pytest.approx(40.0)  # 120 - 80
    assert ball_y == pytest.approx(40.0)  # 80 - 40
    assert players == []


def test_empty_freeze_frame_defender():
    """No players — defender event ball is NOT flipped (actor-relative already normalized)."""
    event = {"team": {"id": 2}, "location": [80.0, 40.0], "type": {"name": "Pressure"}}
    ball_x, ball_y, players = normalize_frame(event, [], defending_team_id=2)
    assert ball_x == pytest.approx(80.0)
    assert ball_y == pytest.approx(40.0)
    assert players == []


def test_defending_keeper_classified_correctly():
    """Defending GK (teammate=False in attacker event) gets is_attacker=False and keeper=True."""
    event = {"team": {"id": 1}, "location": [100.0, 40.0], "type": {"name": "Shot"}}
    freeze_frame = [
        {"location": [115.0, 40.0], "teammate": False, "actor": False, "keeper": True},
    ]
    _, _, players = normalize_frame(event, freeze_frame, defending_team_id=2)
    assert len(players) == 1
    gk = players[0]
    assert gk.keeper is True
    assert gk.is_attacker is False


def test_ball_coordinates_clamped():
    """Ball location outside pitch bounds is clamped to [0, 120] × [0, 80] after flip."""
    event = {"team": {"id": 1}, "location": [121.0, 85.0], "type": {"name": "Carry"}}
    # Attacker event: do_flip=True → 120-121=-1 → 0; 80-85=-5 → 0
    ball_x, ball_y, _ = normalize_frame(event, [], defending_team_id=2)
    assert ball_x == pytest.approx(0.0)
    assert ball_y == pytest.approx(0.0)


def test_actor_flag_preserved():
    """actor=True on a freeze-frame player survives normalization unchanged."""
    event = {"team": {"id": 1}, "location": [80.0, 40.0], "type": {"name": "Carry"}}
    freeze_frame = [
        {"location": [80.0, 40.0], "teammate": True, "actor": True, "keeper": False},
        {"location": [90.0, 35.0], "teammate": False, "actor": False, "keeper": False},
    ]
    _, _, players = normalize_frame(event, freeze_frame, defending_team_id=2)
    actor_players = [p for p in players if p.actor]
    non_actor_players = [p for p in players if not p.actor]
    assert len(actor_players) == 1
    assert len(non_actor_players) == 1


def test_player_at_center_unaffected_by_flip():
    """Player at (60, 40) maps to (60, 40) after flip: 120-60=60, 80-40=40."""
    event = {"team": {"id": 1}, "location": [80.0, 40.0], "type": {"name": "Carry"}}
    freeze_frame = [{"location": [60.0, 40.0], "teammate": False, "actor": False, "keeper": False}]
    _, _, players = normalize_frame(event, freeze_frame, defending_team_id=2)
    assert players[0].x == pytest.approx(60.0)
    assert players[0].y == pytest.approx(40.0)
