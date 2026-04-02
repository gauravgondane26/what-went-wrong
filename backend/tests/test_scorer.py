"""Tests for defensive shape scoring."""
import pytest

from app.services.scorer import (
    GRID_COLS,
    GRID_ROWS,
    _is_shadowed,
    compute_composite,
    compute_pressure_grid,
    score_compactness,
    score_cover_shadows,
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
