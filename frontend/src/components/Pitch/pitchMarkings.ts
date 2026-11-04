/**
 * Static pitch markings in pitch units (StatsBomb 120 × 80 yards). Pure D3, zero React imports.
 * Strokes use vector-effect so they stay 1px at any zoom.
 */
import type * as d3 from 'd3'
import { FULL_VIEW } from '../../lib/geometry'
import { PITCH_THEME as T } from './theme'

type G = d3.Selection<SVGGElement, unknown, null, undefined>

export function drawPitchMarkings(g: G) {
  g.selectAll('*').remove()
  g.append('rect')
    .attr('x', FULL_VIEW.x).attr('y', FULL_VIEW.y)
    .attr('width', FULL_VIEW.w).attr('height', FULL_VIEW.h)
    .attr('fill', T.pitch)

  const lines = g.append('g')
    .attr('fill', 'none')
    .attr('stroke', T.line)
    .attr('stroke-width', 1)
  const path = (d: string) => lines.append('path').attr('d', d).attr('vector-effect', 'non-scaling-stroke')
  const spot = (cx: number, cy: number) =>
    g.append('circle').attr('cx', cx).attr('cy', cy).attr('r', 0.35).attr('fill', T.line)

  path('M0 0H120V80H0Z')
  path('M60 0V80')
  lines.append('circle').attr('cx', 60).attr('cy', 40).attr('r', 10).attr('vector-effect', 'non-scaling-stroke')
  spot(60, 40)

  for (const right of [false, true]) {
    const X = (x: number) => (right ? 120 - x : x)
    path(`M${X(0)} 18H${X(18)}V62H${X(0)}`) // penalty area
    path(`M${X(0)} 30H${X(6)}V50H${X(0)}`) // six-yard box
    path(`M${X(0)} 36H${X(-2)}V44H${X(0)}`) // goal
    path(right ? 'M102 32.7A10 10 0 0 0 102 47.3' : 'M18 32.7A10 10 0 0 1 18 47.3') // arc
    spot(X(12), 40)
  }
}
