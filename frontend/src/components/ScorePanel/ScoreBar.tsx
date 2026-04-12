interface Props {
  label: string
  value: number      // 0–1
  hint: string       // short description shown on hover
  highlight?: boolean
}

export function ScoreBar({ label, value, hint, highlight = false }: Props) {
  const pct = Math.round(value * 100)

  return (
    <div className={`score-bar ${highlight ? 'score-bar--highlight' : ''}`} title={hint}>
      <div className="score-bar-header">
        <span className="score-bar-label">{label}</span>
        <span className="score-bar-value">{pct}%</span>
      </div>
      <div className="score-bar-track">
        <div
          className="score-bar-fill"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  )
}
