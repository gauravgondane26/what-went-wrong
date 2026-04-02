"""
Tests for coordinate normalization.

Key invariant: after normalization, mean(defender.x) < mean(attacker.x)
for every frame in any valid goal sequence. If this breaks, the flip logic is wrong.
"""
import pytest

from app.services.normalizer import detect_attack_direction, normalize_frame


def _make_freeze_frame(
    attackers: list[tuple[float, float]],
    defenders: list[tuple[float, float]],
    actor_is_attacker: bool = True,
) -> list[dict]:
    """Build a synthetic freeze frame. teammate=True means same team as actor."""
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


# Scenario: attacking team attacks toward x=120 (no flip needed)
# Defenders near x=10–30, attackers near x=80–110, ball at x=85
def test_no_flip_attacker_actor():
    """Attacker performs the event; attack is toward x=120."""
    attacking_team_id = 1
    defending_team_id = 2

    # Event actor is the attacker (team_id=1)
    event = {
        "team": {"id": attacking_team_id},
        "location": [85.0, 40.0],
        "type": {"name": "Carry"},
    }

    defenders_raw = [(10.0, 30.0), (15.0, 45.0), (20.0, 55.0), (25.0, 40.0)]
    attackers_raw = [(80.0, 35.0), (90.0, 50.0), (105.0, 40.0)]
    freeze_frame = _make_freeze_frame(attackers_raw, defenders_raw, actor_is_attacker=True)

    ball_x, ball_y, players = normalize_frame(event, freeze_frame, defending_team_id, True)

    assert ball_x == pytest.approx(85.0)
    assert ball_y == pytest.approx(40.0)

    atk_players = [p for p in players if p.is_attacker]
    def_players = [p for p in players if not p.is_attacker and not p.keeper]

    assert len(atk_players) == 3
    assert len(def_players) == 4

    mean_atk_x = sum(p.x for p in atk_players) / len(atk_players)
    mean_def_x = sum(p.x for p in def_players) / len(def_players)

    # Invariant: defenders closer to x=0 (their goal)
    assert mean_def_x < mean_atk_x, (
        f"Invariant violated: mean defender x ({mean_def_x:.1f}) >= mean attacker x ({mean_atk_x:.1f})"
    )


# Scenario: attacking team attacks toward x=0 (flip needed)
# Raw coords: defenders near x=90–110 (their goal is at x=120), ball at x=35
def test_flip_when_attacking_toward_x0():
    """Attack direction is toward x=0; coordinates must be flipped."""
    attacking_team_id = 1
    defending_team_id = 2

    event = {
        "team": {"id": attacking_team_id},
        "location": [35.0, 40.0],  # shot from x=35, attacking toward x=0
        "type": {"name": "Shot"},
    }

    # Raw coords (before flip): defenders near x=90–110, attackers near x=20–40
    defenders_raw = [(90.0, 30.0), (95.0, 45.0), (100.0, 55.0), (105.0, 40.0)]
    attackers_raw = [(20.0, 35.0), (30.0, 50.0), (35.0, 40.0)]
    freeze_frame = _make_freeze_frame(attackers_raw, defenders_raw, actor_is_attacker=True)

    ball_x, ball_y, players = normalize_frame(event, freeze_frame, defending_team_id, False)

    # Ball at x=35 → flipped to x=120-35=85
    assert ball_x == pytest.approx(85.0)

    atk_players = [p for p in players if p.is_attacker]
    def_players = [p for p in players if not p.is_attacker and not p.keeper]

    mean_atk_x = sum(p.x for p in atk_players) / len(atk_players)
    mean_def_x = sum(p.x for p in def_players) / len(def_players)

    assert mean_def_x < mean_atk_x, (
        f"Invariant violated after flip: mean defender x ({mean_def_x:.1f}) >= mean attacker x ({mean_atk_x:.1f})"
    )


def test_defender_actor_no_flip():
    """Defender performs the event (e.g., Pressure); attack is toward x=120."""
    attacking_team_id = 1
    defending_team_id = 2

    # Event actor is the DEFENDER (team_id=2)
    event = {
        "team": {"id": defending_team_id},
        "location": [70.0, 40.0],
        "type": {"name": "Pressure"},
    }

    # In this event's freeze frame, teammate=True means SAME TEAM as actor = DEFENDERS
    defenders_raw = [(15.0, 30.0), (20.0, 45.0), (25.0, 55.0), (70.0, 40.0)]
    attackers_raw = [(80.0, 35.0), (90.0, 50.0), (110.0, 40.0)]
    freeze_frame = _make_freeze_frame(
        defenders_raw, attackers_raw, actor_is_attacker=False
    )  # actor is defender, so "attackers" in _make_freeze_frame are passed as second arg

    ball_x, ball_y, players = normalize_frame(event, freeze_frame, defending_team_id, True)

    atk_players = [p for p in players if p.is_attacker]
    def_players = [p for p in players if not p.is_attacker and not p.keeper]

    assert len(atk_players) == 3
    assert len(def_players) == 4

    mean_atk_x = sum(p.x for p in atk_players) / len(atk_players)
    mean_def_x = sum(p.x for p in def_players) / len(def_players)

    assert mean_def_x < mean_atk_x


def test_detect_attack_direction_toward_120():
    event = {"location": [95.0, 40.0]}
    assert detect_attack_direction(event) is True


def test_detect_attack_direction_toward_0():
    event = {"location": [25.0, 40.0]}
    assert detect_attack_direction(event) is False


def test_empty_freeze_frame():
    """No players → ball position still normalizes correctly."""
    event = {"team": {"id": 1}, "location": [80.0, 40.0], "type": {"name": "Shot"}}
    ball_x, ball_y, players = normalize_frame(event, [], defending_team_id=2, attacking_toward_120=True)
    assert ball_x == pytest.approx(80.0)
    assert ball_y == pytest.approx(40.0)
    assert players == []
