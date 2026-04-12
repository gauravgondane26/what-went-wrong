import * as d3 from 'd3'
import type { CoverShadow, FrameData } from '../../types/frame'

const SHADOW_FILL = 'rgba(255, 200, 50, 0.12)'
const SHADOW_STROKE = 'rgba(255, 200, 50, 0.3)'
const SHADOW_STROKE_WIDTH = 0.5
const TRANSITION_MS = 200

/**
 * Renders/updates cover shadow cones on the pitch.
 * Each cone is a triangle from the ball origin through two boundary points.
 */
export function renderShadowLayer(
  svg: d3.Selection<SVGSVGElement, unknown, null, undefined>,
  frame: FrameData,
  xScale: d3.ScaleLinear<number, number>,
  yScale: d3.ScaleLinear<number, number>,
) {
  let g = svg.select<SVGGElement>('g.shadow-layer')
  if (g.empty()) {
    // Insert above pressure layer, below player layer
    const playerLayer = svg.select('g.player-layer')
    if (!playerLayer.empty()) {
      g = (playerLayer.node() as Element).parentNode
        ? d3.select((playerLayer.node() as Element).parentNode as SVGSVGElement)
            .insert('g', 'g.player-layer')
        : svg.append('g')
    } else {
      g = svg.append('g')
    }
    g.attr('class', 'shadow-layer').attr('pointer-events', 'none')
  }

  const shadowPath = (s: CoverShadow) =>
    `M ${xScale(s.origin_x)},${yScale(s.origin_y)} ` +
    `L ${xScale(s.left_x)},${yScale(s.left_y)} ` +
    `L ${xScale(s.right_x)},${yScale(s.right_y)} Z`

  const paths = g
    .selectAll<SVGPathElement, CoverShadow>('path.shadow-cone')
    .data(frame.cover_shadows, (_d, i) => String(i))

  // Enter
  paths
    .enter()
    .append('path')
    .attr('class', 'shadow-cone')
    .attr('d', shadowPath)
    .attr('fill', SHADOW_FILL)
    .attr('stroke', SHADOW_STROKE)
    .attr('stroke-width', SHADOW_STROKE_WIDTH)

  // Update with transition
  paths
    .transition()
    .duration(TRANSITION_MS)
    .attr('d', shadowPath)

  // Exit
  paths.exit().remove()
}
