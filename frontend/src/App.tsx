import { useAnalysisStore, selectCurrentFrame } from './stores/analysisStore'
import { BrowsePanel } from './components/BrowsePanel/BrowsePanel'
import { PitchContainer } from './components/Pitch/PitchContainer'
import { FrameStepper } from './components/FrameStepper/FrameStepper'
import { ScorePanel } from './components/ScorePanel/ScorePanel'

export function App() {
  const { sequence, selectedGoal, loading, error } = useAnalysisStore()
  const currentFrame = useAnalysisStore(selectCurrentFrame)

  return (
    <div className="app">
      <header className="app-header">
        <h1 className="app-title">What Went Wrong</h1>
        <p className="app-subtitle">Soccer defensive collapse analyzer</p>
      </header>

      <div className="app-body">
        {/* Left: browse panel */}
        <BrowsePanel />

        {/* Centre: pitch + stepper */}
        <main className="app-main">
          {error && <div className="app-error">{error}</div>}

          {!selectedGoal && !loading && (
            <div className="app-empty">
              <p>Select a competition, match, and goal to begin.</p>
            </div>
          )}

          {loading && !sequence && (
            <div className="app-empty">
              <p>Loading…</p>
            </div>
          )}

          {sequence && (
            <>
              <div className="pitch-wrapper">
                <PitchContainer frame={currentFrame} width={640} />
              </div>
              <FrameStepper />
            </>
          )}
        </main>

        {/* Right: score panel */}
        <aside className="app-aside">
          <ScorePanel />
        </aside>
      </div>
    </div>
  )
}
