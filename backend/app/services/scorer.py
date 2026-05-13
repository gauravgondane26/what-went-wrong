"""
Defensive shape scoring for a single frame.

All coordinates are post-normalization: defending goal at x=0, attacking toward x=120.
"""
from __future__ import annotations

import math

import numpy as np

from app.models.frame import CoverShadow, DefensiveScores, PlayerPosition

# Pitch dimensions
PITCH_LENGTH = 120.0
PITCH_WIDTH = 80.0

# Max bounding box area for a fully spread defensive unit (~40 wide × 60 deep)
MAX_DEFENSIVE_AREA = 2400.0

# Max x value for last-line normalization (defender at x=60 = midfield)
MAX_LINE_HEIGHT = 60.0

# Composite weights
W_COMPACTNESS = 0.4
W_LINE_HEIGHT = 0.3
W_SHADOW = 0.3

# Pressure grid dimensions
GRID_COLS = 24  # 5-unit cells across 120
GRID_ROWS = 16  # 5-unit cells across 80
SIGMA = 8.0  # Gaussian influence radius in pitch units

# Cover shadow max useful range — defenders beyond this distance can't meaningfully
# block a passing lane in real soccer (~36 metres). Prevents cross-pitch shadow
# cones when 360 freeze-frame player positions lag behind ball movement.
MAX_SHADOW_RANGE = 40.0


def score_compactness(defenders: list[tuple[float, float]]) -> float:
    """
    1 - normalized bounding-box area of the defensive unit.
    Returns 1.0 if defenders are perfectly stacked, 0.0 if fully spread.
    """
    if len(defenders) < 2:
        return 1.0
    xs = [p[0] for p in defenders]
    ys = [p[1] for p in defenders]
    area = (max(xs) - min(xs)) * (max(ys) - min(ys))
    return round(1.0 - min(area / MAX_DEFENSIVE_AREA, 1.0), 4)


def score_line_height(defenders: list[tuple[float, float]]) -> float:
    """
    Average x-coordinate of the 4 deepest defenders (lowest x = closest to own goal).
    Lower values = deeper, safer defensive line.
    Returns raw x (0–120); callers should interpret relative to PITCH_LENGTH.
    """
    if not defenders:
        return 0.0
    sorted_by_depth = sorted(defenders, key=lambda p: p[0])
    last_four = sorted_by_depth[: min(4, len(sorted_by_depth))]
    return round(sum(p[0] for p in last_four) / len(last_four), 2)


def _is_shadowed(
    ball: tuple[float, float],
    defender: tuple[float, float],
    attacker: tuple[float, float],
    width_factor: float = 0.15,
) -> bool:
    """
    Returns True if `defender` blocks the passing lane from `ball` to `attacker`.

    Algorithm: project defender onto the ball→attacker ray; check that
    the defender lies between them (0.05 < t < 0.95) and is within the
    shadow width of the ray.
    """
    bx, by = ball
    dx, dy = defender
    ax, ay = attacker

    def_dist = math.hypot(dx - bx, dy - by)
    if def_dist > MAX_SHADOW_RANGE:
        return False

    ray_len = math.hypot(ax - bx, ay - by)
    if ray_len < 0.1:
        return False

    # Scalar projection of defender onto ball→attacker ray (normalised 0–1)
    t = ((dx - bx) * (ax - bx) + (dy - by) * (ay - by)) / (ray_len ** 2)
    if not (0.05 < t < 0.95):
        return False

    # Perpendicular distance from defender to the ray
    perp_dist = abs((dx - bx) * (ay - by) - (dy - by) * (ax - bx)) / ray_len

    shadow_width = max(1.5, def_dist * width_factor)

    return perp_dist < shadow_width


