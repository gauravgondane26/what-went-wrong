"""Tests for defensive shape scoring."""
import pytest

from app.models.frame import PlayerPosition
from app.services.scorer import (
    GRID_COLS,
    GRID_ROWS,
    MARK_RADIUS,
    MAX_SHADOW_RANGE,
    _is_shadowed,
    box_marking,
    in_box,
    compute_composite,
    compute_pressure_grid,
    score_compactness,
    score_cover_shadows,
    score_frame,
    score_goal_side,
    score_line_height,
    shadow_targets,
)


def test_compactness_tight_unit():
    defenders = [(10.0, 38.0), (10.0, 42.0), (12.0, 38.0), (12.0, 42.0)]
    score = score_compactness(defenders, (11.0, 40.0))
    assert score > 0.99  # near-zero area → near 1.0


def test_compactness_spread_unit():
    defenders = [(5.0, 10.0), (5.0, 70.0), (45.0, 10.0), (45.0, 70.0)]
    score = score_compactness(defenders, (25.0, 40.0))
    assert score < 0.2  # wide spread → low compactness


def test_compactness_single_player():
    assert score_compactness([(30.0, 40.0)], (30.0, 40.0)) == 1.0


def test_compactness_empty():
    assert score_compactness([], (30.0, 40.0)) == 1.0


def test_line_height_deep():
    defenders = [(5.0, 40.0), (8.0, 30.0), (10.0, 50.0), (12.0, 40.0), (40.0, 40.0)]
    height = score_line_height(defenders)
    # deepest 4: x=5,8,10,12 → mean=8.75
    assert height == pytest.approx(8.75)


def test_line_height_high():
    defenders = [(45.0, 40.0), (48.0, 30.0), (50.0, 50.0), (52.0, 40.0)]
    height = score_line_height(defenders)
    assert height == pytest.approx(48.75)


def test_line_height_empty():
    assert score_line_height([]) == 0.0


def test_is_shadowed_blocked():
    # Defender sits directly between ball and attacker
    ball = (60.0, 40.0)
    attacker = (110.0, 40.0)
    defender = (80.0, 40.0)  # on the ray, at t=0.4
    assert _is_shadowed(ball, defender, attacker) is True


def test_is_shadowed_outside_range():
    # Defender is BEHIND the ball (t < 0)
    ball = (60.0, 40.0)
    attacker = (110.0, 40.0)
    defender = (40.0, 40.0)
    assert _is_shadowed(ball, defender, attacker) is False


def test_is_shadowed_too_far_side():
    # Defender is far off to the side
    ball = (60.0, 40.0)
    attacker = (110.0, 40.0)
    defender = (80.0, 70.0)  # way off to the side
    assert _is_shadowed(ball, defender, attacker) is False


def test_cover_shadows_full_coverage():
    ball = (60.0, 40.0)
    attackers = [(100.0, 40.0)]
    defenders = [(80.0, 40.0)]  # directly in front of attacker
    coverage, shadows = score_cover_shadows(defenders, attackers, ball)
    assert coverage == 1.0
    assert len(shadows) == 1


def test_cover_shadows_no_coverage():
    ball = (60.0, 40.0)
    attackers = [(100.0, 40.0)]
    defenders = [(10.0, 10.0)]  # nowhere near the lane
    coverage, shadows = score_cover_shadows(defenders, attackers, ball)
    assert coverage == 0.0
    assert len(shadows) == 0


def test_cover_shadows_no_targets_means_no_open_lane():
    coverage, shadows = score_cover_shadows([(30.0, 40.0)], [], (60.0, 40.0))
    assert coverage == 1.0
    assert shadows == []


def test_pressure_grid_dimensions():
    defenders = [(30.0, 40.0), (35.0, 35.0)]
    grid = compute_pressure_grid(defenders)
    assert len(grid) == GRID_COLS * GRID_ROWS  # 384


