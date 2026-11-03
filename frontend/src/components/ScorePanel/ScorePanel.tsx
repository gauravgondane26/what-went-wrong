import { useAnalysisStore, selectCurrentFrame } from '../../stores/analysisStore'
import { ScoreBar } from './ScoreBar'
import { Sparkline } from './Sparkline'

export function ScorePanel() {
  const { sequence, currentFrameIndex } = useAnalysisStore()
  const currentFrame = useAnalysisStore(selectCurrentFrame)

  if (!sequence || !currentFrame) return null

  const { scores } = currentFrame
  const isCollapse = currentFrame.is_collapse_frame

  return (
    <div className={`score-panel ${isCollapse ? 'score-panel--collapse' : ''}`}>
      <h3 className="score-panel-heading">
        Defensive Shape
        {isCollapse && <span className="collapse-badge">collapse point</span>}
      </h3>

      {/* Composite score — prominent */}
      <div className="composite-score">
        <span className="composite-score-label">Composite</span>
        <span className="composite-score-value">
          {scores.composite === null ? '–' : Math.round(scores.composite * 100)}
        </span>
        {currentFrame.score_delta !== null && currentFrame.score_delta < -0.01 && (
          <span className="score-delta">
            ▼ {Math.abs(currentFrame.score_delta * 100).toFixed(1)}
          </span>
        )}
      </div>
      {!scores.reliable && (
        <p className="score-unreliable">
          Only {scores.defenders_visible} defenders in view — not enough to score the shape.
        </p>
      )}

      {/* Individual metric bars */}
      <ScoreBar
        label="Compactness"
        value={scores.compactness}
        hint="How tightly grouped the 6 defenders nearest the ball are. Higher = better."
        highlight={isCollapse}
      />
      <ScoreBar
        label="Goal-side"
        value={scores.goal_side_share}
        hint="Share of visible defenders between the ball and their own goal. Higher = better."
        highlight={isCollapse}
      />
      <ScoreBar
        label="Cover shadows"
        value={scores.cover_shadow_coverage}
        hint="Fraction of attackers (excluding the ball carrier and keeper) with the passing lane blocked. Higher = better."
        highlight={isCollapse}
      />
      <p className="score-info" title="Average x of the 4 deepest visible defenders, in pitch units from their own goal (0–120). Shown for reference; not part of the composite.">
        Last line: {scores.line_height.toFixed(0)} units from goal
      </p>

      {/* Sparkline */}
      <div className="sparkline-wrapper">
        <span className="sparkline-label">Shape over sequence</span>
        <Sparkline
          frames={sequence.frames}
          currentIndex={currentFrameIndex}
          collapseIndex={sequence.collapse_frame_index}
          width={220}
          height={48}
        />
        <div className="sparkline-legend">
          <span className="sparkline-legend-item sparkline-legend-item--collapse">
            ╌ collapse
          </span>
          <span className="sparkline-legend-item sparkline-legend-item--current">
            ● current
          </span>
        </div>
      </div>
    </div>
  )
}
