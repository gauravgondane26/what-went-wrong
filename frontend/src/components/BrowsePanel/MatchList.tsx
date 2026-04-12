import { useAnalysisStore } from '../../stores/analysisStore'
import type { MatchSummary } from '../../types/frame'

export function MatchList() {
  const {
    matches,
    selectedCompetition,
    selectedMatch,
    selectMatch,
    loading,
  } = useAnalysisStore()

  if (!selectedCompetition) return null

  return (
    <div className="browse-section">
      <h3 className="browse-heading">Match</h3>
      {loading && matches.length === 0 ? (
        <p className="loading">Loading…</p>
      ) : matches.length === 0 ? (
        <p className="empty">No 360-data matches available.</p>
      ) : (
        <ul className="browse-list">
          {matches.map(m => (
            <li
              key={m.match_id}
              className={`browse-item ${m.match_id === selectedMatch?.match_id ? 'selected' : ''}`}
              onClick={() => selectMatch(m)}
            >
              <span className="browse-item-primary">
                {m.home_team_name} {m.home_score}–{m.away_score} {m.away_team_name}
              </span>
              <span className="browse-item-secondary">
                {m.match_date} · {m.competition_stage}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
