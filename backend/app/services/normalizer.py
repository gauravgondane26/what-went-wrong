"""
Coordinate normalization for StatsBomb events.

StatsBomb contract: every event's `location` (and its 360 freeze frame
coordinates) are given from the EVENT ACTOR'S TEAM's perspective — that team
always attacks toward x=120, defends toward x=0.

When consecutive events alternate teams (e.g., a defender Pressure event
immediately after an attacker Carry), the coordinate system mirrors. Without
normalization, defenders appear on the attacking half every other frame.

Our target: the DEFENDING team's goal is always at x=0.

Flip formula:  x' = 120 - x,  y' = 80 - y

When to flip:
  - event actor IS the attacking team  → their goal is at x=0 in this frame's
    coordinates, so defenders appear near x=0 ONLY in THEIR attack direction.
    Wait — let's be precise:
      * event actor's team attacks toward x=120
      * teammates (teammate=True in freeze frame) = attacker's teammates = ATTACKERS
      * opponents (teammate=False) = DEFENDERS
      * defenders appear near low x values already in this frame ✓ NO FLIP NEEDED

  - event actor IS the defending team  → their goal is at x=0, they attack x=120,
    but the defending team's goal for THIS analysis is also x=0, so still correct.

  Wait, actually the correct analysis is simpler:

  `needs_flip = (event actor's team id) != (defending_team_id)`

  If the event actor is the ATTACKER (not the defending team):
    * In SB coordinates, attacker's goal is at x=0, they attack toward x=120
    * teammate=True → attacker  (near x=120 side → high x)
    * teammate=False → defender (near x=0 side → low x) ✓ correct already
    → needs_flip = False

  If the event actor is the DEFENDER (the defending team):
    * In SB coordinates, defender's goal is at x=0, they attack toward x=120
    * teammate=True → defender  (near x=0 side → low x) ... BUT teammate=True
      means SAME TEAM as event actor = DEFENDERS
    * teammate=False → attacker (near x=120 side → high x)
    * So defenders are at low x but labeled teammate=True — is_attacker must flip
    * AND the coordinate orientation has defenders near x=0 ✓ — no position flip
    → needs_flip = True for the teammate→is_attacker mapping, but NOT for coords?

  Actually re-reading StatsBomb docs more carefully:
  The coordinate system is NOT flipped per-event in open data.
  Each MATCH has a fixed coordinate orientation. In the first half one team
  attacks toward x=120 and in the second half they switch (standard football).
  The `location` coordinates are absolute pitch coordinates, not actor-relative.

  HOWEVER: the `teammate` flag in 360 freeze frames IS relative to the event actor.
  teammate=True = same team as the player who performed this event.

  So the only normalization needed is:
  1. Determine which direction the defending team attacks in each period.
  2. If in this period, the defending team attacks toward x=120 (i.e., they
     defend toward x=0), no positional flip needed.
  3. If in this period, the defending team attacks toward x=0 (i.e., they
     defend toward x=120), flip all coordinates.
  4. Map teammate flag → is_attacker relative to the defending team.

  Determining attack direction: StatsBomb doesn't explicitly say which team
  attacks which way per half. We infer it from the event data:
    - Find a Shot event by the home team in period 1.
    - If shot location x > 60, home team attacks toward x=120 in period 1.
    - Teams swap at half time.

  For simplicity in this tool, we use a heuristic:
    - Look at the ball carrier's location in the first event of the sequence.
    - The attacking team (possessing team) should be moving toward the opponent's goal.
    - If their average carry/pass end_x > start_x, they attack toward x=120.
    - Otherwise, they attack toward x=0 → flip everything.

  Practical approach used here:
  We detect attack direction from the goal event itself: the shot that resulted
  in the goal. The shot location should be inside the attacking half (x > 60
  if attacking toward x=120, or x < 60 if toward x=0). We use this to set the
  flip flag for the entire sequence.
"""
from __future__ import annotations

import math

from app.models.frame import CoverShadow, PlayerPosition


def detect_attack_direction(goal_event: dict) -> bool:
    """
    Returns True if the attacking team attacks toward x=120 (no flip needed).
    Returns False if they attack toward x=0 (flip needed).

    Uses the shot location: if x > 60, they're shooting from the right half
    toward x=120 goal. If x < 60, they attack toward x=0.
    """
    loc = goal_event.get("location")
    if not loc:
        return True  # default: no flip
    return loc[0] > 60.0


def normalize_frame(
    event: dict,
    freeze_frame: list[dict],
    defending_team_id: int,
    attacking_toward_120: bool,
) -> tuple[float, float, list[PlayerPosition]]:
    """
    Normalize a single event frame so the defending team's goal is at x=0.

    Args:
        event: raw StatsBomb event dict
        freeze_frame: list of player dicts from 360 data (teammate, location, keeper, actor)
        defending_team_id: team ID of the defending (conceding) team
        attacking_toward_120: True if attacking team attacks toward x=120

    Returns:
        (ball_x, ball_y, players)
    """
    needs_flip = attacking_toward_120

    def flip(x: float, y: float) -> tuple[float, float]:
        if needs_flip:
            return 120.0 - x, 80.0 - y
        return x, y

    def clamp(x: float, y: float) -> tuple[float, float]:
        return max(0.0, min(120.0, x)), max(0.0, min(80.0, y))

    loc = event.get("location") or [60.0, 40.0]
    ball_x, ball_y = clamp(*flip(loc[0], loc[1]))

    event_actor_team_id = event.get("team", {}).get("id")
    # actor_is_defender: the player performing this event is on the defending team
    actor_is_defender = event_actor_team_id == defending_team_id

    players: list[PlayerPosition] = []
    for p in freeze_frame:
        px, py = clamp(*flip(*p["location"]))

        # `teammate` means same team as the EVENT ACTOR (not the ball carrier's team).
        teammate: bool = p.get("teammate", False)

        # is_attacker truth table:
        #   actor_is_defender=False (actor is attacker), teammate=True  → attacker ✓
        #   actor_is_defender=False (actor is attacker), teammate=False → defender ✓
        #   actor_is_defender=True  (actor is defender), teammate=True  → defender ✓
        #   actor_is_defender=True  (actor is defender), teammate=False → attacker ✓
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

    return ball_x, ball_y, players
