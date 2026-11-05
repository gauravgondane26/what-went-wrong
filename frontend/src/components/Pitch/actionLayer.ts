/**
 * Ball's path: an ink arrow for the move on the ball. Pure D3, zero React imports.
 *   - most frames: this frame's own action, from the ball to where it ends up
 *   - the collapse frame: the action that broke the defence (collapse_cause), from
 *     where it started, so the cause is on screen at the moment it is named
 * Passes are solid, carries dashed. Only telling moves get a label.
 * The arrowhead is drawn as a path (no <marker>, so no element ids to clash).
 */
import type * as d3 from 'd3'
import type { FrameAction, FrameData } from '../../types/frame'
import type { ViewBox } from '../../lib/geometry'
import { PITCH_THEME as T } from './theme'

type G = d3.Selection<SVGGElement, unknown, null, undefined>

/** The action that led into the collapse, with where it started. */
export interface IncomingAction {
  action: FrameAction
  fromX: number
  fromY: number
}

interface Arrow {
  x1: number
  y1: number
  x2: number
  y2: number
  dashed: boolean
  label: string | null
}

export function actionLabel(a: FrameAction): string | null {
  if (a.kind !== 'Pass') return null
  if (a.set_piece) return a.set_piece === 'Kick Off' ? 'Kick-off' : a.set_piece.charAt(0) + a.set_piece.slice(1).toLowerCase()
  if (a.cross) return 'Cross'
  if (a.through_ball) return 'Through ball'
  if (a.cut_back) return 'Cut-back'
  if (a.switch) return 'Switch'
  return null
}

function toArrow(a: FrameAction, fromX: number, fromY: number): Arrow | null {
  if (a.end_x === null || a.end_y === null) return null
  if (Math.hypot(a.end_x - fromX, a.end_y - fromY) < 1.5) return null // too short to read
  return { x1: fromX, y1: fromY, x2: a.end_x, y2: a.end_y, dashed: a.kind === 'Carry', label: actionLabel(a) }
}

function head(a: Arrow, size: number): string {
  const ang = Math.atan2(a.y2 - a.y1, a.x2 - a.x1)
  const back = (da: number) => [a.x2 - size * Math.cos(ang + da), a.y2 - size * Math.sin(ang + da)]
  const [l, r] = [back(0.45), back(-0.45)]
  return `M${a.x2} ${a.y2}L${l[0]} ${l[1]}L${r[0]} ${r[1]}Z`
}

export function renderActionLayer(
  g: G,
  frame: FrameData,
  incoming: IncomingAction | null,
  view: ViewBox,
  visible: boolean,
) {
  const arrow = !visible
    ? null
    : incoming
      ? toArrow(incoming.action, incoming.fromX, incoming.fromY)
      : frame.action
        ? toArrow(frame.action, frame.ball_x, frame.ball_y)
        : null
  const data = arrow ? [arrow] : []
  const size = Math.max(1.2, view.w / 70)

  g.selectAll<SVGPathElement, Arrow>('path.ball-path')
    .data(data)
    .join('path')
    .attr('class', 'ball-path')
    .attr('d', (a) => `M${a.x1} ${a.y1}L${a.x2} ${a.y2}`)
    .attr('fill', 'none')
    .attr('stroke', T.ink)
    .attr('stroke-width', 1.75)
    .attr('stroke-linecap', 'round')
    .attr('stroke-dasharray', (a) => (a.dashed ? '1 3' : null))
    .attr('vector-effect', 'non-scaling-stroke')

  g.selectAll<SVGPathElement, Arrow>('path.ball-path-head')
    .data(data)
    .join('path')
    .attr('class', 'ball-path-head')
    .attr('d', (a) => head(a, size))
    .attr('fill', T.ink)

  const fs = Math.max(2, view.w / 48)
  g.selectAll<SVGTextElement, Arrow>('text')
    .data(data.filter((a) => a.label))
    .join('text')
    .attr('x', (a) => (a.x1 + a.x2) / 2)
    .attr('y', (a) => (a.y1 + a.y2) / 2 - fs * 0.6)
    .attr('text-anchor', 'middle')
    .attr('font-size', fs)
    .attr('font-family', T.fontSans)
    .attr('font-weight', 500)
    .attr('fill', T.ink)
    .attr('paint-order', 'stroke')
    .attr('stroke', T.pitch)
    .attr('stroke-width', fs * 0.3)
    .text((a) => a.label as string)
}
