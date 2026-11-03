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


# ---------------------------------------------------------------------------
# Freeze frames stored in the opponent's coordinate system.
#
# For "losing side" events (Dribbled Past, Dispossessed, Foul Won, and some
# Duels/Dribbles) StatsBomb stores player POSITIONS rotated 180° into the
# opponent's frame, while the `teammate` flag stays relative to the actor.
# Verified on EURO 2020 / WC 2022 360 data: on 131/132 Dribbled Past frames the
# actor's own keeper (teammate=True) sits at x≈118 and the actor stands at the
# rotated ball position.
# ---------------------------------------------------------------------------
def _dribbled_past_frame() -> tuple[dict, list[dict]]:
    """Defender (team 2) is dribbled past at (30, 50) in normalized space.

    event.location is actor-relative (defender frame: own goal at x=0) → (30, 50).
    Player positions are stored in the ATTACKER's frame (rotated): the defender
    actor sits at (90, 30) and the defending keeper (teammate=True) at (118, 40).
    """
    event = {"team": {"id": 2}, "location": [30.0, 50.0], "type": {"name": "Dribbled Past"}}
    freeze_frame = [
        {"location": [90.0, 30.0], "teammate": True, "actor": True, "keeper": False},    # defender actor
        {"location": [118.0, 40.0], "teammate": True, "actor": False, "keeper": True},   # defending keeper
        {"location": [100.0, 45.0], "teammate": True, "actor": False, "keeper": False},  # defender
        {"location": [88.0, 32.0], "teammate": False, "actor": False, "keeper": False},  # attacker (dribbler)
        {"location": [80.0, 50.0], "teammate": False, "actor": False, "keeper": False},  # attacker
    ]
    return event, freeze_frame


def test_rotated_freeze_frame_keeps_team_labels():
    """Positions are rotated back, but team labels must NOT be inverted."""
    event, freeze_frame = _dribbled_past_frame()
    _, _, players = normalize_frame(event, freeze_frame, defending_team_id=2)

    by_loc = {(round(p.x), round(p.y)): p for p in players}
    actor = next(p for p in players if p.actor)
    keeper = next(p for p in players if p.keeper)

    # Actor (a defender) is back at the ball and still labelled a defender
    assert (round(actor.x), round(actor.y)) == (30, 50)
    assert actor.is_attacker is False
    # Defending keeper is in its own goal at x≈2 and still a defender
    assert keeper.x < 10
    assert keeper.is_attacker is False
    # The two attackers stay attackers
    assert by_loc[(32, 48)].is_attacker is True
    assert by_loc[(40, 30)].is_attacker is True


# ---------------------------------------------------------------------------
# Orientation decision (A2). Paired events share one freeze frame; for the
# other team's event, POSITIONS and TEAMMATE LABELS can each be in the
# opponent's frame. Positions: decided by the actor standing on the rotated
# ball. Labels: decided by visible keepers, else by how the frame was shared
# (copied_labels), else by event type.
# In these tests team 1 attacks, team 2 defends; truth is given in normalized
# space (defending goal at x=0).
# ---------------------------------------------------------------------------
def _aerial_lost_copy_of_shot(with_keeper: bool) -> tuple[dict, list[dict]]:
    """Real case: England v Iran (WC 2022) 34'. Iran's Aerial Lost carries a
    verbatim copy of England's Shot frame — positions in England's frame and
    teammate flags relative to England (the 'actor' flag marks the shooter)."""
    event = {"team": {"id": 2}, "location": [8.1, 42.1], "type": {"name": "Duel"}}
    freeze_frame = [
        {"location": [112.0, 38.0], "teammate": True, "actor": True, "keeper": False},     # England shooter
        {"location": [110.0, 45.0], "teammate": False, "actor": False, "keeper": False},   # Iran defender
    ]
    if with_keeper:
        freeze_frame.append(
            {"location": [116.86, 40.51], "teammate": False, "actor": False, "keeper": True}  # Iran keeper
        )
    return event, freeze_frame


@pytest.mark.parametrize("with_keeper", [True, False])
def test_verbatim_copy_rotates_positions_and_labels(with_keeper):
    event, freeze_frame = _aerial_lost_copy_of_shot(with_keeper)
    ball_x, ball_y, players = normalize_frame(
        event, freeze_frame, defending_team_id=2, copied_labels=True
    )
    shooter = next(p for p in players if p.actor)
    defender = next(p for p in players if not p.actor and not p.keeper)
    assert (ball_x, ball_y) == pytest.approx((8.1, 42.1))
    assert (shooter.x, shooter.y) == pytest.approx((8.0, 42.0))
    assert shooter.is_attacker is True
    assert (defender.x, defender.y) == pytest.approx((10.0, 35.0))
    assert defender.is_attacker is False
    if with_keeper:
        keeper = next(p for p in players if p.keeper)
        assert keeper.x == pytest.approx(3.14)
        assert keeper.is_attacker is False


def test_keeper_decides_labels_over_copy_hint():
    """A visible keeper outranks the sharing hint when they disagree."""
    event, freeze_frame = _aerial_lost_copy_of_shot(with_keeper=True)
    _, _, players = normalize_frame(event, freeze_frame, defending_team_id=2, copied_labels=False)
    keeper = next(p for p in players if p.keeper)
    assert keeper.is_attacker is False
    assert next(p for p in players if p.actor).is_attacker is True


