/**
 * Pure D3 orchestrator, zero React imports. Called from PitchContainer.
 *
 * Layer order (bottom → top), created once and updated per frame:
 *   markings · pressure · last line · unit around the ball · passing lanes · unmarked in the box
 *   · ball's path · players + ball
 *
 * The SVG works in pitch units (viewBox), so zooming to the move is just a viewBox change.
 */
import * as d3 from 'd3'
import type { FrameData } from '../../types/frame'
import { frameGeometry, type ViewBox } from '../../lib/geometry'
import { drawPitchMarkings } from './pitchMarkings'
import { renderPressureLayer } from './pressureLayer'
import { renderLanes, renderLastLine, renderUnit, renderUnmarked } from './shapeLayers'
import { renderPlayers } from './playerLayer'
import { renderActionLayer, type IncomingAction } from './actionLayer'

export interface PitchLayers {
  unit: boolean
  lanes: boolean
  line: boolean
  pressure: boolean
  path: boolean
  unmarked: boolean
}

export const DEFAULT_LAYERS: PitchLayers = {
  unit: true, lanes: true, line: true, pressure: false, path: true, unmarked: true,
}

type Svg = d3.Selection<SVGSVGElement, unknown, null, undefined>
const ORDER = ['markings', 'pressure', 'line', 'unit', 'lanes', 'unmarked', 'path', 'players'] as const

function layer(svg: Svg, name: (typeof ORDER)[number]) {
  return svg.select<SVGGElement>(`g.layer-${name}`)
}

function ensureLayers(svg: Svg) {
  if (svg.select('g.layer-markings').empty()) {
    for (const name of ORDER) svg.append('g').attr('class', `layer-${name}`).attr('pointer-events', 'none')
    drawPitchMarkings(layer(svg, 'markings'))
    return
  }
  // A layer added after this SVG was first drawn (e.g. during hot reload): insert it in order.
  ORDER.forEach((name, i) => {
    if (!layer(svg, name).empty()) return
    const next = ORDER.slice(i + 1).map((n) => layer(svg, n).node()).find(Boolean) ?? null
    svg.insert('g', () => next as Element).attr('class', `layer-${name}`).attr('pointer-events', 'none')
  })
}

export function setView(svg: Svg, view: ViewBox) {
  svg.attr('viewBox', `${view.x} ${view.y} ${view.w} ${view.h}`)
}

export function renderPitchFrame(
  svg: Svg,
  frame: FrameData | null,
  view: ViewBox,
  layers: PitchLayers,
  animate: boolean,
  incoming: IncomingAction | null = null,
) {
  ensureLayers(svg)
  setView(svg, view)
  if (!frame) {
    for (const name of ORDER.slice(1)) layer(svg, name).selectAll('*').remove()
    return
  }
  const geo = frameGeometry(frame)
  renderPressureLayer(layer(svg, 'pressure'), frame, layers.pressure)
  renderLastLine(layer(svg, 'line'), frame, geo, view, layers.line)
  renderUnit(layer(svg, 'unit'), geo, layers.unit)
  renderLanes(layer(svg, 'lanes'), frame, geo, layers.lanes)
  renderUnmarked(layer(svg, 'unmarked'), geo, layers.unmarked)
  renderActionLayer(layer(svg, 'path'), frame, incoming, view, layers.path)
  renderPlayers(layer(svg, 'players'), frame, animate)
}
