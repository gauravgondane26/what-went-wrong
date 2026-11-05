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

# Compactness = mean distance from their centroid of the COMPACT_UNIT outfield
# defenders nearest the ball, mapped linearly so SPREAD_TIGHT (or less) → 1.0 and
# SPREAD_LOOSE (or more) → 0.0. Using a fixed-size unit makes the score almost
# independent of how many defenders the camera caught (C2): on EURO 2020 goals the
# median per-sequence correlation with visible-defender count is −0.03, versus
# +0.64 for the old bounding box. The range spans roughly p5–p95 of real frames.
COMPACT_UNIT = 6
SPREAD_TIGHT = 5.0
SPREAD_LOOSE = 15.0

# Below this many visible outfield defenders a frame says more about the camera
# than the shape: its composite is None and collapse detection skips it (C2).
MIN_RELIABLE_DEFENDERS = 6

# Attackers this close to the ball are the carrier: no lane to block (C3).
CARRIER_RADIUS = 2.0

# Composite weights
W_COMPACTNESS = 0.4
W_GOAL_SIDE = 0.3
W_SHADOW = 0.3

# Pressure grid dimensions
GRID_COLS = 24  # 5-unit cells across 120
GRID_ROWS = 16  # 5-unit cells across 80
SIGMA = 8.0  # Gaussian influence radius in pitch units
# Fixed pressure scale: a cell covered by this much summed Gaussian weight (two
# defenders on top of it) reads 1.0. Fixed, not per-frame, so frames compare
# and the heatmap fades when defenders leave an area (C4).
PRESSURE_SATURATION = 2.0

# Cover shadow max useful range — defenders beyond this distance can't meaningfully
# block a passing lane in real soccer (~36 metres). Prevents cross-pitch shadow
# cones when 360 freeze-frame player positions lag behind ball movement.
MAX_SHADOW_RANGE = 40.0

# Box marking: the composite reads a packed penalty area as "compact" even when
# runners are free, which is how crosses and set pieces beat it. An attacker in
# the defended penalty area with no defender (keeper included) within
# MARK_RADIUS is unmarked. On EURO 2020 goals the count jumps from ~0.6 on
# earlier frames to ~2.3 on the final frame of crossed goals while the
# composite stays ~0.57. Display and collapse detection only; not in composite.
BOX_DEPTH = 18.0
BOX_Y_MIN = 18.0
BOX_Y_MAX = 62.0
MARK_RADIUS = 2.0


def score_compactness(
    defenders: list[tuple[float, float]], ball: tuple[float, float]
) -> float:
    """
    How tightly grouped the defensive unit around the ball is, 0–1 (higher = tighter).

    Takes the COMPACT_UNIT defenders nearest the ball and uses their mean
    distance from their centroid. Returns 1.0 with fewer than 2 defenders
    (such frames are flagged unreliable anyway).
    """
    if len(defenders) < 2:
        return 1.0
    bx, by = ball
    defenders = sorted(defenders, key=lambda p: math.hypot(p[0] - bx, p[1] - by))
    defenders = defenders[:COMPACT_UNIT]
    cx = sum(p[0] for p in defenders) / len(defenders)
    cy = sum(p[1] for p in defenders) / len(defenders)
    spread = sum(math.hypot(x - cx, y - cy) for x, y in defenders) / len(defenders)
    norm = (spread - SPREAD_TIGHT) / (SPREAD_LOOSE - SPREAD_TIGHT)
    return round(1.0 - min(max(norm, 0.0), 1.0), 4)


def score_goal_side(defenders: list[tuple[float, float]], ball_x: float) -> float:
    """
    Fraction of outfield defenders between the ball and their own goal (x < ball_x).

    Replaces absolute line height in the composite (C1): absolute depth rises
    naturally as play nears goal, whereas being goal-side of the ball is what a
    defence loses when it is broken.
    """
    if not defenders:
        return 0.0
    return round(sum(1 for x, _ in defenders if x < ball_x) / len(defenders), 4)


def score_line_height(defenders: list[tuple[float, float]]) -> float:
    """
    Average x-coordinate of the 4 deepest defenders (lowest x = closest to own goal).
    Lower values = deeper, safer defensive line.
    Returns raw x (0–120). Display only; not part of the composite (C1).
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
    coverage_fraction: 0–1, fraction of `attackers` with at least one cover shadow.
        `attackers` should already exclude the carrier and keeper (see
        `shadow_targets`). With no targets there is no open lane, so 1.0.
    shadows: list of CoverShadow cone geometries for rendering.
    """
    if not attackers:
        return 1.0, []

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


def shadow_targets(
    players: list[PlayerPosition], ball: tuple[float, float]
) -> list[tuple[float, float]]:
    """Attackers a defender could cut off: not the keeper, not the ball carrier (C3)."""
    bx, by = ball
    return [
        (p.x, p.y)
        for p in players
        if p.is_attacker
        and not p.keeper
        and not p.actor
        and math.hypot(p.x - bx, p.y - by) > CARRIER_RADIUS
    ]


def in_box(x: float, y: float) -> bool:
    return x <= BOX_DEPTH and BOX_Y_MIN <= y <= BOX_Y_MAX


def box_marking(players: list[PlayerPosition]) -> tuple[int, int]:
    """(attackers in the defended box, how many of them are unmarked).

    Outfield attackers only; the ball carrier counts (a free shooter is the
    point). Any visible defender, keeper included, within MARK_RADIUS marks.
    """
    markers = [(p.x, p.y) for p in players if not p.is_attacker]
    in_area = [p for p in players if p.is_attacker and not p.keeper and in_box(p.x, p.y)]
    unmarked = sum(
        all(math.hypot(p.x - mx, p.y - my) > MARK_RADIUS for mx, my in markers)
        for p in in_area
    )
    return len(in_area), unmarked


def compute_composite(
    compactness: float, goal_side: float, shadow_coverage: float
) -> float:
    return round(
        W_COMPACTNESS * compactness + W_GOAL_SIDE * goal_side + W_SHADOW * shadow_coverage,
        4,
    )


def compute_pressure_grid(
    defenders: list[tuple[float, float]],
) -> list[float]:
    """
    Returns a 384-element (GRID_COLS × GRID_ROWS) flat list (row-major) of
    defensive pressure intensity values in [0, 1].

    Each cell's value is the sum of Gaussian contributions from all defenders,
    divided by the fixed PRESSURE_SATURATION and clipped to 1.0.
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

    grid = np.minimum(grid / PRESSURE_SATURATION, 1.0)

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
    ball = (ball_x, ball_y)
    attackers = shadow_targets(players, ball)

    compactness = score_compactness(defenders, ball)
    line_height = score_line_height(defenders)
    goal_side = score_goal_side(defenders, ball_x)
    shadow_coverage, shadows = score_cover_shadows(defenders, attackers, ball)
    reliable = len(defenders) >= MIN_RELIABLE_DEFENDERS
    composite = (
        compute_composite(compactness, goal_side, shadow_coverage) if reliable else None
    )
    pressure_grid = compute_pressure_grid(defenders)
    attackers_in_box, unmarked_in_box = box_marking(players)

    scores = DefensiveScores(
        attackers_in_box=attackers_in_box,
        unmarked_in_box=unmarked_in_box,
        compactness=compactness,
        line_height=line_height,
        goal_side_share=goal_side,
        cover_shadow_coverage=shadow_coverage,
        composite=composite,
        defenders_visible=len(defenders),
        reliable=reliable,
    )
    return scores, shadows, pressure_grid
