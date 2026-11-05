/**
 * Pitch geometry for the visualisation. Pure functions, no DOM.
 *
 * Coordinates are normalised by the backend: StatsBomb 120 × 80 yards, defending goal at x = 0.
 * The lane test mirrors backend/app/services/scorer.py (`_is_shadowed`, `shadow_targets`,
 * COMPACT_UNIT) so the pitch draws exactly what the shape score counts, and `boxMarking`
 * mirrors `box_marking` (BOX_*, MARK_RADIUS). Keep them in sync.
 */
import type { FrameData, GoalSequenceResponse, PlayerPosition } from '../types/frame'

export const PITCH_LENGTH = 120
export const PITCH_WIDTH = 80
/** Outer drawing bounds: the pitch plus room for the goal mouths. */
export const FULL_VIEW = { x: -4, y: -3, w: 128, h: 86 } as const
export const VIEW_RATIO = FULL_VIEW.w / FULL_VIEW.h

const MAX_SHADOW_RANGE = 40
const CARRIER_RADIUS = 2
const COMPACT_UNIT = 6
const BOX_DEPTH = 18
const BOX_Y_MIN = 18
const BOX_Y_MAX = 62
const MARK_RADIUS = 2

export const inBox = (p: { x: number; y: number }) => p.x <= BOX_DEPTH && p.y >= BOX_Y_MIN && p.y <= BOX_Y_MAX

/**
 * Outfield attackers in the defended box, and those with no defender (keeper included)
 * within MARK_RADIUS. Mirrors scorer.box_marking: a defender exactly at the radius marks.
 */
export function boxMarking(players: PlayerPosition[]): { inBox: PlayerPosition[]; unmarked: PlayerPosition[] } {
  const markers = players.filter((p) => !p.is_attacker)
  const area = players.filter((p) => p.is_attacker && !p.keeper && inBox(p))
  return {
    inBox: area,
    unmarked: area.filter((a) => markers.every((m) => Math.hypot(a.x - m.x, a.y - m.y) > MARK_RADIUS)),
  }
}

type Pt = [number, number]

export interface Lane {
  target: PlayerPosition
  blocked: boolean
}

export interface FrameGeometry {
  ball: Pt
  /** Visible outfield defenders (keeper excluded). */
  defenders: PlayerPosition[]
  /** Defenders level with or ahead of the ball: not goal-side. */
  upfield: PlayerPosition[]
  /** The COMPACT_UNIT defenders nearest the ball, as used by the compactness score. */
  unit: PlayerPosition[]
  /** Convex hull of `unit`, for drawing. */
  unitHull: Pt[]
  /** One lane per attacker who could receive a pass (not the keeper, not the carrier). */
  lanes: Lane[]
  actor: PlayerPosition | undefined
  /** Attackers in the defended box with no defender within 2 yards (box marking). */
  unmarked: PlayerPosition[]
}

export interface ViewBox {
  x: number
  y: number
  w: number
  h: number
}

function isShadowed(ball: Pt, defender: Pt, attacker: Pt): boolean {
  const [bx, by] = ball
  const [dx, dy] = defender
  const [ax, ay] = attacker
  const defDist = Math.hypot(dx - bx, dy - by)
  if (defDist > MAX_SHADOW_RANGE) return false
  const rayLen = Math.hypot(ax - bx, ay - by)
  if (rayLen < 0.1) return false
  const t = ((dx - bx) * (ax - bx) + (dy - by) * (ay - by)) / (rayLen * rayLen)
  if (!(t > 0.05 && t < 0.95)) return false
  const perp = Math.abs((dx - bx) * (ay - by) - (dy - by) * (ax - bx)) / rayLen
  return perp < Math.max(1.5, defDist * 0.15)
}

/** Andrew's monotone chain. Returns the hull in order; fewer than 3 points come back as-is. */
export function convexHull(points: Pt[]): Pt[] {
  if (points.length < 3) return points
  const p = [...points].sort((a, b) => a[0] - b[0] || a[1] - b[1])
  const cross = (o: Pt, a: Pt, b: Pt) => (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
  const lower: Pt[] = []
  for (const q of p) {
    while (lower.length >= 2 && cross(lower[lower.length - 2], lower[lower.length - 1], q) <= 0) lower.pop()
    lower.push(q)
  }
  const upper: Pt[] = []
  for (const q of [...p].reverse()) {
    while (upper.length >= 2 && cross(upper[upper.length - 2], upper[upper.length - 1], q) <= 0) upper.pop()
    upper.push(q)
  }
  return lower.slice(0, -1).concat(upper.slice(0, -1))
}

export function frameGeometry(frame: FrameData): FrameGeometry {
  const ball: Pt = [frame.ball_x, frame.ball_y]
  const defenders = frame.players.filter((p) => !p.is_attacker && !p.keeper)
  const dist = (p: PlayerPosition) => Math.hypot(p.x - ball[0], p.y - ball[1])
  const targets = frame.players.filter(
    (p) => p.is_attacker && !p.keeper && !p.actor && dist(p) > CARRIER_RADIUS,
  )
  const lanes = targets.map((target) => ({
    target,
    blocked: defenders.some((d) => isShadowed(ball, [d.x, d.y], [target.x, target.y])),
  }))
  const unit = [...defenders].sort((a, b) => dist(a) - dist(b)).slice(0, COMPACT_UNIT)
  return {
    ball,
    defenders,
    upfield: defenders.filter((d) => d.x >= frame.ball_x),
    unit,
    unitHull: convexHull(unit.map((p) => [p.x, p.y] as Pt)),
    lanes,
    actor: frame.players.find((p) => p.actor),
    unmarked: boxMarking(frame.players).unmarked,
  }
}

/**
 * One camera for the whole move: the box around every player and the ball across all frames,
 * always including the defended goal at x = 0, padded and widened to the pitch's aspect ratio.
 * Fixed per sequence so the view never jumps between frames.
 */
export function sequenceView(seq: GoalSequenceResponse): ViewBox {
  let x1 = -Infinity
  let y0 = Infinity
  let y1 = -Infinity
  for (const f of seq.frames) {
    for (const p of f.players) { x1 = Math.max(x1, p.x); y0 = Math.min(y0, p.y); y1 = Math.max(y1, p.y) }
    x1 = Math.max(x1, f.ball_x); y0 = Math.min(y0, f.ball_y); y1 = Math.max(y1, f.ball_y)
  }
  if (!Number.isFinite(x1)) return { ...FULL_VIEW }
  const pad = 7
  const w = Math.min(FULL_VIEW.w, Math.max(x1 + pad * 2, (y1 - y0 + pad * 2) * VIEW_RATIO, 56))
  const h = w / VIEW_RATIO
  const x = Math.max(FULL_VIEW.x, Math.min(FULL_VIEW.x + FULL_VIEW.w - w, -4))
  const y = Math.max(FULL_VIEW.y, Math.min(FULL_VIEW.y + FULL_VIEW.h - h, (y0 + y1) / 2 - h / 2))
  return { x, y, w, h }
}
