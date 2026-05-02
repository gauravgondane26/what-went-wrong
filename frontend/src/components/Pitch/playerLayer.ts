import * as d3 from 'd3'
import type { FrameData, PlayerPosition } from '../../types/frame'

// Player dot colors
const ATTACKER_COLOR = '#e05c2a'   // orange-red
const DEFENDER_COLOR = '#3a86e8'   // blue
const KEEPER_COLOR = '#f7c948'     // yellow
const ACTOR_RING_COLOR = '#ffffff' // white ring on the actor

const DOT_RADIUS = 5
const KEEPER_RADIUS = 6
const ACTOR_RING_WIDTH = 1.5
const TRANSITION_MS = 300

const LOW_DEFENDER_WARNING_THRESHOLD = 6

/**
 * Renders/updates player dots and the ball on the pitch.
 * Uses D3 enter/update/exit with transitions for smooth frame stepping.
 */
export function renderPlayerLayer(
  svg: d3.Selection<SVGSVGElement, unknown, null, undefined>,
  frame: FrameData,
  xScale: d3.ScaleLinear<number, number>,
  yScale: d3.ScaleLinear<number, number>,
) {
  // --- Player dots ---
  let g = svg.select<SVGGElement>('g.player-layer')
  if (g.empty()) {
    g = svg.append('g').attr('class', 'player-layer').attr('pointer-events', 'none')
  }

  const dots = g
    .selectAll<SVGCircleElement, PlayerPosition>('circle.player')
    .data(frame.players, (_d, i) => String(i))

  // Enter: appear at position but fade in
  dots
    .enter()
    .append('circle')
    .attr('class', 'player')
    .attr('cx', d => xScale(d.x))
    .attr('cy', d => yScale(d.y))
    .attr('r', d => (d.keeper ? KEEPER_RADIUS : DOT_RADIUS))
    .attr('fill', playerColor)
    .attr('stroke', d => (d.actor ? ACTOR_RING_COLOR : 'none'))
    .attr('stroke-width', d => (d.actor ? ACTOR_RING_WIDTH : 0))
    .attr('opacity', 0)
    .transition()
    .duration(TRANSITION_MS)
    .attr('opacity', 1)

  // Update with transition
  dots
    .transition()
    .duration(TRANSITION_MS)
    .attr('cx', d => xScale(d.x))
    .attr('cy', d => yScale(d.y))
    .attr('r', d => (d.keeper ? KEEPER_RADIUS : DOT_RADIUS))
    .attr('fill', playerColor)
    .attr('stroke', d => (d.actor ? ACTOR_RING_COLOR : 'none'))
    .attr('stroke-width', d => (d.actor ? ACTOR_RING_WIDTH : 0))
    .attr('opacity', 1)

  // Exit: fade out then remove
  dots
    .exit()
    .transition()
    .duration(TRANSITION_MS)
    .attr('opacity', 0)
    .remove()

  // --- Ball ---
  renderBall(svg, frame, xScale, yScale)

  // --- Low defender count warning indicator ---
  renderWarning(svg, frame)
}

function playerColor(d: PlayerPosition): string {
  if (d.keeper) return KEEPER_COLOR
  return d.is_attacker ? ATTACKER_COLOR : DEFENDER_COLOR
}

function renderBall(
  svg: d3.Selection<SVGSVGElement, unknown, null, undefined>,
  frame: FrameData,
  xScale: d3.ScaleLinear<number, number>,
  yScale: d3.ScaleLinear<number, number>,
) {
  let ball = svg.select<SVGGElement>('g.ball-layer')
  if (ball.empty()) {
    ball = svg.append('g').attr('class', 'ball-layer').attr('pointer-events', 'none')
  }

  // White circle with black outline
  let circle = ball.select<SVGCircleElement>('circle.ball')
  if (circle.empty()) {
    circle = ball.append('circle').attr('class', 'ball').attr('r', 4)
  }

  circle
    .transition()
    .duration(TRANSITION_MS)
    .attr('cx', xScale(frame.ball_x))
    .attr('cy', yScale(frame.ball_y))
    .attr('fill', '#ffffff')
    .attr('stroke', '#222222')
    .attr('stroke-width', 1)
}

function renderWarning(
  svg: d3.Selection<SVGSVGElement, unknown, null, undefined>,
  frame: FrameData,
) {
  svg.select('g.warning-layer').remove()

  const defenderCount = frame.players.filter(
    p => !p.is_attacker && !p.keeper,
  ).length

  if (defenderCount >= LOW_DEFENDER_WARNING_THRESHOLD) return

  const g = svg.append('g').attr('class', 'warning-layer')

  g.append('text')
    .attr('x', 8)
    .attr('y', 16)
    .attr('fill', '#f7c948')
    .attr('font-size', '11px')
    .attr('font-family', 'monospace')
    .text(`only ${defenderCount} defenders visible`)
}
