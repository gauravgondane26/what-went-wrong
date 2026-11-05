from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class PlayerPosition(BaseModel):
    x: float  # normalized: defending goal at x=0, attacking direction → x=120
    y: float  # 0–80 unchanged
    is_attacker: bool  # True = same team as ball carrier (attacking team)
    actor: bool  # True = this player performed the event action
    keeper: bool


class CoverShadow(BaseModel):
    origin_x: float  # ball position
    origin_y: float
    left_x: float  # left boundary of cone
    left_y: float
    right_x: float  # right boundary of cone
    right_y: float


class DefensiveScores(BaseModel):
    compactness: float  # 0–1; higher = tighter unit (spread of the 6 defenders nearest the ball)
    line_height: float  # raw x of the 4 deepest defenders; display only, not in composite
    goal_side_share: float  # 0–1; fraction of outfield defenders between ball and own goal
    cover_shadow_coverage: float  # 0–1; fraction of receivable attackers with a lane blocked
    # 0.4*compactness + 0.3*goal_side_share + 0.3*shadow_coverage; None when not reliable
    composite: float | None
    defenders_visible: int  # visible outfield defenders (keeper excluded)
    reliable: bool  # defenders_visible >= MIN_RELIABLE_DEFENDERS
    # Box marking (display + collapse detection, not in composite): outfield
    # attackers in the defended penalty area, and those with no defender within 2 units.
    attackers_in_box: int = 0
    unmarked_in_box: int = 0


class FrameAction(BaseModel):
    """What the event's actor did with the ball (Pass, Carry, Shot, Dribble).

    End coordinates are normalized like the ball (defending goal at x=0); None
    when the event has no end location (Dribble).
    """

    kind: str  # StatsBomb event type name: "Pass", "Carry", "Shot", "Dribble"
    end_x: float | None = None
    end_y: float | None = None
    cross: bool = False
    through_ball: bool = False
    cut_back: bool = False
    switch: bool = False
    height: str | None = None     # passes: "Ground Pass" | "Low Pass" | "High Pass"
    set_piece: str | None = None  # passes: "Corner" | "Free Kick" | "Throw-in" | "Goal Kick" | "Kick Off"
    under_pressure: bool = False


class FrameData(BaseModel):
    frame_index: int
    event_id: str
    event_type: str  # "Pass", "Carry", "Shot", "Pressure", etc.
    minute: int
    second: int
    period: int
    timestamp_seconds: float

    ball_x: float  # normalized coordinates
    ball_y: float

    players: list[PlayerPosition]
    player_count: int  # visible players; < 6 defenders = data quality warning

    scores: DefensiveScores
    cover_shadows: list[CoverShadow]
    pressure_grid: list[float]  # 384 floats (24 cols × 16 rows), row-major, values 0–1

    is_collapse_frame: bool  # True on at most one frame: where the defence fell apart (see collapse.py)
    # On the collapse frame: which signal found it — "shape" (composite drop) or
    # "marking" (rise in unmarked attackers in the box). None on other frames.
    collapse_kind: Literal["shape", "marking"] | None = None
    # composite minus the previous reliable frame's; None if unreliable or first reliable
    score_delta: float | None

    # The ball-moving action on this frame's event. When later events repeat this
    # frame's snapshot (e.g. a Carry after its Ball Receipt*), the first of their
    # actions is adopted if this event has none. None if no event moved the ball.
    action: FrameAction | None = None


class GoalSequenceResponse(BaseModel):
    match_id: int
    goal_event_id: str
    defending_team_id: int
    defending_team_name: str
    attacking_team_id: int
    attacking_team_name: str
    collapse_frame_index: int | None  # None when neither the shape nor the marking broke down
    collapse_kind: Literal["shape", "marking"] | None = None
    frames: list[FrameData]
    # StatsBomb play pattern of the goal's possession: "Regular Play", "From Corner",
    # "From Free Kick", "From Throw In", "From Counter", "From Goal Kick", ...
    play_pattern: str | None = None


class GoalSummary(BaseModel):
    goal_event_id: str
    goal_event_index: int
    minute: int
    second: int
    period: int
    scoring_team_id: int
    scoring_team_name: str
    conceding_team_id: int
    conceding_team_name: str
    xg: float | None
    possession_number: int
    is_penalty: bool  # in-game penalty (shot.type == "Penalty"); shape analysis is limited
    sequence_length: int  # number of events in the possession sequence


class MatchSummary(BaseModel):
    match_id: int
    match_date: str
    home_team_id: int
    home_team_name: str
    away_team_id: int
    away_team_name: str
    home_score: int
    away_score: int
    competition_stage: str


class CompetitionSummary(BaseModel):
    competition_id: int
    season_id: int
    competition_name: str
    season_name: str
    country_name: str
