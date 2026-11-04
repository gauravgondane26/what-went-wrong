/**
 * Shape-score timeline: one series (composite × 100 per moment) in the defence hue, gaps where a
 * moment isn't scored, the fall into the collapse in red, and an ink cursor on the current moment.
 * Pure D3, zero React imports. Moments are evenly spaced by index: several share a second.
 */
import type * as d3 from 'd3'
import type { FrameData } from '../../types/frame'
import { clock } from '../../lib/copy'
import { PITCH_THEME as T } from '../Pitch/theme'

type Svg = d3.Selection<SVGSVGElement, unknown, null, undefined>

export const TIMELINE_HEIGHT = 132
const M = { l: 34, r: 74, t: 14, b: 34 }
const BANDS: [number, number, string][] = [[1, 0.7, 'Solid'], [0.7, 0.4, 'Stretched'], [0.4, 0, 'Broken']]
const HAIR = '#ebebeb'
const HAIR_STRONG = '#a1a1a1'

export interface TimelineScale {
  x: (i: number) => number
  indexAt: (px: number) => number
  width: number
}

export function timelineScale(width: number, n: number): TimelineScale {
  const inner = width - M.l - M.r
  const step = n > 1 ? inner / (n - 1) : 0
  return {
    width,
    x: (i) => (n === 1 ? M.l + inner / 2 : M.l + i * step),
    indexAt: (px) => (n === 1 ? 0 : Math.max(0, Math.min(n - 1, Math.round((px - M.l) / step)))),
  }
}

export function renderTimeline(svg: Svg, frames: FrameData[], collapse: number | null, width: number) {
  const n = frames.length
  const H = TIMELINE_HEIGHT
  const { x } = timelineScale(width, n)
  const y = (v: number) => M.t + (1 - v) * (H - M.t - M.b)
  const k = (i: number) => frames[i]?.scores.composite ?? null

  svg.attr('viewBox', `0 0 ${width} ${H}`).selectAll('*').remove()
  const g = svg.append('g').attr('font-family', T.fontSans).attr('font-size', 11)
  const mono = (sel: d3.Selection<SVGTextElement, unknown, null, undefined>) =>
    sel.attr('font-family', T.fontMono).attr('font-size', 10).attr('fill', T.mute)

  for (const [a, b, label] of BANDS) {
    g.append('text').attr('x', width - M.r + 10).attr('y', (y(a) + y(b)) / 2 + 4).attr('fill', T.mute).text(label)
  }
  for (const v of [0, 0.4, 0.7, 1]) {
    g.append('path')
      .attr('d', `M${M.l} ${y(v)}H${width - M.r}`)
      .attr('stroke', v === 0 ? HAIR_STRONG : HAIR)
      .attr('stroke-dasharray', v === 0 || v === 1 ? null : '3 3')
    mono(g.append('text')).attr('x', M.l - 8).attr('y', y(v) + 4).attr('text-anchor', 'end').text(Math.round(v * 100))
  }

  const labelled = new Set([0, n - 1])
  if (collapse !== null) labelled.add(collapse)
  if (n > 6) labelled.add(Math.round((n - 1) / 2))
  for (const i of labelled) {
    mono(g.append('text'))
      .attr('x', x(i)).attr('y', H - 8)
      .attr('text-anchor', i === 0 ? 'start' : i === n - 1 ? 'end' : 'middle')
      .text(clock(frames[i]))
  }
  frames.forEach((f, i) => {
    g.append('path').attr('d', `M${x(i)} ${H - M.b + 4}v5`).attr('stroke', f.scores.reliable ? HAIR_STRONG : HAIR)
  })

  let d = ''
  let open = false
  frames.forEach((_, i) => {
    const v = k(i)
    if (v === null) { open = false; return }
    d += `${open ? 'L' : 'M'}${x(i)} ${y(v)}`
    open = true
  })
  g.append('path').attr('d', d).attr('fill', 'none').attr('stroke', T.defence).attr('stroke-width', 2).attr('stroke-linejoin', 'round')

  frames.forEach((_, i) => {
    const v = k(i)
    if (v === null) {
      g.append('circle').attr('cx', x(i)).attr('cy', y(0)).attr('r', 2).attr('fill', T.canvas).attr('stroke', HAIR_STRONG)
    } else if (k(i - 1) === null && k(i + 1) === null) {
      g.append('circle').attr('cx', x(i)).attr('cy', y(v)).attr('r', 2.5).attr('fill', T.defence)
    }
  })

  if (collapse !== null) {
    let p = collapse - 1
    while (p >= 0 && k(p) === null) p--
    g.append('path')
      .attr('d', `M${x(collapse)} ${M.t - 6}V${H - M.b}`)
      .attr('stroke', T.collapse).attr('stroke-width', 1.25).attr('stroke-dasharray', '3 2')
    const cv = k(collapse)
    if (p >= 0 && cv !== null) {
      g.append('path')
        .attr('d', `M${x(p)} ${y(k(p) as number)}L${x(collapse)} ${y(cv)}`)
        .attr('stroke', T.collapse).attr('stroke-width', 2.5).attr('stroke-linecap', 'round')
    }
    const flip = collapse > n * 0.7
    g.append('text')
      .attr('x', x(collapse) + (flip ? -5 : 5)).attr('y', M.t - 2)
      .attr('text-anchor', flip ? 'end' : 'start')
      .attr('fill', T.collapse).attr('font-weight', 500)
      .text('Collapse')
  }

  svg.append('g').attr('class', 'tl-cursor')
}

export function renderCursor(svg: Svg, frames: FrameData[], index: number, width: number) {
  const { x } = timelineScale(width, frames.length)
  const y = (v: number) => M.t + (1 - v) * (TIMELINE_HEIGHT - M.t - M.b)
  const v = frames[index]?.scores.composite ?? null
  const c = svg.select<SVGGElement>('g.tl-cursor')
  c.selectAll('*').remove()
  c.append('path').attr('d', `M${x(index)} ${M.t}V${TIMELINE_HEIGHT - M.b}`).attr('stroke', T.ink)
  c.append('circle')
    .attr('cx', x(index)).attr('cy', y(v ?? 0)).attr('r', 4.5)
    .attr('fill', v === null ? T.canvas : T.ink)
    .attr('stroke', v === null ? T.ink : T.canvas).attr('stroke-width', 2)
}
