import { forwardRef } from 'react'
import { IconButton } from '../ui'
import { SWATCH } from './PitchKey'

const ITEMS: [keyof typeof SWATCH, string, string][] = [
  ['defender', 'Defender', 'A player on the defending team, in view of the camera.'],
  ['upfield', 'Upfield of the ball', 'A defender who is no longer between the ball and their goal.'],
  ['keeper', 'Goalkeeper', "Drawn as a square in their team's style."],
  ['attacker', 'Attacker', 'A player on the team that scored.'],
  ['actor', 'On the ball', 'The player making this pass, carry, tackle or save.'],
  ['unit', 'Unit around the ball', 'The 6 defenders nearest the ball. A small, tight outline means a compact unit.'],
  ['openLane', 'Open passing lane', 'A pass the player on the ball could make with no defender in the way.'],
  ['blockedLane', 'Blocked passing lane', 'A defender stands in the way of this pass.'],
  ['path', "Ball's path", 'Where the pass, run or shot on the ball goes next (a dotted line is a run with the ball). At the collapse it shows the move that broke the defence instead.'],
  ['line', 'Last line', 'Average position of the 4 deepest defenders.'],
  ['pressure', 'Pressure', 'Ground the defence can reach quickly. Darker means more defenders close by.'],
]

/** Explainer dialog. Opened with ref.current.showModal(); Escape and the close button dismiss it. */
export const HowToRead = forwardRef<HTMLDialogElement>(function HowToRead(_, ref) {
  const close = () => (ref && typeof ref !== 'function' ? ref.current?.close() : undefined)
  return (
    <dialog ref={ref} className="how" aria-labelledby="how-title">
      <IconButton icon="close" label="Close" className="how-close" onClick={close} />
      <h2 id="how-title">How to read the pitch</h2>
      <p>
        The defending team always defends the goal on the left, so every goal reads the same way.
        Blue is the defence. Red marks the moment its shape broke.
      </p>
      <dl className="how-key">
        {ITEMS.map(([k, term, def]) => (
          <div key={k} className="how-row">
            <dt>{SWATCH[k]}<b>{term}</b></dt>
            <dd>{def}</dd>
          </div>
        ))}
      </dl>
      <h3>The shape score</h3>
      <p>
        Each moment gets a score out of 100 built from three measures: how tight the defenders around the
        ball are (40%), how many are goal-side of the ball (30%), and how many passing lanes they cut off
        (30%). 70 and above is solid, 40 to 69 is stretched, under 40 is broken.
      </p>
      <h3>The collapse</h3>
      <p>
        The collapse is the biggest fall in the score across the move, comparing the two moments after each
        step with the two before it. Some goals have none: the shape held, it was already broken, or the
        camera showed too few defenders to judge.
      </p>
      <h3>What the camera can't see</h3>
      <p>
        Positions come from the broadcast picture, so players outside the frame are missing. When fewer than
        6 defenders are in view, the moment isn't scored.
      </p>
    </dialog>
  )
})
