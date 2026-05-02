import { useEffect, useCallback, useState, useRef } from 'react'
import { useAnalysisStore, selectCurrentFrame } from '../../stores/analysisStore'

const PLAY_INTERVAL_MS = 750

export function FrameStepper() {
  const {
    sequence,
    currentFrameIndex,
    stepBack,
    stepForward,
    setFrameIndex,
  } = useAnalysisStore()
  const currentFrame = useAnalysisStore(selectCurrentFrame)

  const totalFrames = sequence?.frames.length ?? 0
  const [isPlaying, setIsPlaying] = useState(false)
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const stopPlayback = useCallback(() => {
    if (intervalRef.current !== null) {
      clearInterval(intervalRef.current)
      intervalRef.current = null
    }
    setIsPlaying(false)
  }, [])

  const startPlayback = useCallback(() => {
    setIsPlaying(true)
    intervalRef.current = setInterval(() => {
      const { currentFrameIndex, sequence } = useAnalysisStore.getState()
      if (!sequence || currentFrameIndex >= sequence.frames.length - 1) {
        stopPlayback()
        return
      }
      useAnalysisStore.getState().stepForward()
    }, PLAY_INTERVAL_MS)
  }, [stopPlayback])

  const togglePlay = useCallback(() => {
    if (isPlaying) stopPlayback()
    else startPlayback()
  }, [isPlaying, startPlayback, stopPlayback])

  // Stop playback when a new sequence loads
  useEffect(() => {
    stopPlayback()
  }, [sequence]) // eslint-disable-line react-hooks/exhaustive-deps

  // Cleanup on unmount
  useEffect(() => () => stopPlayback(), [stopPlayback])

  // Keyboard nav: arrow keys + space to play/pause
  const handleKey = useCallback(
    (e: KeyboardEvent) => {
      if (!sequence) return
      if (e.key === ' ') { e.preventDefault(); togglePlay() }
      if (e.key === 'ArrowRight' || e.key === 'ArrowDown') { stopPlayback(); stepForward() }
      if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') { stopPlayback(); stepBack() }
    },
    [sequence, togglePlay, stopPlayback, stepForward, stepBack],
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
        {isCollapse && <span className="collapse-label">collapse</span>}
        <span className="frame-time">
          {currentFrame.period === 5
            ? 'Shootout'
            : `${currentFrame.minute}:${String(currentFrame.second).padStart(2, '0')}`}
        </span>
      </div>

      {/* Prev / play / slider / Next */}
      <div className="stepper-controls">
        <button
          className="stepper-btn"
          onClick={() => { stopPlayback(); stepBack() }}
          disabled={isFirst || isPlaying}
          aria-label="Previous frame"
        >
          ‹
        </button>

        <button
          className="stepper-btn stepper-btn--play"
          onClick={togglePlay}
          disabled={isLast && !isPlaying}
          aria-label={isPlaying ? 'Pause' : 'Play'}
        >
          {isPlaying ? '⏸' : '▶'}
        </button>

        <input
          type="range"
          className="stepper-slider"
          min={0}
          max={totalFrames - 1}
          value={currentFrameIndex}
          onChange={e => { stopPlayback(); setFrameIndex(Number(e.target.value)) }}
        />

        <button
          className="stepper-btn"
          onClick={() => { stopPlayback(); stepForward() }}
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
