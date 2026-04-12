import { useEffect, useCallback } from 'react'
import { useAnalysisStore } from '../../stores/analysisStore'

export function FrameStepper() {
  const {
    sequence,
    currentFrameIndex,
    currentFrame,
    stepBack,
    stepForward,
    setFrameIndex,
  } = useAnalysisStore()

  const totalFrames = sequence?.frames.length ?? 0

  // Keyboard nav: arrow keys
  const handleKey = useCallback(
    (e: KeyboardEvent) => {
      if (!sequence) return
      if (e.key === 'ArrowRight' || e.key === 'ArrowDown') stepForward()
      if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') stepBack()
    },
    [sequence, stepForward, stepBack],
  )

  useEffect(() => {
    window.addEventListener('keydown', handleKey)
    return () => window.removeEventListener('keydown', handleKey)
  }, [handleKey])

  if (!sequence || !currentFrame) return null

  const isFirst = currentFrameIndex === 0
  const isLast = currentFrameIndex === totalFrames - 1
  const isCollapse = currentFrame.is_collapse_frame

  return (
    <div className="frame-stepper">
      {/* Event type badge */}
      <div className="frame-badge-row">
        <span className={`event-badge ${isCollapse ? 'event-badge--collapse' : ''}`}>
          {currentFrame.event_type}
        </span>
        {isCollapse && <span className="collapse-label">⚡ collapse</span>}
        <span className="frame-time">
          {currentFrame.period === 5
            ? 'Shootout'
            : `${currentFrame.minute}:${String(currentFrame.second).padStart(2, '0')}`}
        </span>
      </div>

      {/* Prev / slider / Next */}
      <div className="stepper-controls">
        <button
          className="stepper-btn"
          onClick={stepBack}
          disabled={isFirst}
          aria-label="Previous frame"
        >
          ‹
        </button>

        <input
          type="range"
          className="stepper-slider"
          min={0}
          max={totalFrames - 1}
          value={currentFrameIndex}
          onChange={e => setFrameIndex(Number(e.target.value))}
        />

        <button
          className="stepper-btn"
          onClick={stepForward}
          disabled={isLast}
          aria-label="Next frame"
        >
          ›
        </button>
      </div>

      {/* Frame counter */}
      <div className="frame-counter">
        frame {currentFrameIndex + 1} / {totalFrames}
      </div>

      {/* Timeline dots — one per frame, collapse frame highlighted */}
      <div className="timeline-dots">
        {sequence.frames.map((f, i) => (
          <button
            key={f.event_id}
            className={`timeline-dot
              ${i === currentFrameIndex ? 'timeline-dot--active' : ''}
              ${f.is_collapse_frame ? 'timeline-dot--collapse' : ''}
            `}
            onClick={() => setFrameIndex(i)}
            aria-label={`Frame ${i + 1}: ${f.event_type}`}
            title={`${f.event_type} ${f.minute}'`}
          />
        ))}
      </div>
    </div>
  )
}
