import * as d3 from 'd3'
import { DependencyList, useEffect, useRef } from 'react'

/**
 * React/D3 integration hook.
 *
 * React owns the SVG element (via the returned ref).
 * D3 exclusively owns everything rendered inside it.
 *
 * Usage:
 *   const ref = useD3<SVGSVGElement>(svg => { ... d3 mutations ... }, [dep])
 *   return <svg ref={ref} />
 *
 * The render function re-runs whenever deps change, just like useEffect.
 * D3 transitions work normally inside the render function because D3 is
 * mutating DOM nodes that React never touches after mount.
 */
export function useD3<T extends Element>(
  renderFn: (selection: d3.Selection<T, unknown, null, undefined>) => void,
  deps: DependencyList,
) {
  const ref = useRef<T>(null)

  useEffect(() => {
    if (ref.current) {
      renderFn(d3.select(ref.current) as d3.Selection<T, unknown, null, undefined>)
    }
    // deps are passed through from the caller
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps)

  return ref
}
