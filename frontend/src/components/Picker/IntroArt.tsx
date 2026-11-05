import { useMemo } from 'react'
import { PitchContainer } from '../Pitch/PitchContainer'
import { VIEW_RATIO, type ViewBox } from '../../lib/geometry'
import { INTRO_FRAME } from './introFrame'

const LAYERS = { unit: true, lanes: true, line: true, pressure: false, path: false, unmarked: false }

/** A real collapse moment, cropped to the play: what the analysis will show you. */
export function IntroArt() {
  const view = useMemo<ViewBox>(() => {
    const xs = INTRO_FRAME.players.map((p) => p.x).concat(INTRO_FRAME.ball_x)
    const ys = INTRO_FRAME.players.map((p) => p.y).concat(INTRO_FRAME.ball_y)
    const x0 = Math.min(...xs) - 7
    const w = Math.max(Math.max(...xs) + 7 - x0, (Math.max(...ys) - Math.min(...ys) + 14) * VIEW_RATIO)
    const h = w / VIEW_RATIO
    return { x: Math.max(-4, x0), y: (Math.min(...ys) + Math.max(...ys)) / 2 - h / 2, w, h }
  }, [])

  return (
    <figure className="intro-art">
      <PitchContainer
        frame={INTRO_FRAME}
        view={view}
        layers={LAYERS}
        animate={false}
        className="intro-pitch"
        description="Example: Russia's defence at 78:42 against Denmark at Euro 2020. All six defenders near the ball are caught upfield of it."
      />
      <figcaption>Russia v Denmark, 78:42. Every Russian near the ball is caught upfield of it.</figcaption>
    </figure>
  )
}