def test_pressure_grid_fixed_scale():
    """C4: one defender alone doesn't saturate; values compare across frames."""
    one = compute_pressure_grid([(62.5, 42.5)])
    assert max(one) == pytest.approx(0.5, abs=0.01)
    many = compute_pressure_grid([(62.5, 42.5)] * 3)
    assert max(many) == 1.0
    assert min(many) >= 0.0


def test_pressure_grid_empty():
    grid = compute_pressure_grid([])
    assert len(grid) == GRID_COLS * GRID_ROWS
    assert all(v == 0.0 for v in grid)


def test_line_height_more_than_four_defenders():
    """With 6 defenders, only the 4 with the lowest x are used."""
    defenders = [(5.0, 20.0), (8.0, 40.0), (12.0, 60.0), (15.0, 40.0), (50.0, 30.0), (70.0, 45.0)]
    result = score_line_height(defenders)
    assert result == pytest.approx((5.0 + 8.0 + 12.0 + 15.0) / 4)


def test_line_height_three_defenders():
    """With fewer than 4 defenders, all are used."""
    defenders = [(10.0, 30.0), (20.0, 40.0), (30.0, 50.0)]
    result = score_line_height(defenders)
    assert result == pytest.approx((10.0 + 20.0 + 30.0) / 3)


def test_is_shadowed_attacker_at_ball_position():
    """Attacker coincident with ball: ray_len < 0.1 → not shadowed."""
    ball = (60.0, 40.0)
    defender = (55.0, 40.0)
    attacker = (60.0, 40.0)
    assert _is_shadowed(ball, defender, attacker) is False


def test_is_shadowed_beyond_max_range():
    """Defender beyond MAX_SHADOW_RANGE is never shadowing, even on a perfect ray."""
    ball = (0.0, 40.0)
    attacker = (100.0, 40.0)
    # Defender exactly on the ray, but beyond MAX_SHADOW_RANGE from ball
    defender_far = (MAX_SHADOW_RANGE + 1.0, 40.0)
    assert _is_shadowed(ball, defender_far, attacker) is False
    # Same geometry but within range → should shadow
    defender_near = (MAX_SHADOW_RANGE - 1.0, 40.0)
    assert _is_shadowed(ball, defender_near, attacker) is True


def test_compactness_all_same_location():
    assert score_compactness([(60.0, 40.0)] * 5, (60.0, 40.0)) == pytest.approx(1.0)


def test_compactness_ignores_far_defenders():
    """C2: extra defenders the camera catches far from the ball don't change the score."""
    ball = (25.0, 40.0)
    block = [(20.0, 30.0), (20.0, 50.0), (30.0, 30.0), (30.0, 50.0), (25.0, 40.0), (22.0, 36.0)]
    wider = block + [(22.0, 5.0), (22.0, 75.0), (60.0, 40.0)]
    assert score_compactness(block, ball) == score_compactness(wider, ball)


def test_compactness_uses_unit_nearest_ball():
    ball = (30.0, 40.0)
    tight_near_ball = [(30.0 + dx, 40.0 + dy) for dx, dy in [(0, 0), (2, 0), (0, 2), (2, 2), (1, 1), (-1, -1)]]
    far_scattered = [(90.0, 5.0), (100.0, 75.0)]
    assert score_compactness(tight_near_ball + far_scattered, ball) == 1.0


def test_goal_side_share():
    defenders = [(10.0, 40.0), (20.0, 40.0), (50.0, 40.0), (70.0, 40.0)]
    assert score_goal_side(defenders, 30.0) == pytest.approx(0.5)
    assert score_goal_side(defenders, 100.0) == pytest.approx(1.0)
    assert score_goal_side([], 30.0) == 0.0


def test_composite_perfect_shape():
    assert compute_composite(1.0, 1.0, 1.0) == pytest.approx(1.0)


def test_composite_broken_shape():
    assert compute_composite(0.0, 0.0, 0.0) == pytest.approx(0.0)


def test_composite_weights():
    assert compute_composite(1.0, 0.0, 0.0) == pytest.approx(0.4)
    assert compute_composite(0.0, 1.0, 0.0) == pytest.approx(0.3)
    assert compute_composite(0.0, 0.0, 1.0) == pytest.approx(0.3)


