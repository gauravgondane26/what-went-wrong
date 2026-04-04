// TypeScript mirror of backend/app/models/frame.py
// Keep in sync with the Pydantic models — field names and types must match exactly.

export interface PlayerPosition {
  x: number               // normalized: defending goal at x=0, attacking toward x=120
  y: number               // 0–80
  is_attacker: boolean    // true = same team as ball carrier
  actor: boolean          // true = player who performed this event
  keeper: boolean
}

export interface CoverShadow {
  origin_x: number        // ball position
  origin_y: number
  left_x: number          // left boundary of cone
  left_y: number
  right_x: number         // right boundary of cone
  right_y: number
}

export interface DefensiveScores {
  compactness: number             // 0–1; higher = tighter unit
  line_height: number             // raw x of last defensive line; lower = deeper/safer
  cover_shadow_coverage: number   // 0–1; fraction of attackers shadowed
  composite: number               // weighted combined score
}

export interface FrameData {
  frame_index: number
  event_id: string
  event_type: string        // "Pass" | "Carry" | "Shot" | "Pressure" | etc.
  minute: number
  second: number
  period: number
  timestamp_seconds: number

  ball_x: number
  ball_y: number

  players: PlayerPosition[]
  player_count: number      // visible players; show warning if < 6 defenders

  scores: DefensiveScores
  cover_shadows: CoverShadow[]
  pressure_grid: number[]   // 384 floats (24 cols × 16 rows), row-major, 0–1

  is_collapse_frame: boolean
  score_delta: number       // composite[i] - composite[i-1]; 0 for first frame
}

export interface GoalSequenceResponse {
  match_id: number
  goal_event_id: string
  defending_team_id: number
  defending_team_name: string
  attacking_team_id: number
  attacking_team_name: string
  collapse_frame_index: number
  frames: FrameData[]
}

export interface GoalSummary {
  goal_event_id: string
  goal_event_index: number
  minute: number
  second: number
  period: number
  scoring_team_id: number
  scoring_team_name: string
  conceding_team_id: number
  conceding_team_name: string
  xg: number | null
  possession_number: number
  is_penalty: boolean
  sequence_length: number
}

export interface MatchSummary {
  match_id: number
  match_date: string
  home_team_id: number
  home_team_name: string
  away_team_id: number
  away_team_name: string
  home_score: number
  away_score: number
  competition_stage: string
}

export interface CompetitionSummary {
  competition_id: number
  season_id: number
  competition_name: string
  season_name: string
  country_name: string
}
