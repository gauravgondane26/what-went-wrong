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

    event_type = (event.get("type") or {}).get("name", "")

    # Some events store the freeze-frame POSITIONS in the opponent's coordinate
    # system. Only positions are rotated back — the `teammate` flag is still
    # relative to the actor, so the team labels above are already correct.
    if _positions_rotated(event_type, players, ball_x, ball_y):
        players = [
            PlayerPosition(
                x=round(120.0 - p.x, 3),
                y=round(80.0 - p.y, 3),
                is_attacker=p.is_attacker,
                actor=p.actor,
                keeper=p.keeper,
            )
            for p in players
        ]

    # Other events have correct positions but an `event.location` stored in
    # the opposite frame: the actor then stands on the rotated ball position.
    actor = next((p for p in players if p.actor), None)
    if actor is not None:
        far = math.hypot(actor.x - ball_x, actor.y - ball_y) > _FAR_FROM_BALL
        rot_x, rot_y = 120.0 - ball_x, 80.0 - ball_y
        if far and math.hypot(actor.x - rot_x, actor.y - rot_y) < _NEAR_ROTATED_BALL:
            ball_x, ball_y = rot_x, rot_y

    return ball_x, ball_y, players


# Freeze-frame positions for these event types are stored in the opponent's
# frame (EURO 2020 / WC 2022 360 data: 95–99% of Dribbled Past, Dispossessed and
# Foul Won frames have the actor standing on the rotated ball position).
_OPPONENT_FRAME_TYPES = {"Dribbled Past", "Dispossessed", "Foul Won"}

# For these types an actor far from the ball means the BALL location is in the
# opposite frame, not the players (goalkeepers confirm the players: 543 vs 17
# frames for Ball Receipt*, 26 vs 10 for Carry).
_BALL_LOCATION_SUSPECT_TYPES = {"Ball Receipt*", "Carry"}

_FAR_FROM_BALL = 30.0
_NEAR_ROTATED_BALL = 10.0


def _keeper_vote(players: list[PlayerPosition]) -> int:
    """+1 for each visible keeper in its own half, −1 for each in the wrong half.

    After normalization the defending keeper belongs near x=0 and the attacking
    keeper near x=120, so a negative vote means the positions are rotated.
    """
    vote = 0
    for p in players:
        if p.keeper:
            in_own_half = p.x > 60.0 if p.is_attacker else p.x < 60.0
            vote += 1 if in_own_half else -1
    return vote


def _positions_rotated(
    event_type: str,
    players: list[PlayerPosition],
    ball_x: float,
    ball_y: float,
) -> bool:
    """Decide whether freeze-frame positions are in the opponent's frame.

    Evidence, strongest first:
      1. Visible goalkeepers — they directly show which end each team defends.
      2. Event types known to always store opponent-frame positions.
      3. Actor far from the ball but standing on the rotated ball position
         (skipped for types where the ball location is the usual culprit).
    """
    vote = _keeper_vote(players)
    if vote != 0:
        return vote < 0

    if event_type in _OPPONENT_FRAME_TYPES:
        return True

    if event_type in _BALL_LOCATION_SUSPECT_TYPES:
        return False

    actor = next((p for p in players if p.actor), None)
    if actor is None:
        return False
    far = math.hypot(actor.x - ball_x, actor.y - ball_y) > _FAR_FROM_BALL
    near_rotated = math.hypot(actor.x - (120.0 - ball_x), actor.y - (80.0 - ball_y)) < _NEAR_ROTATED_BALL
    return far and near_rotated