def _p(x, y, attacker=False, actor=False, keeper=False):
    return PlayerPosition(x=x, y=y, is_attacker=attacker, actor=actor, keeper=keeper)


def test_shadow_targets_exclude_carrier_and_keeper():
    """C3: carrier (actor or on the ball) and attacking keeper can't be cut off."""
    players = [
        _p(60.0, 40.0, attacker=True, actor=True),   # carrier
        _p(61.0, 40.5, attacker=True),               # on the ball, not flagged actor
        _p(115.0, 40.0, attacker=True, keeper=True),  # attacking keeper
        _p(40.0, 20.0, attacker=True),               # real target
        _p(30.0, 40.0),                              # defender
    ]
    assert shadow_targets(players, (60.0, 40.0)) == [(40.0, 20.0)]


def test_score_frame_unreliable_below_min_defenders():
    """C2: fewer than 6 outfield defenders → no composite."""
    players = [_p(5.0, 40.0, keeper=True)] + [_p(20.0 + i, 40.0) for i in range(5)]
    scores, _, _ = score_frame(players, 70.0, 40.0)
    assert scores.defenders_visible == 5
    assert scores.reliable is False
    assert scores.composite is None


def test_score_frame_reliable_composite():
    defenders = [_p(20.0 + 2 * i, 30.0 + 3 * i) for i in range(6)]
    players = defenders + [_p(5.0, 40.0, keeper=True), _p(60.0, 40.0, attacker=True, actor=True)]
    scores, _, _ = score_frame(players, 60.0, 40.0)
    assert scores.reliable is True
    assert scores.goal_side_share == 1.0
    assert scores.cover_shadow_coverage == 1.0  # only the carrier attacks
    assert scores.composite == pytest.approx(
        compute_composite(scores.compactness, 1.0, 1.0)
    )


# ---------------------------------------------------------------------------
# Box marking
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "x, y, inside",
    [(0.0, 40.0, True), (18.0, 18.0, True), (18.0, 62.0, True),
     (18.1, 40.0, False), (10.0, 17.9, False), (10.0, 62.1, False)],
)
def test_in_box_edges(x, y, inside):
    assert in_box(x, y) is inside


def test_box_marking_counts_only_free_attackers_in_box():
    players = [
        _p(6.0, 40.0, True),               # marked: defender 1.5 away
        _p(6.0, 41.5, False),
        _p(8.0, 30.0, True),               # unmarked: nearest defender 3 away
        _p(8.0, 33.0, False),
        _p(4.0, 50.0, True, actor=True),   # unmarked shooter counts
        _p(30.0, 40.0, True),              # outside the box: ignored
        _p(1.0, 40.0, True, keeper=True),  # attacking keeper never counts (sanity)
    ]
    assert box_marking(players) == (3, 2)


def test_keeper_marks_too():
    players = [_p(3.0, 40.0, True), _p(1.5, 40.5, False, keeper=True)]
    assert box_marking(players) == (1, 0)


def test_box_marking_exactly_at_radius_is_marked():
    players = [_p(10.0, 40.0, True), _p(10.0 + MARK_RADIUS, 40.0, False)]
    assert box_marking(players) == (1, 0)


def test_score_frame_reports_box_marking_without_touching_composite():
    defenders = [_p(5.0 + 2 * i, 20.0 + 6 * i, False) for i in range(6)]
    free_runner = _p(6.0, 60.0, True)
    base = score_frame(defenders, 25.0, 40.0)[0]
    scores = score_frame(defenders + [free_runner], 25.0, 40.0)[0]
    assert (scores.attackers_in_box, scores.unmarked_in_box) == (1, 1)
    assert (base.attackers_in_box, base.unmarked_in_box) == (0, 0)
    # The runner is a shadow target, so coverage may move, but compactness and
    # goal-side are untouched: box marking is not part of the composite formula.
    assert scores.compactness == base.compactness
    assert scores.goal_side_share == base.goal_side_share
