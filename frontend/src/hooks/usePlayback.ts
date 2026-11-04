import { useCallback, useEffect, useRef, useState } from 'react'
import { useAnalysisStore } from '../stores/analysisStore'

const PLAY_INTERVAL_MS = 900

/**
 * Play / pause through the sequence with the store's existing actions, plus keyboard shortcuts:
 * ← / → step, Space plays, C jumps to the collapse. Shortcuts are ignored while focus is in a
 * control (buttons, inputs, the timeline slider, dialogs) or a modifier is held, so they never
 * double-step a focused control.
 */
export function usePlayback() {
  const sequence = useAnalysisStore((s) => s.sequence)
  const [playing, setPlaying] = useState(false)
  const timer = useRef<ReturnType<typeof setInterval> | null>(null)

  const stop = useCallback(() => {
    if (timer.current !== null) clearInterval(timer.current)
    timer.current = null
    setPlaying(false)
  }, [])

  const play = useCallback(() => {
    const { sequence: seq, currentFrameIndex, setFrameIndex } = useAnalysisStore.getState()
    if (!seq) return
    if (currentFrameIndex >= seq.frames.length - 1) setFrameIndex(0)
    setPlaying(true)
    timer.current = setInterval(() => {
      const s = useAnalysisStore.getState()
      if (!s.sequence || s.currentFrameIndex >= s.sequence.frames.length - 1) { stop(); return }
      s.stepForward()
    }, PLAY_INTERVAL_MS)
  }, [stop])

  const toggle = useCallback(() => (timer.current ? stop() : play()), [play, stop])

  // A new sequence always starts paused.
  useEffect(() => stop, [sequence, stop])

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement | null
      if (!useAnalysisStore.getState().sequence) return
      if (e.metaKey || e.ctrlKey || e.altKey) return
      if (target?.closest('input, select, textarea, button, a, [role="slider"], dialog')) return
      const s = useAnalysisStore.getState()
      if (e.key === ' ') { e.preventDefault(); toggle() }
      else if (e.key === 'ArrowRight') { stop(); s.stepForward() }
      else if (e.key === 'ArrowLeft') { stop(); s.stepBack() }
      else if (e.key.toLowerCase() === 'c' && s.sequence?.collapse_frame_index != null) {
        stop(); s.setFrameIndex(s.sequence.collapse_frame_index)
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [toggle, stop])

  return { playing, play, stop, toggle }
}
