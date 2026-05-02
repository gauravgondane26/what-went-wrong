import * as d3 from 'd3'

// StatsBomb pitch dimensions
const PITCH_LENGTH = 120
const PITCH_WIDTH = 80

// Penalty box dimensions
const PENALTY_BOX_LENGTH = 18
const PENALTY_BOX_WIDTH = 44
const GOAL_BOX_LENGTH = 6
const GOAL_BOX_WIDTH = 20
const PENALTY_SPOT_DIST = 12
const CENTRE_CIRCLE_RADIUS = 10
const CORNER_ARC_RADIUS = 1

const LINE_COLOR = 'rgba(255,255,255,0.7)'
const LINE_WIDTH = 0.5

/**
 * Draws static pitch markings onto an SVG <g> layer.
 * Called once on mount — never redrawn unless the SVG is destroyed.
 *
 * All coordinates are in StatsBomb units (0–120 × 0–80).
 * Callers pass in D3 scales to convert to SVG pixels.
 */
export function drawPitchMarkings(
  svg: d3.Selection<SVGSVGElement, unknown, null, undefined>,
  xScale: d3.ScaleLinear<number, number>,
  yScale: d3.ScaleLinear<number, number>,
) {
  // Remove any existing markings layer before redrawing
  svg.select('g.pitch-markings').remove()

  const g = svg
    .append('g')
    .attr('class', 'pitch-markings')
    .attr('pointer-events', 'none')

  const x = (v: number) => xScale(v)
  const y = (v: number) => yScale(v)
  const w = (v: number) => Math.abs(xScale(v) - xScale(0))
  const h = (v: number) => Math.abs(yScale(v) - yScale(0))

  const line = (attrs: Record<string, number | string>) =>
    g
      .append('line')
      .attr('stroke', LINE_COLOR)
      .attr('stroke-width', LINE_WIDTH)
      .each(function () {
        Object.entries(attrs).forEach(([k, v]) => d3.select(this).attr(k, v))
      })

  const rect = (
    rx: number,
    ry: number,
    rw: number,
    rh: number,
  ) =>
    g
      .append('rect')
      .attr('x', x(rx))
      .attr('y', y(ry))
      .attr('width', w(rw))
      .attr('height', h(rh))
      .attr('fill', 'none')
      .attr('stroke', LINE_COLOR)
      .attr('stroke-width', LINE_WIDTH)

  // Pitch outline
  rect(0, 0, PITCH_LENGTH, PITCH_WIDTH)

  // Halfway line
  line({
    x1: x(PITCH_LENGTH / 2),
    y1: y(0),
    x2: x(PITCH_LENGTH / 2),
    y2: y(PITCH_WIDTH),
  })

  // Centre circle
  g.append('circle')
    .attr('cx', x(PITCH_LENGTH / 2))
    .attr('cy', y(PITCH_WIDTH / 2))
    .attr('r', w(CENTRE_CIRCLE_RADIUS))
    .attr('fill', 'none')
    .attr('stroke', LINE_COLOR)
    .attr('stroke-width', LINE_WIDTH)

  // Centre spot
  g.append('circle')
    .attr('cx', x(PITCH_LENGTH / 2))
    .attr('cy', y(PITCH_WIDTH / 2))
    .attr('r', 2)
    .attr('fill', LINE_COLOR)

  // --- Left side (x=0, defending goal in normalized coords) ---
  const leftBoxY = (PITCH_WIDTH - PENALTY_BOX_WIDTH) / 2
  const leftSmallBoxY = (PITCH_WIDTH - GOAL_BOX_WIDTH) / 2

  // Left penalty box
  rect(0, leftBoxY, PENALTY_BOX_LENGTH, PENALTY_BOX_WIDTH)
  // Left goal box
  rect(0, leftSmallBoxY, GOAL_BOX_LENGTH, GOAL_BOX_WIDTH)
  // Left goal
  rect(-2, (PITCH_WIDTH - 8) / 2, 2, 8)
    .attr('stroke', 'rgba(255,255,255,0.5)')
  // Left penalty spot
  g.append('circle')
    .attr('cx', x(PENALTY_SPOT_DIST))
    .attr('cy', y(PITCH_WIDTH / 2))
    .attr('r', 2)
    .attr('fill', LINE_COLOR)
  // Left penalty arc
  drawPenaltyArc(g, x, y, w, 'left')

  // --- Right side (x=120, attacking goal) ---
  const rightBoxX = PITCH_LENGTH - PENALTY_BOX_LENGTH
  const rightSmallBoxX = PITCH_LENGTH - GOAL_BOX_LENGTH

  // Right penalty box
  rect(rightBoxX, leftBoxY, PENALTY_BOX_LENGTH, PENALTY_BOX_WIDTH)
  // Right goal box
  rect(rightSmallBoxX, leftSmallBoxY, GOAL_BOX_LENGTH, GOAL_BOX_WIDTH)
  // Right goal
  rect(PITCH_LENGTH, (PITCH_WIDTH - 8) / 2, 2, 8)
    .attr('stroke', 'rgba(255,255,255,0.5)')
  // Right penalty spot
  g.append('circle')
    .attr('cx', x(PITCH_LENGTH - PENALTY_SPOT_DIST))
    .attr('cy', y(PITCH_WIDTH / 2))
    .attr('r', 2)
    .attr('fill', LINE_COLOR)
  // Right penalty arc
  drawPenaltyArc(g, x, y, w, 'right')

  // Corner arcs
  drawCornerArc(g, x, y, w, 0, 0, 0)        // top-left
  drawCornerArc(g, x, y, w, PITCH_LENGTH, 0, 90)   // top-right
  drawCornerArc(g, x, y, w, 0, PITCH_WIDTH, 270)   // bottom-left
  drawCornerArc(g, x, y, w, PITCH_LENGTH, PITCH_WIDTH, 180) // bottom-right
}

