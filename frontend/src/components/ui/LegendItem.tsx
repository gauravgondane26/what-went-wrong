import type { CSSProperties, ReactNode } from 'react'

type Swatch = 'dot' | 'ring' | 'ball' | 'cone' | 'gradient' | 'dashed'

interface LegendItemProps {
  swatch: Swatch
  /** CSS colour for dot / cone swatches, e.g. 'var(--color-defence)'. */
  color?: string
  children: ReactNode
}

export function LegendItem({ swatch, color, children }: LegendItemProps) {
  const style: CSSProperties | undefined =
    color && (swatch === 'dot' || swatch === 'cone') ? { background: color } : undefined
  return (
    <li className="legend-item">
      <span className={`legend-swatch legend-swatch--${swatch}`} style={style} aria-hidden="true" />
      <span>{children}</span>
    </li>
  )
}

/** Wrapper list for LegendItems. */
export function Legend({ label, children }: { label: string; children: ReactNode }) {
  return (
    <ul className="legend" aria-label={label}>
      {children}
    </ul>
  )
}
