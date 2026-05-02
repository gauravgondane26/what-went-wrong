import * as d3 from 'd3'
import type { FrameData } from '../../types/frame'

const GRID_COLS = 24
const GRID_ROWS = 16
const TRANSITION_MS = 300

// Color scale: transparent → deep blue
const colorScale = d3
  .scaleSequential(d3.interpolateBlues)
  .domain([0, 1])

/**
 * Renders/updates the 24×16 defensive pressure heatmap.
 * Each cell's opacity is driven by the pressure_grid value for that cell.
 * Low pressure = transparent; high pressure = opaque blue.
 */
export function renderPressureLayer(
  svg: d3.Selection<SVGSVGElement, unknown, null, undefined>,
  frame: FrameData,
  xScale: d3.ScaleLinear<number, number>,
  yScale: d3.ScaleLinear<number, number>,
) {
  let g = svg.select<SVGGElement>('g.pressure-layer')
  if (g.empty()) {
    // Insert pressure layer below player layer
    const playerLayer = svg.select('g.player-layer')
    if (!playerLayer.empty()) {
      g = playerLayer.insert<SVGGElement>('g', ':first-child')
    } else {
      g = svg.append('g')
    }
    g.attr('class', 'pressure-layer').attr('pointer-events', 'none')
  }

  const pitchW = 120
  const pitchH = 80
  const cellW = pitchW / GRID_COLS
  const cellH = pitchH / GRID_ROWS

  // Build cell data: {col, row, value}
  interface Cell { col: number; row: number; value: number }
  const cells: Cell[] = frame.pressure_grid.map((value, i) => ({
    col: i % GRID_COLS,
    row: Math.floor(i / GRID_COLS),
    value,
  }))

  const rects = g
    .selectAll<SVGRectElement, Cell>('rect.pressure-cell')
    .data(cells, d => `${d.col}-${d.row}`)

  // Enter
  rects
    .enter()
    .append('rect')
    .attr('class', 'pressure-cell')
    .attr('x', d => xScale(d.col * cellW))
    .attr('y', d => yScale(d.row * cellH))
    .attr('width', Math.abs(xScale(cellW) - xScale(0)))
    .attr('height', Math.abs(yScale(cellH) - yScale(0)))
    .attr('fill', d => colorScale(d.value))
    .attr('opacity', d => d.value * 0.45)

  // Update with transition
  rects
    .transition()
    .duration(TRANSITION_MS)
    .attr('fill', d => colorScale(d.value))
    .attr('opacity', d => d.value * 0.45)

  // No exit needed — grid size is always 384
}