function drawPenaltyArc(
  g: d3.Selection<SVGGElement, unknown, null, undefined>,
  x: (v: number) => number,
  y: (v: number) => number,
  w: (v: number) => number,
  side: 'left' | 'right',
) {
  const cx = side === 'left' ? PENALTY_SPOT_DIST : PITCH_LENGTH - PENALTY_SPOT_DIST
  const arcRadius = w(CENTRE_CIRCLE_RADIUS)
  // D3 arc: 0 = 12 o'clock, clockwise.
  // Left arc faces right (toward centre): centred at 90° (3 o'clock) ± 53°.
  // Right arc faces left (toward centre): centred at 270° (9 o'clock) ± 53°.
  const startAngle = side === 'left' ? 37 : 217
  const endAngle = side === 'left' ? 143 : 323

  const arcPath = d3.arc<unknown>()({
    innerRadius: arcRadius,
    outerRadius: arcRadius,
    startAngle: (startAngle * Math.PI) / 180,
    endAngle: (endAngle * Math.PI) / 180,
  })

  if (arcPath) {
    g.append('path')
      .attr('d', arcPath)
      .attr('transform', `translate(${x(cx)},${y(PITCH_WIDTH / 2)})`)
      .attr('fill', 'none')
      .attr('stroke', LINE_COLOR)
      .attr('stroke-width', LINE_WIDTH)
  }
}

function drawCornerArc(
  g: d3.Selection<SVGGElement, unknown, null, undefined>,
  x: (v: number) => number,
  y: (v: number) => number,
  w: (v: number) => number,
  cx: number,
  cy: number,
  rotationDeg: number,
) {
  const r = w(CORNER_ARC_RADIUS)
  const arcPath = d3.arc<unknown>()({
    innerRadius: r,
    outerRadius: r,
    startAngle: 0,
    endAngle: Math.PI / 2,
  })

  if (arcPath) {
    g.append('path')
      .attr('d', arcPath)
      .attr('transform', `translate(${x(cx)},${y(cy)}) rotate(${rotationDeg})`)
      .attr('fill', 'none')
      .attr('stroke', LINE_COLOR)
      .attr('stroke-width', LINE_WIDTH)
  }
}
