/**
 * The overlays that draw each score on the pitch. Pure D3, zero React imports.
 *   - last line:  dashed line at the average x of the 4 deepest defenders (line_height)
 *   - unit:       hull of the 6 defenders nearest the ball (compactness)
 *   - lanes:      ball → each receivable attacker; dashed ink when open, faint blue when blocked
 *                 (cover shadows, same test as the backend)
 *   - unmarked:   dashed ring on attackers free in the box (box marking, same test as the backend)
 */
import type * as d3 from 'd3'
import type { FrameData } from '../../types/frame'
import type { FrameGeometry, ViewBox } from '../../lib/geometry'
import { PITCH_THEME as T } from './theme'

type G = d3.Selection<SVGGElement, unknown, null, undefined>

export function renderLastLine(g: G, frame: FrameData, geo: FrameGeometry, view: ViewBox, visible: boolean) {
  g.selectAll('*').remove()
  if (!visible || geo.defenders.length < 4) return
  const x = frame.scores.line_height
  g.append('path')
    .attr('d', `M${x} 0V80`)
    .attr('stroke', T.defence)
    .attr('stroke-width', 1.25)
    .attr('stroke-dasharray', '4 3')
    .attr('vector-effect', 'non-scaling-stroke')
    .attr('fill', 'none')
  const fs = Math.max(2, view.w / 48)
  g.append('text')
    .attr('x', x + fs * 0.5)
    .attr('y', Math.max(0, view.y) + fs * 1.4)
    .attr('font-size', fs)
    .attr('font-family', T.fontSans)
    .attr('font-weight', 500)
    .attr('fill', T.defence)
    .text(`Last line · ${Math.round(x)} yd`)
}

export function renderUnit(g: G, geo: FrameGeometry, visible: boolean) {
  const data = visible && geo.unitHull.length >= 3 ? [geo.unitHull] : []
  g.selectAll<SVGPolygonElement, [number, number][]>('polygon')
    .data(data)
    .join('polygon')
    .attr('points', (d) => d.map((p) => p.join(',')).join(' '))
    .attr('fill', T.defence)
    .attr('fill-opacity', 0.1)
    .attr('stroke', T.defence)
    .attr('stroke-width', 1.25)
    .attr('stroke-linejoin', 'round')
    .attr('vector-effect', 'non-scaling-stroke')
}

export function renderLanes(g: G, frame: FrameData, geo: FrameGeometry, visible: boolean) {
  const lanes = visible ? geo.lanes : []
  g.selectAll<SVGPathElement, (typeof lanes)[number]>('path')
    .data(lanes)
    .join('path')
    .attr('d', (l) => `M${frame.ball_x} ${frame.ball_y}L${l.target.x} ${l.target.y}`)
    .attr('fill', 'none')
    .attr('stroke', (l) => (l.blocked ? T.defence : T.ink))
    .attr('stroke-opacity', (l) => (l.blocked ? 0.4 : 0.9))
    .attr('stroke-width', 1.5)
    .attr('stroke-dasharray', (l) => (l.blocked ? null : '4 3'))
    .attr('stroke-linecap', 'round')
    .attr('vector-effect', 'non-scaling-stroke')
}

/** Dashed ink ring around each attacker in the box with no defender within 2 yards (box marking). */
export function renderUnmarked(g: G, geo: FrameGeometry, visible: boolean) {
  const free = visible ? geo.unmarked : []
  g.selectAll<SVGCircleElement, (typeof free)[number]>('circle')
    .data(free)
    .join('circle')
    .attr('cx', (p) => p.x)
    .attr('cy', (p) => p.y)
    .attr('r', 3.1)
    .attr('fill', 'none')
    .attr('stroke', T.ink)
    .attr('stroke-width', 1.25)
    .attr('stroke-dasharray', '2 2')
    .attr('vector-effect', 'non-scaling-stroke')
}
