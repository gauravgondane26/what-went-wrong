import type { GoalSummary, MatchSummary } from '../../types/frame'
import { goalMinute } from '../../lib/copy'
import { Button, Callout, Icon } from '../ui'

const dateFmt = new Intl.DateTimeFormat(undefined, { day: 'numeric', month: 'short', year: 'numeric' })

interface Props {
  match: MatchSummary
  open: boolean
  goals: GoalSummary[]
  loading: boolean
  slow: boolean
  error: string | null
  onToggle: () => void
  onRetry: () => void
  onPickGoal: (goal: GoalSummary) => void
}

/** One match; opens in place to list its goals, each one click from the analysis. */
export function MatchRow({ match: m, open, goals, loading, slow, error, onToggle, onRetry, onPickGoal }: Props) {
  const homeWon = m.home_score > m.away_score
  const awayWon = m.away_score > m.home_score
  const panelId = `goals-${m.match_id}`

  return (
    <li className="match" data-open={open}>
      <button type="button" className="match-row" aria-expanded={open} aria-controls={panelId} onClick={onToggle}>
        <span className="match-date">{dateFmt.format(new Date(m.match_date))}</span>
        <span className="teams">
          <span className={awayWon ? 'team team--lost' : 'team'}>{m.home_team_name}</span>
          <span className="score">{m.home_score}–{m.away_score}</span>
          <span className={homeWon ? 'team team--lost' : 'team'}>{m.away_team_name}</span>
        </span>
        <Icon name="chevronDown" className="chev" />
      </button>
      {open && (
        <div className="goals" id={panelId}>
          {error ? (
            <Callout tone="warning" title="Couldn't load this match's goals" live="alert"
              action={<Button variant="secondary" onClick={onRetry}>Try again</Button>}>
              {error}
            </Callout>
          ) : loading ? (
            <p className="goals-msg">{slow ? 'Waking the server up… this can take up to a minute.' : 'Loading goals…'}</p>
          ) : goals.length === 0 ? (
            <p className="goals-msg">No goals in this match.</p>
          ) : (
            goals.map((g) => (
              <button key={g.goal_event_id} type="button" className="goal" onClick={() => onPickGoal(g)}>
                <span className="goal-min">{goalMinute(g)}</span>
                <span className="goal-who">
                  <b>{g.scoring_team_name}</b> score against {g.conceding_team_name}
                  <span className="goal-meta">
                    {[g.is_penalty ? 'Penalty' : null, g.xg != null ? `Chance quality ${Math.round(g.xg * 100)}%` : null]
                      .filter(Boolean).join(' · ')}
                  </span>
                </span>
                <span className="goal-go">
                  <span className="goal-go-label">See what went wrong</span>
                  <Icon name="arrowRight" />
                </span>
              </button>
            ))
          )}
        </div>
      )}
    </li>
  )
}
