/**
 * Defensive pressure field: the backend's 24 × 16 grid (5-yard cells), drawn as a single-hue
 * ramp in the defence colour. Off by default; it's context, not the story. Zero React imports.
 */
import type * as d3 from 'd3'
import type { FrameData } from '../../types/frame'
import { PITCH_THEME as T } from './theme'

type G = d3.Selection<SVGGElement, unknown, null, undefined>

const COLS = 24
const CELL = 5
const MAX_OPACITY = 0.38

interface Cell { col: number; row: number; value: number }

export function renderPressureLayer(g: G, frame: FrameData, visible: boolean) {
  const cells: Cell[] = visible
    ? frame.pressure_grid
        .map((value, i) => ({ col: i % COLS, row: Math.floor(i / COLS), value }))
        .filter((c) => c.value >= 0.04)
    : []

  g.selectAll<SVGRectElement, Cell>('rect')
    .data(cells, (d) => `${d.col}-${d.row}`)
    .join('rect')
    .attr('x', (d) => d.col * CELL)
    .attr('y', (d) => d.row * CELL)
    .attr('width', CELL)
    .attr('height', CELL)
    .attr('fill', T.defence)
    .attr('fill-opacity', (d) => (d.value * MAX_OPACITY).toFixed(3))
}
