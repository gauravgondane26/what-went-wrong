import { useEffect, useLayoutEffect, useRef, useState } from 'react'
import * as d3 from 'd3'
import type { GoalSequenceResponse } from '../../types/frame'
import { clock, describeEvent, score100, shortEvent } from '../../lib/copy'
import { IconButton } from '../ui'
import { renderCursor, renderTimeline, timelineScale, TIMELINE_HEIGHT } from './timelineRenderer'

interface Props {
  sequence: GoalSequenceResponse
  index: number
  playing: boolean
  onSeek: (index: number) => void
  onTogglePlay: () => void
  onStep: (delta: number) => void
}

/** The shape score across the move; click, drag or use the arrow keys to move through it. */
export function ShapeTimeline({ sequence, index, playing, onSeek, onTogglePlay, onStep }: Props) {
  const svgRef = useRef<SVGSVGElement>(null)
  const [width, setWidth] = useState(0)
  const [hover, setHover] = useState<number | null>(null)
  const dragging = useRef(false)
  const frames = sequence.frames
  const n = frames.length
  const f = frames[index]

  useLayoutEffect(() => {
    const el = svgRef.current
    if (!el) return
    const ro = new ResizeObserver(([entry]) => setWidth(Math.round(entry.contentRect.width)))
    ro.observe(el)
    return () => ro.disconnect()
  }, [])

  useEffect(() => {
    if (!svgRef.current || !width) return
    renderTimeline(d3.select(svgRef.current), frames, sequence.collapse_frame_index, width)
  }, [frames, sequence.collapse_frame_index, width])

  useEffect(() => {
    if (!svgRef.current || !width) return
    renderCursor(d3.select(svgRef.current), frames, index, width)
  }, [frames, index, width])

  const indexFromEvent = (e: React.PointerEvent) => {
    const rect = e.currentTarget.getBoundingClientRect()
    return timelineScale(width, n).indexAt(e.clientX - rect.left)
  }

  const onKeyDown = (e: React.KeyboardEvent) => {
    const map: Record<string, () => void> = {
      ArrowRight: () => onStep(1), ArrowUp: () => onStep(1),
      ArrowLeft: () => onStep(-1), ArrowDown: () => onStep(-1),
      Home: () => onSeek(0), End: () => onSeek(n - 1),
    }
    const fn = map[e.key]
    if (fn) { e.preventDefault(); fn() }
  }

  const tip = hover !== null && width ? frames[hover] : null
  const scoreText = (i: number) => {
    const k = frames[i].scores.composite
    return k === null ? 'not scored' : String(score100(k))
  }

  return (
    <section className="timeline-card" aria-labelledby="tl-title">
      <div className="tl-head">
        <h2 id="tl-title">Shape score</h2>
        <span className="tl-pos mono" aria-hidden="true">{clock(f)} · {index + 1}/{n}</span>
        <div className="tl-controls">
          <IconButton icon="prev" label="Previous moment" onClick={() => onStep(-1)} disabled={index === 0} />
          <IconButton icon={playing ? 'pause' : 'play'} label={playing ? 'Pause' : 'Play'} variant="primary" onClick={onTogglePlay} />
          <IconButton icon="next" label="Next moment" onClick={() => onStep(1)} disabled={index === n - 1} />
        </div>
      </div>
      <div className="tl-plot">
        <svg
          ref={svgRef}
          className="tl-svg"
          height={TIMELINE_HEIGHT}
          role="slider"
          tabIndex={0}
          aria-labelledby="tl-title"
          aria-valuemin={1}
          aria-valuemax={n}
          aria-valuenow={index + 1}
          aria-valuetext={`Moment ${index + 1} of ${n}, ${clock(f)}, ${describeEvent(f, sequence)}, ${frames[index].scores.composite === null ? 'not scored' : `score ${scoreText(index)}`}`}
          onKeyDown={onKeyDown}
          onPointerDown={(e) => { dragging.current = true; e.currentTarget.setPointerCapture(e.pointerId); onSeek(indexFromEvent(e)) }}
          onPointerMove={(e) => { const i = indexFromEvent(e); setHover(i); if (dragging.current) onSeek(i) }}
          onPointerUp={() => { dragging.current = false }}
          onPointerLeave={() => setHover(null)}
        />
        {tip && hover !== null && (
          <div className="tl-tip" style={{ left: timelineScale(width, n).x(hover) }} aria-hidden="true">
            {clock(tip)} · {shortEvent(tip.event_type)} · {scoreText(hover)}
          </div>
        )}
      </div>
    </section>
  )
}
