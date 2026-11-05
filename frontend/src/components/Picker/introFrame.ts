/**
 * A real frame for the landing illustration: Russia v Denmark, Euro 2020 (match 3788769),
 * Denmark's 78th-minute goal, the collapse moment (78:42). StatsBomb open data.
 * Static so the landing page draws without waiting for the API.
 */
import type { FrameData } from '../../types/frame'

export const INTRO_FRAME: FrameData = {
  "frame_index": 9,
  "event_id": "f8f0bd12-be43-4a28-9082-ea99315f503a",
  "event_type": "Goal Keeper",
  "minute": 78,
  "second": 42,
  "period": 2,
  "timestamp_seconds": 2022.915,
  "ball_x": 1.7,
  "ball_y": 42.0,
  "player_count": 11,
  "is_collapse_frame": true,
  "score_delta": -0.1581,
  "players": [
    {
      "x": 1.7,
      "y": 42.0,
      "is_attacker": false,
      "actor": true,
      "keeper": true
    },
    {
      "x": 5.0,
      "y": 53.32,
      "is_attacker": false,
      "actor": false,
      "keeper": false
    },
    {
      "x": 6.25,
      "y": 43.52,
      "is_attacker": false,
      "actor": false,
      "keeper": false
    },
    {
      "x": 7.33,
      "y": 67.31,
      "is_attacker": false,
      "actor": false,
      "keeper": false
    },
    {
      "x": 8.16,
      "y": 37.72,
      "is_attacker": true,
      "actor": false,
      "keeper": false
    },
    {
      "x": 8.81,
      "y": 51.09,
      "is_attacker": false,
      "actor": false,
      "keeper": false
    },
    {
      "x": 9.4,
      "y": 51.23,
      "is_attacker": true,
      "actor": false,
      "keeper": false
    },
    {
      "x": 9.75,
      "y": 52.7,
      "is_attacker": true,
      "actor": false,
      "keeper": false
    },
    {
      "x": 10.08,
      "y": 45.54,
      "is_attacker": true,
      "actor": false,
      "keeper": false
    },
    {
      "x": 13.28,
      "y": 51.47,
      "is_attacker": false,
      "actor": false,
      "keeper": false
    },
    {
      "x": 19.78,
      "y": 44.34,
      "is_attacker": false,
      "actor": false,
      "keeper": false
    }
  ],
  "scores": {
    "compactness": 0.7147,
    "line_height": 6.85,
    "goal_side_share": 0.0,
    "cover_shadow_coverage": 0.5,
    "composite": 0.4359,
    "defenders_visible": 6,
    "reliable": true,
    "attackers_in_box": 4,
    "unmarked_in_box": 2
  },
  "cover_shadows": [],
  "pressure_grid": [],
  "action": null
}
