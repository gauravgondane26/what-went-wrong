import { useRef, useEffect } from 'react'
import * as d3 from 'd3'
import type { FrameData } from '../../types/frame'

interface Props {
  frames: FrameData[]
  currentIndex: number
  collapseIndex: number
  width: number
  height: number
}

export function Sparkline({ frames, currentIndex, collapseIndex, width, height }: Props) {
  const svgRef = useRef<SVGSVGElement>(null)

  useEffect(() => {
    if (!svgRef.current) return
    const svg = d3.select(svgRef.current)
    svg.selectAll('*').remove()

    const scores = frames.map(f => f.scores.composite)
    const n = scores.length

    const xScale = d3.scaleLinear([0, n - 1], [8, width - 8])
    const yScale = d3.scaleLinear([0, 1], [height - 6, 6])

    // Line
    const line = d3.line<number>()
      .x((_, i) => xScale(i))
      .y(d => yScale(d))
      .curve(d3.curveMonotoneX)

    svg.append('path')
      .datum(scores)
      .attr('fill', 'none')
      .attr('stroke', '#888')
      .attr('stroke-width', 1.5)
      .attr('d', line)

    // Collapse marker — vertical red line
    svg.append('line')
      .attr('x1', xScale(collapseIndex))
      .attr('x2', xScale(collapseIndex))
      .attr('y1', 4)
      .attr('y2', height - 4)
      .attr('stroke', '#e05c2a')
      .attr('stroke-width', 1.5)
      .attr('stroke-dasharray', '3,2')

    // Current frame dot
    svg.append('circle')
      .attr('cx', xScale(currentIndex))
      .attr('cy', yScale(scores[currentIndex]))
      .attr('r', 3.5)
      .attr('fill', '#ffffff')
      .attr('stroke', '#3a86e8')
      .attr('stroke-width', 1.5)

  }, [frames, currentIndex, collapseIndex, width, height])

  return (
    <svg
      ref={svgRef}
      width={width}
      height={height}
      style={{ display: 'block' }}
    />
  )
}
