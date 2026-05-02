import { useEffect, useRef } from 'react'
import * as d3 from 'd3'
import type { FrameData } from '../../types/frame'
import { renderEmptyPitch, renderPitchFrame } from './pitchRenderer'

// Maintain a 120:80 (3:2) aspect ratio matching StatsBomb pitch dimensions
const ASPECT = 80 / 120

interface Props {
  frame: FrameData | null
  width: number
}

export function PitchContainer({ frame, width }: Props) {
  const height = Math.round(width * ASPECT)
  const svgRef = useRef<SVGSVGElement>(null)

  // Draw empty pitch on mount
  useEffect(() => {
    if (!svgRef.current) return
    const svg = d3.select(svgRef.current)
    renderEmptyPitch(svg, width, height)
  }, [width, height])

  // Re-render when frame changes
  useEffect(() => {
    if (!svgRef.current || !frame) return
    const svg = d3.select(svgRef.current)
    renderPitchFrame(svg, frame, width, height)
  }, [frame, width, height])

  return (
    <svg
      ref={svgRef}
      width={width}
      height={height}
      style={{
        display: 'block',
        background: '#2d5a1b',
        borderRadius: '4px',
        border: '1px solid #1a3d0f',
        overflow: 'hidden',
      }}
    />
  )
}
