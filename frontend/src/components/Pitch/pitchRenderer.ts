/**
 * Pure D3 orchestrator — zero React imports.
 * Called from PitchContainer via the useD3 hook whenever the frame changes.
 *
 * Layer order (bottom → top):
 *   1. pitch-markings  (static, drawn once)
 *   2. pressure-layer  (heatmap)
 *   3. shadow-layer    (cover shadow cones)
 *   4. player-layer    (dots + ball)
 *   5. warning-layer   (low defender count badge, inside playerLayer)
 */
import * as d3 from 'd3'
import type { FrameData } from '../../types/frame'
import { drawPitchMarkings } from './pitchMarkings'
import { renderPlayerLayer } from './playerLayer'
import { renderPressureLayer } from './pressureLayer'
import { renderShadowLayer } from './shadowLayer'

export function renderPitchFrame(
  svg: d3.Selection<SVGSVGElement, unknown, null, undefined>,
  frame: FrameData,
  svgWidth: number,
  svgHeight: number,
) {
  const xScale = d3.scaleLinear([0, 120], [0, svgWidth])
  const yScale = d3.scaleLinear([0, 80], [0, svgHeight])

  // Draw markings once — skip if already present
  if (svg.select('g.pitch-markings').empty()) {
    drawPitchMarkings(svg, xScale, yScale)
  }

  renderPressureLayer(svg, frame, xScale, yScale)
  renderShadowLayer(svg, frame, xScale, yScale)
  renderPlayerLayer(svg, frame, xScale, yScale)
}

/**
 * Called on initial mount to draw a blank pitch with no frame data.
 */
export function renderEmptyPitch(
  svg: d3.Selection<SVGSVGElement, unknown, null, undefined>,
  svgWidth: number,
  svgHeight: number,
) {
  const xScale = d3.scaleLinear([0, 120], [0, svgWidth])
  const yScale = d3.scaleLinear([0, 80], [0, svgHeight])
  drawPitchMarkings(svg, xScale, yScale)
}
