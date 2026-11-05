"""
What the actor did with the ball on each frame's event: kind, normalized end
location and the StatsBomb flags that matter for explaining a collapse (cross,
through ball, cut-back, switch, pass height, set piece, under pressure).
"""
from __future__ import annotations

from app.models.frame import FrameAction
from app.services.normalizer import normalize_point

# Event types whose actor moves the ball and so can "break" a shape.
ACTION_TYPES = {"Pass", "Carry", "Shot", "Dribble"}

# pass.type values that are restarts. (Recovery / Interception describe how
# the passer won the ball, not a set piece.)
SET_PIECES = {"Corner", "Free Kick", "Throw-in", "Goal Kick", "Kick Off"}


def _name(obj: dict | None) -> str | None:
    return (obj or {}).get("name")


def event_action(event: dict, defending_team_id: int) -> FrameAction | None:
    kind = _name(event.get("type"))
    if kind not in ACTION_TYPES:
        return None

    detail = event.get(kind.lower()) or {}
    end = detail.get("end_location")
    end_x = end_y = None
    if end and len(end) >= 2:
        nx, ny = normalize_point(event, defending_team_id, end[0], end[1])
        end_x, end_y = round(nx, 3), round(ny, 3)

    action = FrameAction(
        kind=kind,
        end_x=end_x,
        end_y=end_y,
        under_pressure=bool(event.get("under_pressure", False)),
    )
    if kind == "Pass":
        action.cross = bool(detail.get("cross", False))
        action.through_ball = bool(detail.get("through_ball", False)) or (
            _name(detail.get("technique")) == "Through Ball"
        )
        action.cut_back = bool(detail.get("cut_back", False))
        action.switch = bool(detail.get("switch", False))
        action.height = _name(detail.get("height"))
        pass_type = _name(detail.get("type"))
        action.set_piece = pass_type if pass_type in SET_PIECES else None
    return action
