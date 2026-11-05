import { useEffect, useId, useRef } from 'react'
import * as d3 from 'd3'
import type { FrameData } from '../../types/frame'
import type { ViewBox } from '../../lib/geometry'
import { renderPitchFrame, type PitchLayers } from './pitchRenderer'
import type { IncomingAction } from './actionLayer'

interface Props {
  frame: FrameData | null
  view: ViewBox
  layers: PitchLayers
  /** Accessible description of what the pitch shows right now. */
  description: string
  animate?: boolean
  className?: string
  /** On the collapse frame: the action that broke the defence, drawn instead of the frame's own. */
  incoming?: IncomingAction | null
}

/** React owns the <svg>; D3 owns everything inside it. */
export function PitchContainer({ frame, view, layers, description, animate = true, className, incoming = null }: Props) {
  const svgRef = useRef<SVGSVGElement>(null)
  const descId = useId()

  useEffect(() => {
    if (!svgRef.current) return
    renderPitchFrame(d3.select(svgRef.current), frame, view, layers, animate, incoming)
  }, [frame, view, layers, animate, incoming])

  return (
    <svg
      ref={svgRef}
      className={className}
      role="img"
      aria-describedby={descId}
      preserveAspectRatio="xMidYMid meet"
    >
      <desc id={descId}>{description}</desc>
    </svg>
  )
}
