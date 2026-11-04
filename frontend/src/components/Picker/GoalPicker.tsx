import { useEffect, useMemo, useState } from 'react'
import { useAnalysisStore } from '../../stores/analysisStore'
import type { CompetitionSummary, GoalSummary, MatchSummary } from '../../types/frame'
import { Button, Callout, Icon } from '../ui'
import { IntroArt } from './IntroArt'
import { MatchRow } from './MatchRow'
import { useSlowFlag } from '../../hooks/useSlowFlag'

/** Euro 2020 opens by default and hosts the example goal (Denmark's 4th v Russia, 78'). */
const DEFAULT_COMP = { competition_id: 55, season_id: 43 }
const EXAMPLE = { match_id: 3788769, goal_event_id: '3440b2d2-93e7-4ca4-9b31-cc5a0f762b7d' }
const STAGE_ORDER = ['Final', 'Semi-finals', 'Quarter-finals', 'Round of 16', 'Group Stage']

const compKey = (c: Pick<CompetitionSummary, 'competition_id' | 'season_id'>) => `${c.competition_id}-${c.season_id}`
const sentence = (s: string) => s.charAt(0) + s.slice(1).toLowerCase()

interface Props {
  onPickGoal: (goal: GoalSummary) => void
}

export function GoalPicker({ onPickGoal }: Props) {
  const {
    competitions, matches, goals, selectedCompetition, selectedMatch, loading, error,
    loadCompetitions, selectCompetition, selectMatch,
  } = useAnalysisStore()
  const [query, setQuery] = useState('')
  const [stage, setStage] = useState('All')
  const [openMatch, setOpenMatch] = useState<number | null>(selectedMatch?.match_id ?? null)
  const slow = useSlowFlag(loading)

  // First visit: load competitions, then open the default one.
  useEffect(() => {
    if (competitions.length === 0 && !loading && !error) void loadCompetitions()
  }, [competitions.length, loading, error, loadCompetitions])
  useEffect(() => {
    if (selectedCompetition || competitions.length === 0) return
    const def = competitions.find((c) => compKey(c) === compKey(DEFAULT_COMP)) ?? competitions[0]
    void selectCompetition(def)
  }, [competitions, selectedCompetition, selectCompetition])

  const stages = useMemo(() => {
    const present = [...new Set(matches.map((m) => m.competition_stage))].sort()
    const known = STAGE_ORDER.filter((s) => present.includes(s))
    return [...known, ...present.filter((s) => !known.includes(s))]
  }, [matches])

  const q = query.trim().toLowerCase()
  const shown = matches.filter((m) =>
    (stage === 'All' || m.competition_stage === stage) &&
    (!q || `${m.home_team_name} ${m.away_team_name}`.toLowerCase().includes(q)))

  const toggleMatch = (m: MatchSummary) => {
    if (openMatch === m.match_id) { setOpenMatch(null); return }
    setOpenMatch(m.match_id)
    if (selectedMatch?.match_id !== m.match_id) void selectMatch(m)
  }

  const showExample = async () => {
    const comp = competitions.find((c) => compKey(c) === compKey(DEFAULT_COMP))
    if (!comp) return
    if (!selectedCompetition || compKey(selectedCompetition) !== compKey(comp)) await selectCompetition(comp)
    const match = useAnalysisStore.getState().matches.find((m) => m.match_id === EXAMPLE.match_id)
    if (!match) return
    setOpenMatch(match.match_id)
    if (useAnalysisStore.getState().selectedMatch?.match_id !== match.match_id) await selectMatch(match)
    const goal = useAnalysisStore.getState().goals.find((g) => g.goal_event_id === EXAMPLE.goal_event_id)
    if (goal) onPickGoal(goal)
  }

  const retry = () => {
    if (competitions.length === 0) void loadCompetitions()
    else if (selectedMatch && openMatch === selectedMatch.match_id) void selectMatch(selectedMatch)
    else if (selectedCompetition) void selectCompetition(selectedCompetition)
  }

  const hasExample = competitions.some((c) => compKey(c) === compKey(DEFAULT_COMP))

  return (
    <section className="picker" aria-labelledby="picker-title">
      <div className="intro">
        <div className="intro-copy">
          <h1 id="picker-title">Find the moment a defence broke.</h1>
          <p>
            Pick a goal. We replay every pass, carry and tackle that led to it, score the defending
            team's shape at each moment, and point to where it fell apart.
          </p>
          {hasExample && (
            <div className="intro-cta">
              <Button variant="primary" size="md" onClick={showExample} disabled={loading}>Show an example goal</Button>
            </div>
          )}
        </div>
        <IntroArt />
      </div>

      <div className="finder">
        <div className="finder-head">
          <label className="field field--select">
            <span className="sr-only">Competition</span>
            <select
              className="select"
              name="competition"
              autoComplete="off"
              value={selectedCompetition ? compKey(selectedCompetition) : ''}
              onChange={(e) => {
                const c = competitions.find((x) => compKey(x) === e.target.value)
                if (c) { setOpenMatch(null); setStage('All'); void selectCompetition(c) }
              }}
              disabled={competitions.length === 0}
            >
              {competitions.length === 0 && <option value="">Loading competitions…</option>}
              {competitions.map((c) => (
                <option key={compKey(c)} value={compKey(c)}>{c.competition_name} {c.season_name}</option>
              ))}
            </select>
            <Icon name="chevronDown" className="field-icon field-icon--end" />
          </label>
          <label className="field field--search">
            <span className="sr-only">Find a team</span>
            <Icon name="search" className="field-icon" />
            <input
              className="search"
              type="search"
              name="team"
              placeholder="Find a team…"
              autoComplete="off"
              spellCheck={false}
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
          </label>
          {stages.length > 1 && (
            <div className="stage-tabs" role="group" aria-label="Stage">
              {['All', ...stages].map((s) => (
                <button key={s} type="button" className="tab" aria-pressed={stage === s} onClick={() => setStage(s)}>
                  {s === 'All' ? 'All' : sentence(s)}
                </button>
              ))}
            </div>
          )}
        </div>

        <div aria-live="polite" aria-busy={loading}>
          {error && !openMatch && (
            <div className="finder-msg">
              <Callout tone="warning" title="Couldn't load the matches" live="alert"
                action={<Button variant="secondary" onClick={retry}>Try again</Button>}>
                {error}. The server may be starting up; try again in a moment.
              </Callout>
            </div>
          )}
          {!error && loading && matches.length === 0 && (
            <p className="empty">{slow ? 'Waking the server up… this can take up to a minute.' : 'Loading matches…'}</p>
          )}
          {!loading && !error && matches.length > 0 && shown.length === 0 && (
            <p className="empty">No matches for “{query}”. Try a country or club name, like “Denmark”.</p>
          )}
          {groupByStage(shown, stages).map(([st, ms]) => (
            <div key={st}>
              <h2 className="group-h">{sentence(st)} · {ms.length} {ms.length === 1 ? 'match' : 'matches'}</h2>
              <ul>
                {ms.map((m) => {
                  const open = openMatch === m.match_id
                  const mine = selectedMatch?.match_id === m.match_id
                  return (
                    <MatchRow
                      key={m.match_id}
                      match={m}
                      open={open}
                      goals={open && mine ? goals : []}
                      loading={open && (!mine || (loading && goals.length === 0))}
                      slow={slow}
                      error={open && mine ? error : null}
                      onToggle={() => toggleMatch(m)}
                      onRetry={retry}
                      onPickGoal={onPickGoal}
                    />
                  )
                })}
              </ul>
            </div>
          ))}
        </div>
      </div>
      <p className="source">
        Data: StatsBomb open data with 360 freeze-frames. Only the players the broadcast camera could see are known at each moment.
      </p>
    </section>
  )
}

function groupByStage(matches: MatchSummary[], stages: string[]): [string, MatchSummary[]][] {
  return stages
    .map((s) => [s, matches.filter((m) => m.competition_stage === s).sort((a, b) => b.match_date.localeCompare(a.match_date))] as [string, MatchSummary[]])
    .filter(([, ms]) => ms.length > 0)
}
