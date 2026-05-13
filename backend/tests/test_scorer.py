"""Tests for defensive shape scoring."""
import pytest

from app.models.frame import PlayerPosition
from app.services.scorer import (
    GRID_COLS,
    GRID_ROWS,
    MAX_SHADOW_RANGE,
    _is_shadowed,
    compute_composite,
    compute_pressure_grid,
    score_compactness,
    score_cover_shadows,
    score_frame,
    score_line_height,
)


def test_compactness_tight_unit():
    defenders = [(10.0, 38.0), (10.0, 42.0), (12.0, 38.0), (12.0, 42.0)]
    score = score_compactness(defenders)
    assert score > 0.99  # near-zero area → near 1.0


def test_compactness_spread_unit():
    defenders = [(5.0, 10.0), (5.0, 70.0), (45.0, 10.0), (45.0, 70.0)]
    score = score_compactness(defenders)
    assert score < 0.2  # wide bounding box → low compactness


def test_compactness_single_player():
    assert score_compactness([(30.0, 40.0)]) == 1.0


def test_compactness_empty():
    assert score_compactness([]) == 1.0


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


def test_cover_shadows_empty_attackers():
    coverage, shadows = score_cover_shadows([(30.0, 40.0)], [], (60.0, 40.0))
    assert coverage == 0.0
    assert shadows == []


def test_composite_perfect_shape():
    # compactness=1, line_height=0, shadow=1 → 0.4 + 0.3*(1-0/60) + 0.3 = 1.0
    score = compute_composite(1.0, 0.0, 1.0)
    assert score == pytest.approx(1.0)


def test_composite_broken_shape():
    # compactness=0, line_height=60, shadow=0 → 0 + 0.3*(0) + 0 = 0.0
    score = compute_composite(0.0, 60.0, 0.0)
    assert score == pytest.approx(0.0)


def test_pressure_grid_dimensions():
    defenders = [(30.0, 40.0), (35.0, 35.0)]
    grid = compute_pressure_grid(defenders)
    assert len(grid) == GRID_COLS * GRID_ROWS  # 384


def test_pressure_grid_normalized():
    defenders = [(60.0, 40.0)]
    grid = compute_pressure_grid(defenders)
    assert max(grid) == pytest.approx(1.0, abs=0.001)
    assert min(grid) >= 0.0


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


def test_compactness_all_same_location():
    """All defenders stacked at the same point: zero bounding-box area → compactness=1.0."""
    defenders = [(60.0, 40.0)] * 5
    assert score_compactness(defenders) == pytest.approx(1.0)


def test_compactness_exactly_two_defenders():
    """Bounding box area is computed correctly for exactly two defenders."""
    defenders = [(10.0, 20.0), (50.0, 60.0)]
    # area = (50-10) * (60-20) = 40 * 40 = 1600
    expected = round(1.0 - 1600 / 2400, 4)
    assert score_compactness(defenders) == pytest.approx(expected)


def test_composite_line_height_above_max():
    """line_height above MAX_LINE_HEIGHT (60) clamps line_norm to 0."""
    result = compute_composite(1.0, 80.0, 1.0)
    # line_norm = max(0, 1 - 80/60) = 0 → composite = 0.4*1 + 0.3*0 + 0.3*1 = 0.7
    assert result == pytest.approx(0.7)


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


def test_score_frame_keeper_excluded_from_defenders():
    """Goalkeeper is excluded from defender list; compactness and line_height see no defenders."""
    gk = PlayerPosition(x=5.0, y=40.0, is_attacker=False, actor=False, keeper=True)
    attacker = PlayerPosition(x=80.0, y=40.0, is_attacker=True, actor=False, keeper=False)
    scores, _, _ = score_frame([gk, attacker], 70.0, 40.0)
    assert scores.compactness == pytest.approx(1.0)   # < 2 outfield defenders
    assert scores.line_height == pytest.approx(0.0)   # no outfield defenders
