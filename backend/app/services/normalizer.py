"""
Coordinate normalization for StatsBomb events.

StatsBomb 360 data convention (confirmed against real open data):
  Both `event.location` (ball position) and 360 freeze frame player positions
  are in the EVENT ACTOR'S TEAM's coordinate system — their team always attacks
  toward x=120 in that space.

  This means consecutive events from different teams mirror each other:
  a defender Pressure at absolute x=85 is stored as x=35 (120-85) because
  the defender's team attacks toward x=120 in their own frame.

  The `teammate` flag is also actor-relative: teammate=True = same team as the
  player who performed the event.

Our normalization target: defending team's goal is always at x=0.

Flip formula when needed:  x' = 120 - x,  y' = 80 - y

The same flip applies to BOTH ball and players — they share the same
actor-relative coordinate system:

  actor is attacker → flip (attacker's actor-relative → target orientation)
  actor is defender → no flip (defender's actor-relative already matches:
                      the two flips — actor-relative→absolute, absolute→target
                      — cancel out)
"""
from __future__ import annotations

import math

from app.models.frame import PlayerPosition


def normalize_frame(
    event: dict,
    freeze_frame: list[dict],
    defending_team_id: int,
) -> tuple[float, float, list[PlayerPosition]]:
    """
    Normalize a single event frame so the defending team's goal is at x=0.

    Both event.location and freeze frame positions are actor-relative, so they
    receive identical flip treatment based solely on who performed the event.

    Returns (ball_x, ball_y, players).
    """
    event_actor_team_id = event.get("team", {}).get("id")
    actor_is_defender = event_actor_team_id == defending_team_id

    # Flip when actor is the attacker; no flip when actor is the defender.
    do_flip = not actor_is_defender

    def flip_coord(x: float, y: float) -> tuple[float, float]:
        if do_flip:
            return 120.0 - x, 80.0 - y
        return x, y

    def clamp(x: float, y: float) -> tuple[float, float]:
        return max(0.0, min(120.0, x)), max(0.0, min(80.0, y))

    loc = event.get("location") or [60.0, 40.0]
    ball_x, ball_y = clamp(*flip_coord(loc[0], loc[1]))

    players: list[PlayerPosition] = []
    for p in freeze_frame:
        px, py = clamp(*flip_coord(*p["location"]))

        teammate: bool = p.get("teammate", False)

        # is_attacker truth table:
        #   actor=attacker, teammate=True  → attacker ✓
        #   actor=attacker, teammate=False → defender ✓
        #   actor=defender, teammate=True  → defender ✓  (teammate flag inverted)
        #   actor=defender, teammate=False → attacker ✓
        is_attacker = teammate != actor_is_defender

        players.append(
            PlayerPosition(
                x=round(px, 3),
                y=round(py, 3),
                is_attacker=is_attacker,
                actor=p.get("actor", False),
                keeper=p.get("keeper", False),
            )
        )

    # Sanity check: the actor always performs the event at the ball's location,
    # so actor.x should be near ball_x. If the distance is large (>30 units),
    # the freeze frame was stored in the wrong actor-relative coordinate system
    # (e.g. Duel events where both players generate records but share the
    # opposing player's freeze frame). Re-flip positions and invert team labels.
    actor = next((p for p in players if p.actor), None)
    if actor is not None and math.hypot(actor.x - ball_x, actor.y - ball_y) > 30.0:
        players = [
            PlayerPosition(
                x=round(120.0 - p.x, 3),
                y=round(80.0 - p.y, 3),
                is_attacker=not p.is_attacker,
                actor=p.actor,
                keeper=p.keeper,
            )
            for p in players
        ]

    return ball_x, ball_y, players
