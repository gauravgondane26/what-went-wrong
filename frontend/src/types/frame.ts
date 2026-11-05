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
  compactness: number             // 0–1; higher = tighter unit (6 defenders nearest the ball)
  line_height: number             // raw x of the 4 deepest defenders; display only
  goal_side_share: number         // 0–1; fraction of outfield defenders between ball and own goal
  cover_shadow_coverage: number   // 0–1; fraction of receivable attackers shadowed
  composite: number | null        // weighted combined score; null when not reliable
  defenders_visible: number       // visible outfield defenders (keeper excluded)
  reliable: boolean               // enough defenders visible to score the shape
  attackers_in_box: number        // outfield attackers in the defended penalty area
  unmarked_in_box: number         // of those, with no defender within 2 units (not in composite)
}

export type ActionKind = 'Pass' | 'Carry' | 'Shot' | 'Dribble'

// What the event's actor did with the ball. End coordinates are normalized
// like the ball; null when the event has no end location (Dribble).
export interface FrameAction {
  kind: ActionKind
  end_x: number | null
  end_y: number | null
  cross: boolean
  through_ball: boolean
  cut_back: boolean
  switch: boolean
  height: 'Ground Pass' | 'Low Pass' | 'High Pass' | null       // passes only
  set_piece: 'Corner' | 'Free Kick' | 'Throw-in' | 'Goal Kick' | 'Kick Off' | null
  under_pressure: boolean
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
  score_delta: number | null  // composite minus previous reliable frame's; null if unreliable/first

  // Ball-moving action on this frame's event (or on a later event that repeated
  // this snapshot); null when no event moved the ball.
  action: FrameAction | null
}

export interface GoalSequenceResponse {
  match_id: number
  goal_event_id: string
  defending_team_id: number
  defending_team_name: string
  attacking_team_id: number
  attacking_team_name: string
  collapse_frame_index: number | null  // null when no reliable drop was found
  frames: FrameData[]
  play_pattern: string | null  // "Regular Play" | "From Corner" | "From Counter" | ...
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
