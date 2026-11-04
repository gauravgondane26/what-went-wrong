import { useRef, useState } from 'react'
import { useAnalysisStore } from './stores/analysisStore'
import type { GoalSummary } from './types/frame'
import { goalMinute } from './lib/copy'
import { AppHeader } from './components/Shell/AppHeader'
import { GoalPicker } from './components/Picker/GoalPicker'
import { AnalysisView } from './components/Analysis/AnalysisView'
import { HowToRead } from './components/Analysis/HowToRead'

/**
 * Two views over the existing store: the goal picker (competition → match → goal, opened in place)
 * and the analysis of one goal. Which one shows is UI state only; the store is unchanged.
 */
export function App() {
  const { selectedCompetition, selectedMatch, selectedGoal, selectGoal } = useAnalysisStore()
  const [browsing, setBrowsing] = useState(true)
  const howRef = useRef<HTMLDialogElement>(null)

  const view = !browsing && selectedGoal ? 'analysis' : 'picker'

  const pickGoal = (goal: GoalSummary) => {
    setBrowsing(false)
    window.scrollTo(0, 0)
    void selectGoal(goal)
  }
  const goHome = () => {
    setBrowsing(true)
    window.scrollTo(0, 0)
  }

  const crumbs = view === 'analysis' && selectedMatch && selectedGoal
    ? [
        ...(selectedCompetition ? [{ label: `${selectedCompetition.competition_name} ${selectedCompetition.season_name}` }] : []),
        { label: `${selectedMatch.home_team_name} ${selectedMatch.home_score}–${selectedMatch.away_score} ${selectedMatch.away_team_name}` },
        { label: `${selectedGoal.scoring_team_name} ${goalMinute(selectedGoal)}`, current: true },
      ]
    : []

  return (
    <>
      <a className="skip-link" href="#main">Skip to content</a>
      <AppHeader view={view} crumbs={crumbs} onHome={goHome} onHowTo={() => howRef.current?.showModal()} />
      <main id="main" className="page" tabIndex={-1}>
        {view === 'analysis'
          ? <AnalysisView onPickGoal={pickGoal} onBack={goHome} />
          : <GoalPicker onPickGoal={pickGoal} />}
      </main>
      <HowToRead ref={howRef} />
    </>
  )
}
