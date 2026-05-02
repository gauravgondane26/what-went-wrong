import { useAnalysisStore, selectCurrentFrame } from '../../stores/analysisStore'
import { ScoreBar } from './ScoreBar'
import { Sparkline } from './Sparkline'

// line_height is a raw pitch x value (0–60+); normalise to 0–1 for display
const MAX_LINE_HEIGHT = 60

export function ScorePanel() {
  const { sequence, currentFrameIndex } = useAnalysisStore()
  const currentFrame = useAnalysisStore(selectCurrentFrame)

  if (!sequence || !currentFrame) return null

  const { scores } = currentFrame
  const isCollapse = currentFrame.is_collapse_frame

  // line_height: lower = deeper/safer → invert for "shape quality" display
  const lineNorm = Math.max(0, 1 - scores.line_height / MAX_LINE_HEIGHT)

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
          {Math.round(scores.composite * 100)}
        </span>
        {currentFrame.score_delta < -0.01 && (
          <span className="score-delta">
            ▼ {Math.abs(currentFrame.score_delta * 100).toFixed(1)}
          </span>
        )}
      </div>

      {/* Individual metric bars */}
      <ScoreBar
        label="Compactness"
        value={scores.compactness}
        hint="How tightly grouped the defensive unit is. Higher = better."
        highlight={isCollapse}
      />
      <ScoreBar
        label="Line depth"
        value={lineNorm}
        hint="How deep the last line of defense sits. Higher = deeper/safer."
        highlight={isCollapse}
      />
      <ScoreBar
        label="Cover shadows"
        value={scores.cover_shadow_coverage}
        hint="Fraction of attackers with a passing lane blocked. Higher = better."
        highlight={isCollapse}
      />

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
