import { useId, type ReactNode } from 'react'

interface MeterProps {
  label: string
  /** 0–1 */
  value: number
  /** Visible one-sentence explanation (never hidden in a tooltip). */
  description?: ReactNode
  /** Formatted value shown at the right; defaults to a percentage. */
  valueText?: string
  tone?: 'defence' | 'collapse'
}

export function Meter({ label, value, description, valueText, tone = 'defence' }: MeterProps) {
  const id = useId()
  const clamped = Math.min(1, Math.max(0, value))
  const pct = Math.round(clamped * 100)
  const text = valueText ?? `${pct}%`

  return (
    <div className={`meter ${tone === 'collapse' ? 'meter--collapse' : ''}`.trim()}>
      <div className="meter__header">
        <span className="meter__label" id={`${id}-label`}>{label}</span>
        <span className="meter__value" aria-hidden="true">{text}</span>
      </div>
      <div
        className="meter__track"
        role="meter"
        aria-labelledby={`${id}-label`}
        aria-describedby={description ? `${id}-desc` : undefined}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={pct}
        aria-valuetext={text}
      >
        <div className="meter__fill" style={{ transform: `scaleX(${clamped})` }} />
      </div>
      {description && <p className="meter__description" id={`${id}-desc`}>{description}</p>}
    </div>
  )
}
