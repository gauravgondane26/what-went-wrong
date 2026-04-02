from __future__ import annotations

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
    compactness: float  # 0–1; higher = tighter defensive unit (better shape)
    line_height: float  # raw x-coord of last defensive line, 0–60+; lower = deeper (safer)
    cover_shadow_coverage: float  # 0–1; fraction of attackers with a cover shadow over them
    composite: float  # 0.4*compactness + 0.3*(1 - line_height/60) + 0.3*shadow_coverage


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

    is_collapse_frame: bool  # True on the frame with the steepest composite score drop
    score_delta: float  # composite[i] - composite[i-1]; 0.0 for first frame


class GoalSequenceResponse(BaseModel):
    match_id: int
    goal_event_id: str
    defending_team_id: int
    defending_team_name: str
    attacking_team_id: int
    attacking_team_name: str
    collapse_frame_index: int
    frames: list[FrameData]


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
    is_penalty: bool  # period == 5; shape analysis is limited
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
