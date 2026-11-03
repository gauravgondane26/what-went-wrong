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

Exception — shared freeze frames:
  Paired events (Dribble/Dribbled Past, Duel/Dispossessed, Foul Committed/Foul
  Won, Aerial Lost/Clearance or Shot, Own Goal Against/For, ...) share ONE
  freeze frame, stored in the coordinate system of one of the two teams. For the
  other team's event two things can be wrong, independently:
    - POSITIONS are in the opponent's frame (the actor stands on the rotated
      ball position), and
    - TEAMMATE labels are relative to the opponent — StatsBomb re-labels them
      for some pairs (Dribbled Past, Dispossessed, Foul Won) but copies them
      verbatim for others (Aerial Lost ↔ Clearance/Shot, Own Goal pairs).
  `normalize_frame` decides each separately (see `_positions_rotated` and
  `_labels_inverted`); `copied_labels_hint` tells it how the labels were shared.
"""
from __future__ import annotations

import math

from app.models.frame import PlayerPosition

_FAR_FROM_BALL = 30.0
_COPY_TOLERANCE = 0.01

# Positions for these types are (almost) always in the opponent's frame and the
# teammate labels are re-labelled for the actor (EURO 2020 / WC 2022 360 data:
# 95–99% of frames). Used when the actor is not visible / no keeper is visible.
_RELABELLED_OPPONENT_FRAME_TYPES = {"Dribbled Past", "Dispossessed", "Foul Won"}


def normalize_frame(
    event: dict,
    freeze_frame: list[dict],
    defending_team_id: int,
    copied_labels: bool | None = None,
) -> tuple[float, float, list[PlayerPosition]]:
    """
    Normalize a single event frame so the defending team's goal is at x=0.

    `copied_labels` (from `copied_labels_hint`) says how this freeze frame was
    shared with a related event of the other team: True = copied verbatim
    (labels relative to the other team), False = re-labelled for this event's
    actor, None = not a shared frame / unknown.

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

    rotated = _positions_rotated(event_type, players, ball_x, ball_y)
    if rotated:
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

    if _labels_inverted(event_type, players, rotated, copied_labels):
        players = [
            PlayerPosition(
                x=p.x,
                y=p.y,
                is_attacker=not p.is_attacker,
                actor=p.actor,
                keeper=p.keeper,
            )
            for p in players
        ]

    return ball_x, ball_y, players


def copied_labels_hint(
    event: dict,
    freeze_frame: list[dict],
    events_by_id: dict[str, dict],
    frames360: dict[str, list[dict]],
) -> bool | None:
    """How this freeze frame was shared with a related event of the other team.

    Returns True if it is a copy of that event's frame with the teammate flags
    copied verbatim (so they are relative to the other team), False if it is a
    copy with the flags re-labelled for this event's actor, and None if it is
    not a copy of any related other-team frame.
    """
    team_id = event.get("team", {}).get("id")
    for rel_id in event.get("related_events") or []:
        other = events_by_id.get(rel_id)
        other_frame = frames360.get(rel_id)
        if not other or not other_frame or other.get("team", {}).get("id") == team_id:
            continue
        pairs = _match_players(freeze_frame, other_frame)
        if pairs is None:
            continue
        same = sum(a.get("teammate", False) == b.get("teammate", False) for a, b in pairs)
        if same == len(pairs):
            return True
        if same == 0:
            return False
    return None


def _match_players(a: list[dict], b: list[dict]) -> list[tuple[dict, dict]] | None:
    """Pair up two freeze frames player-by-player if their positions coincide."""
    if not a or len(a) != len(b):
        return None
    pairs = []
    remaining = list(b)
    for p in a:
        q = next(
            (
                q for q in remaining
                if math.hypot(p["location"][0] - q["location"][0],
                              p["location"][1] - q["location"][1]) <= _COPY_TOLERANCE
            ),
            None,
        )
        if q is None:
            return None
        remaining.remove(q)
        pairs.append((p, q))
    return pairs


def _keeper_vote(players: list[PlayerPosition]) -> int:
    """+1 for each visible keeper in its own half, −1 for each in the wrong half.

    After normalization the defending keeper belongs near x=0 and the attacking
    keeper near x=120.
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
    """Are the freeze-frame positions in the opponent's coordinate system?

    The actor performs the event at the ball, so an actor more than 30 units
    away means the positions are rotated. It is the players, not the ball, that
    are off: checked by continuity against the related same-team frame
    (Ball Receipt* 963 vs 90 frames, Carry 80 vs 22). Requiring the actor to
    stand exactly on the rotated ball made consecutive-frame orientation errors
    worse (556 → 915), so any far actor counts.
    """
    actor = next((p for p in players if p.actor), None)
    if actor is None:
        return event_type in _RELABELLED_OPPONENT_FRAME_TYPES
    return math.hypot(actor.x - ball_x, actor.y - ball_y) > _FAR_FROM_BALL


def _labels_inverted(
    event_type: str,
    players: list[PlayerPosition],
    positions_rotated: bool,
    copied_labels: bool | None,
) -> bool:
    """Are the teammate labels relative to the opponent instead of the actor?

    Evidence, strongest first:
      1. Visible goalkeepers (with positions already settled, each team's
         keeper must be in its own half).
      2. How the frame was shared with the other team's event.
      3. Event types known to re-label (keep labels); otherwise a rotated frame
         carries the opponent's labels too.
    """
    vote = _keeper_vote(players)
    if vote != 0:
        return vote < 0
    if not positions_rotated:
        return False
    if copied_labels is not None:
        return copied_labels
    return event_type not in _RELABELLED_OPPONENT_FRAME_TYPES