def test_rotated_own_frame_defaults_to_opponent_labels():
    """Not a shared frame, no keeper: a rotated frame carries the opponent's labels too.
    (Ball Receipt* frames with the actor on the rotated ball: continuity with the
    related Pass says players rotated 963 vs 90; keepers say labels inverted 543 vs 17.)"""
    event = {"team": {"id": 1}, "location": [80.0, 50.0], "type": {"name": "Ball Receipt*"}}  # → (40, 30)
    freeze_frame = [
        {"location": [40.0, 30.0], "teammate": False, "actor": True, "keeper": False},   # receiver (team 1)
        {"location": [35.0, 35.0], "teammate": True, "actor": False, "keeper": False},   # team 2 defender
    ]
    ball_x, ball_y, players = normalize_frame(event, freeze_frame, defending_team_id=2)
    receiver = next(p for p in players if p.actor)
    defender = next(p for p in players if not p.actor)
    assert (ball_x, ball_y) == pytest.approx((40.0, 30.0))
    assert (receiver.x, receiver.y) == pytest.approx((40.0, 30.0))
    assert receiver.is_attacker is True
    assert (defender.x, defender.y) == pytest.approx((35.0, 35.0))
    assert defender.is_attacker is False


def test_opponent_frame_type_rotated_without_actor_or_keeper():
    """Dribbled Past is rotated by event type even when no actor/keeper is visible."""
    event = {"team": {"id": 2}, "location": [30.0, 50.0], "type": {"name": "Dribbled Past"}}
    freeze_frame = [
        {"location": [100.0, 45.0], "teammate": True, "actor": False, "keeper": False},   # defender → (20, 35)
        {"location": [80.0, 50.0], "teammate": False, "actor": False, "keeper": False},   # attacker → (40, 30)
    ]
    _, _, players = normalize_frame(event, freeze_frame, defending_team_id=2)
    defender = next(p for p in players if not p.is_attacker)
    attacker = next(p for p in players if p.is_attacker)
    assert (defender.x, defender.y) == pytest.approx((20.0, 35.0))
    assert (attacker.x, attacker.y) == pytest.approx((40.0, 30.0))


def test_relabelled_copy_rotates_positions_only():
    """No keeper, frame shared with re-labelled teammate flags: rotate positions, keep labels."""
    event = {"team": {"id": 1}, "location": [80.0, 50.0], "type": {"name": "Duel"}}  # → ball (40, 30)
    freeze_frame = [
        {"location": [40.0, 30.0], "teammate": True, "actor": True, "keeper": False},   # stored rotated
        {"location": [35.0, 35.0], "teammate": False, "actor": False, "keeper": False},
    ]
    ball_x, ball_y, players = normalize_frame(
        event, freeze_frame, defending_team_id=2, copied_labels=False
    )
    actor = next(p for p in players if p.actor)
    other = next(p for p in players if not p.actor)
    assert (ball_x, ball_y) == pytest.approx((40.0, 30.0))
    assert (actor.x, actor.y) == pytest.approx((40.0, 30.0))
    assert actor.is_attacker is True
    assert (other.x, other.y) == pytest.approx((35.0, 35.0))
    assert other.is_attacker is False


def test_far_actor_rotates_positions_even_off_the_rotated_ball():
    """Actor > 30 from the ball but not exactly on the rotated ball: still rotate.
    Requiring the actor to stand on the rotated ball raised consecutive-frame
    orientation errors from 556 to 915 on the 20-match sample."""
    event = {"team": {"id": 1}, "location": [80.0, 40.0], "type": {"name": "Pass"}}  # → ball (40, 40)
    freeze_frame = [{"location": [60.0, 75.0], "teammate": True, "actor": True, "keeper": False}]  # → (60, 5)
    ball_x, ball_y, players = normalize_frame(
        event, freeze_frame, defending_team_id=2, copied_labels=False
    )
    assert (ball_x, ball_y) == pytest.approx((40.0, 40.0))
    assert (players[0].x, players[0].y) == pytest.approx((60.0, 75.0))
    assert players[0].is_attacker is True


# ---------------------------------------------------------------------------
# copied_labels_hint: detect a frame shared with a related other-team event.
# ---------------------------------------------------------------------------
from app.services.normalizer import copied_labels_hint  # noqa: E402


def _pair(teammate_flags_copied: bool, shift: float = 0.0):
    shot = {"id": "s", "team": {"id": 1}, "related_events": ["d"]}
    duel = {"id": "d", "team": {"id": 2}, "related_events": ["s"]}
    shot_ff = [
        {"location": [112.0, 38.0], "teammate": True, "actor": True, "keeper": False},
        {"location": [116.85514372, 40.509134], "teammate": False, "actor": False, "keeper": True},
    ]
    duel_ff = [
        {**p,
         "location": [p["location"][0] + shift, p["location"][1] + 1e-7],
         "teammate": p["teammate"] if teammate_flags_copied else not p["teammate"]}
        for p in shot_ff
    ]
    return duel, duel_ff, {"s": shot, "d": duel}, {"s": shot_ff, "d": duel_ff}


def test_hint_verbatim_copy():
    duel, ff, by_id, frames = _pair(teammate_flags_copied=True)
    assert copied_labels_hint(duel, ff, by_id, frames) is True


def test_hint_relabelled_copy():
    duel, ff, by_id, frames = _pair(teammate_flags_copied=False)
    assert copied_labels_hint(duel, ff, by_id, frames) is False


def test_hint_not_a_copy():
    duel, ff, by_id, frames = _pair(teammate_flags_copied=True, shift=2.0)
    assert copied_labels_hint(duel, ff, by_id, frames) is None


def test_hint_ignores_same_team_copies():
    duel, ff, by_id, frames = _pair(teammate_flags_copied=True)
    by_id["s"]["team"]["id"] = 2
    assert copied_labels_hint(duel, ff, by_id, frames) is None
