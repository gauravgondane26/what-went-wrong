import { useEffect, useRef } from 'react'
import type { GoalSequenceResponse } from '../../types/frame'
import { clock, eventTeam, score100, shortEvent } from '../../lib/copy'

interface Props {
  sequence: GoalSequenceResponse
  index: number
  onSeek: (index: number) => void
}

/** Every event in the move, in order; the current one marked, the collapse flagged. */
export function PlayByPlay({ sequence: seq, index, onSeek }: Props) {
  const listRef = useRef<HTMLOListElement>(null)

  useEffect(() => {
    const list = listRef.current
    const row = list?.querySelector<HTMLElement>('[aria-current="true"]')
    if (!list || !row) return
    const top = row.offsetTop - list.offsetTop
    if (top < list.scrollTop || top > list.scrollTop + list.clientHeight - 40) list.scrollTop = top - 60
  }, [index])

  return (
    <section className="panel pbp" aria-labelledby="pbp-title">
      <h2 id="pbp-title">Play by play</h2>
      <ol className="pbp-list" ref={listRef}>
        {seq.frames.map((f, i) => {
          const team = eventTeam(f, seq)
          const collapse = i === seq.collapse_frame_index
          return (
            <li key={f.event_id}>
              <button type="button" className="pbp-row" aria-current={i === index} data-collapse={collapse} onClick={() => onSeek(i)}>
                <span className="pbp-clock mono">{clock(f)}</span>
                <span className="pbp-event">
                  {shortEvent(f.event_type)} {team && <span className="pbp-team">{team}</span>}
                  {collapse && <span className="pbp-flag"> · collapse</span>}
                </span>
                <span className="pbp-score mono">{f.scores.composite === null ? '–' : score100(f.scores.composite)}</span>
              </button>
            </li>
          )
        })}
      </ol>
    </section>
  )
}
