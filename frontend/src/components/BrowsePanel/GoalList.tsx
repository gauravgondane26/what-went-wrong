import { useAnalysisStore } from '../../stores/analysisStore'

export function GoalList() {
  const {
    goals,
    selectedMatch,
    selectedGoal,
    selectGoal,
    loading,
  } = useAnalysisStore()

  if (!selectedMatch) return null

  return (
    <div className="browse-section">
      <h3 className="browse-heading">Goal</h3>
      {loading && goals.length === 0 ? (
        <p className="loading">Loading…</p>
      ) : goals.length === 0 ? (
        <p className="empty">No goals found.</p>
      ) : (
        <ul className="browse-list">
          {goals.map(g => (
            <li
              key={g.goal_event_id}
              className={`browse-item ${g.goal_event_id === selectedGoal?.goal_event_id ? 'selected' : ''}`}
              onClick={() => selectGoal(g)}
            >
              <span className="browse-item-primary">
                {g.scoring_team_name}
                {g.is_penalty && <span className="badge">PEN</span>}
                <span className="browse-item-minute">
                  {g.period === 5 ? 'Shootout' : `${g.minute}'`}
                </span>
              </span>
              <span className="browse-item-secondary">
                vs {g.conceding_team_name}
                {g.xg != null && ` · xG ${g.xg.toFixed(2)}`}
                {` · ${g.sequence_length} events`}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
