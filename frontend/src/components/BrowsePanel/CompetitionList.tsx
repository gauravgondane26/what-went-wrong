import { useEffect } from 'react'
import { useAnalysisStore } from '../../stores/analysisStore'
import type { CompetitionSummary } from '../../types/frame'

export function CompetitionList() {
  const {
    competitions,
    selectedCompetition,
    loadCompetitions,
    selectCompetition,
    loading,
    error,
  } = useAnalysisStore()

  useEffect(() => {
    if (competitions.length === 0) loadCompetitions()
  }, [])

  if (error) return <p className="error">{error}</p>

  return (
    <div className="browse-section">
      <h3 className="browse-heading">Competition</h3>
      {loading && competitions.length === 0 ? (
        <p className="loading">Loading…</p>
      ) : (
        <ul className="browse-list">
          {competitions.map(c => (
            <li
              key={`${c.competition_id}-${c.season_id}`}
              className={`browse-item ${isSelected(c, selectedCompetition) ? 'selected' : ''}`}
              onClick={() => selectCompetition(c)}
            >
              <span className="browse-item-primary">{c.competition_name}</span>
              <span className="browse-item-secondary">
                {c.country_name} · {c.season_name}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

function isSelected(c: CompetitionSummary, selected: CompetitionSummary | null) {
  return (
    selected?.competition_id === c.competition_id &&
    selected?.season_id === c.season_id
  )
}