def _build_shadow_cone(
    ball: tuple[float, float],
    defender: tuple[float, float],
    cone_half_angle_deg: float = 8.0,
) -> CoverShadow:
    bx, by = ball
    dx, dy = defender
    angle = math.atan2(dy - by, dx - bx)
    half_rad = math.radians(cone_half_angle_deg)
    tip_dist = math.hypot(dx - bx, dy - by)
    ext = tip_dist + 25.0

    return CoverShadow(
        origin_x=round(bx, 3),
        origin_y=round(by, 3),
        left_x=round(bx + ext * math.cos(angle - half_rad), 3),
        left_y=round(by + ext * math.sin(angle - half_rad), 3),
        right_x=round(bx + ext * math.cos(angle + half_rad), 3),
        right_y=round(by + ext * math.sin(angle + half_rad), 3),
    )


def score_cover_shadows(
    defenders: list[tuple[float, float]],
    attackers: list[tuple[float, float]],
    ball: tuple[float, float],
) -> tuple[float, list[CoverShadow]]:
    """
    Returns (coverage_fraction, shadows).
    coverage_fraction: 0–1, fraction of attackers with at least one cover shadow.
    shadows: list of CoverShadow cone geometries for rendering.
    """
    if not attackers:
        return 0.0, []

    blocked = 0
    shadows: list[CoverShadow] = []

    for atk in attackers:
        for defn in defenders:
            if _is_shadowed(ball, defn, atk):
                blocked += 1
                shadows.append(_build_shadow_cone(ball, defn))
                break  # one defender per attacker is enough

    coverage = round(blocked / len(attackers), 4)
    return coverage, shadows


def compute_composite(
    compactness: float, line_height: float, shadow_coverage: float
) -> float:
    line_norm = max(0.0, 1.0 - line_height / MAX_LINE_HEIGHT)
    return round(
        W_COMPACTNESS * compactness + W_LINE_HEIGHT * line_norm + W_SHADOW * shadow_coverage,
        4,
    )


def compute_pressure_grid(
    defenders: list[tuple[float, float]],
) -> list[float]:
    """
    Returns a 384-element (GRID_COLS × GRID_ROWS) flat list (row-major) of
    defensive pressure intensity values in [0, 1].

    Each cell's value is the sum of Gaussian contributions from all defenders,
    normalised so the maximum cell is 1.0.
    """
    cell_w = PITCH_LENGTH / GRID_COLS  # 5.0
    cell_h = PITCH_WIDTH / GRID_ROWS   # 5.0

    cx = np.array([(j + 0.5) * cell_w for j in range(GRID_COLS)])
    cy = np.array([(i + 0.5) * cell_h for i in range(GRID_ROWS)])
    XX, YY = np.meshgrid(cx, cy)  # shape (GRID_ROWS, GRID_COLS)

    grid = np.zeros((GRID_ROWS, GRID_COLS), dtype=np.float64)

    for dx, dy in defenders:
        dist_sq = (XX - dx) ** 2 + (YY - dy) ** 2
        grid += np.exp(-dist_sq / (2.0 * SIGMA ** 2))

    max_val = grid.max()
    if max_val > 0:
        grid = grid / max_val

    return [round(float(v), 4) for v in grid.flatten()]


def score_frame(
    players: list[PlayerPosition],
    ball_x: float,
    ball_y: float,
) -> tuple[DefensiveScores, list[CoverShadow], list[float]]:
    """
    Compute all scores for one frame.

    Returns (DefensiveScores, cover_shadows, pressure_grid).
    """
    defenders = [(p.x, p.y) for p in players if not p.is_attacker and not p.keeper]
    attackers = [(p.x, p.y) for p in players if p.is_attacker]
    ball = (ball_x, ball_y)

    compactness = score_compactness(defenders)
    line_height = score_line_height(defenders)
    shadow_coverage, shadows = score_cover_shadows(defenders, attackers, ball)
    composite = compute_composite(compactness, line_height, shadow_coverage)
    pressure_grid = compute_pressure_grid(defenders)

    scores = DefensiveScores(
        compactness=compactness,
        line_height=line_height,
        cover_shadow_coverage=shadow_coverage,
        composite=composite,
    )
    return scores, shadows, pressure_grid
