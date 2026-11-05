import { useMemo, useState } from 'react'
import { useAnalysisStore } from '../../stores/analysisStore'
import type { GoalSummary } from '../../types/frame'
import { FULL_VIEW, sequenceView } from '../../lib/geometry'
import { finding, frameSummary, goalMinute } from '../../lib/copy'
import { usePlayback } from '../../hooks/usePlayback'
import { useSlowFlag } from '../../hooks/useSlowFlag'
import { PitchContainer } from '../Pitch/PitchContainer'
import { DEFAULT_LAYERS, type PitchLayers } from '../Pitch/pitchRenderer'
import type { IncomingAction } from '../Pitch/actionLayer'
import { ShapeTimeline } from '../Timeline/ShapeTimeline'
import { Badge, Button, Callout, Icon } from '../ui'
import { MomentPanel } from './MomentPanel'
import { PitchKey } from './PitchKey'
import { PlayByPlay } from './PlayByPlay'

interface Props {
  onPickGoal: (goal: GoalSummary) => void
  onBack: () => void
}

export function AnalysisView({ onPickGoal, onBack }: Props) {
  const { sequence, selectedGoal, goals, currentFrameIndex, loading, error, setFrameIndex, selectGoal } = useAnalysisStore()
  const { playing, stop, toggle } = usePlayback()
  const [layers, setLayers] = useState<PitchLayers>(DEFAULT_LAYERS)
  const [wholePitch, setWholePitch] = useState(false)
  const slow = useSlowFlag(loading)
  const view = useMemo(() => (sequence ? sequenceView(sequence) : FULL_VIEW), [sequence])
  // The move that broke the defence, drawn on the collapse frame from where it started.
  const cause = useMemo<IncomingAction | null>(() => {
    const c = sequence?.collapse_cause
    if (!sequence || !c?.action || c.action_frame_index === null) return null
    const from = sequence.frames[c.action_frame_index]
    return { action: c.action, fromX: from.ball_x, fromY: from.ball_y }
  }, [sequence])

  if (!sequence || !selectedGoal) {
    return (
      <section className="analysis" aria-busy={loading} aria-live="polite">
        {error ? (
          <Callout tone="warning" title="Couldn't load this goal" live="alert"
            action={<div className="row-gap">
              <Button variant="primary" onClick={() => selectedGoal && selectGoal(selectedGoal)}>Try again</Button>
              <Button variant="secondary" onClick={onBack}>Pick another goal</Button>
            </div>}>
            {error}
          </Callout>
        ) : (
          <div className="analysis-loading">
            <h1>Replaying the move…</h1>
            <p>{slow
              ? 'The server is waking up after a quiet spell. The first goal can take up to a minute; after that it is quick.'
              : 'Loading every event and player position before the goal.'}</p>
            <div className="skeleton skeleton--pitch" />
          </div>
        )}
      </section>
    )
  }

  const frame = sequence.frames[currentFrameIndex]
  const top = finding(sequence, selectedGoal.scoring_team_name)
  const isCollapse = currentFrameIndex === sequence.collapse_frame_index
  const seek = (i: number) => { stop(); setFrameIndex(i) }

  return (
    <section className="analysis" aria-labelledby="analysis-title">
      <div className="title-row">
        <div className="title-text">
          <h1 id="analysis-title">{top.title}{top.clock && <> <span className="tnum">{top.clock}</span></>}</h1>
          <p className="finding">
            {top.body.map((part, i) => (part.strong ? <b key={i}>{part.text}</b> : <span key={i}>{part.text}</span>))}
          </p>
        </div>
        <div className="title-actions">
          {goals.length > 1 && (
            <div className="goal-tabs" role="group" aria-label="Goals in this match">
              {goals.map((g) => (
                <button
                  key={g.goal_event_id}
                  type="button"
                  className="goal-tab"
                  aria-current={g.goal_event_id === selectedGoal.goal_event_id}
                  onClick={() => g.goal_event_id !== selectedGoal.goal_event_id && onPickGoal(g)}
                >
                  <span className="tnum">{goalMinute(g)}</span> {g.scoring_team_name}
                </button>
              ))}
            </div>
          )}
          <Button
            variant="primary"
            onClick={() => sequence.collapse_frame_index !== null && seek(sequence.collapse_frame_index)}
            disabled={sequence.collapse_frame_index === null}
            title={sequence.collapse_frame_index === null ? 'No collapse found in this move' : undefined}
          >
            <Icon name="target" />Jump to the collapse
          </Button>
        </div>
      </div>

      <div className="layout">
        <div className="stage">
          <div className="pitch-card" data-collapse={isCollapse}>
            <div className="pitch-caps">
              <span><Icon name="prev" />{sequence.defending_team_name} defend this goal</span>
              <span>{sequence.attacking_team_name} attack this way<Icon name="next" /></span>
            </div>
            <div className="pitch-wrap">
              <PitchContainer
                frame={frame}
                view={wholePitch ? FULL_VIEW : view}
                layers={layers}
                description={frameSummary(sequence, currentFrameIndex)}
                className="pitch"
                incoming={isCollapse ? cause : null}
              />
              {isCollapse && <Badge tone="collapse" className="pitch-flag">Collapse moment</Badge>}
            </div>
            <PitchKey
              defending={sequence.defending_team_name}
              attacking={sequence.attacking_team_name}
              layers={layers}
              wholePitch={wholePitch}
              onLayer={(k, on) => setLayers((l) => ({ ...l, [k]: on }))}
              onWholePitch={setWholePitch}
            />
          </div>
        </div>

        <aside className="rail" aria-label="This moment">
          <ShapeTimeline
            sequence={sequence}
            index={currentFrameIndex}
            playing={playing}
            onSeek={seek}
            onTogglePlay={toggle}
            onStep={(d) => seek(currentFrameIndex + d)}
          />
          <MomentPanel sequence={sequence} index={currentFrameIndex} />
          <PlayByPlay sequence={sequence} index={currentFrameIndex} onSeek={seek} />
        </aside>
      </div>
      <p className="source">
        Data: StatsBomb open data (360 freeze-frames). Shape score = 40% compactness + 30% goal-side + 30% lanes
        blocked. Moments with fewer than 6 defenders in view aren't scored.
      </p>
    </section>
  )
}
