import type { GoalSequenceResponse } from '../../types/frame'
import { frameGeometry } from '../../lib/geometry'
import { band, biggestDrop, clock, describeEvent, METRICS, pct, previousScored, score100, type MetricKey } from '../../lib/copy'
import { Badge, Callout, Meter } from '../ui'

const BAND_TONE = { Solid: 'defence', Stretched: 'neutral', Broken: 'collapse' } as const

interface Props {
  sequence: GoalSequenceResponse
  index: number
}

/** What is happening at this moment, and how good the defending shape is, in words. */
export function MomentPanel({ sequence: seq, index }: Props) {
  const f = seq.frames[index]
  const s = f.scores
  const geo = frameGeometry(f)
  const isCollapse = index === seq.collapse_frame_index
  const markingCollapse = isCollapse && seq.collapse_kind === 'marking'
  const bd = isCollapse && !markingCollapse ? biggestDrop(seq, index) : null
  const cause = isCollapse ? seq.collapse_cause : null
  const b = band(s.composite)
  const prev = previousScored(seq, index)

  let delta = ''
  let deltaDown = false
  if (s.composite !== null) {
    if (prev < 0) delta = 'First scored moment'
    else {
      const was = score100(seq.frames[prev].scores.composite as number)
      const d = score100(s.composite) - was
      deltaDown = d <= -10
      delta = d === 0 ? 'Same as the moment before' : `${d > 0 ? 'Up' : 'Down'} ${Math.abs(d)} from ${was} the moment before`
    }
  }

  const open = geo.lanes.filter((l) => !l.blocked).length
  const goalSide = geo.defenders.length - geo.upfield.length
  const unitN = Math.min(6, geo.defenders.length)
  const describe: Record<MetricKey, string> = {
    compactness: `How tightly the ${unitN} defenders nearest the ball are grouped.`,
    goal_side_share: `${goalSide} of ${geo.defenders.length} defenders are between the ball and their goal.`,
    cover_shadow_coverage: geo.lanes.length
      ? `${geo.lanes.length - open} of ${geo.lanes.length} passes to a teammate are cut off.`
      : 'No attacker to pass to in view.',
  }

  return (
    <section className="panel moment" aria-labelledby="moment-title">
      <div className="moment-head">
        <span className="moment-clock mono">{clock(f)} · moment {index + 1} of {seq.frames.length}</span>
        <h2 className="moment-what" id="moment-title">{describeEvent(f, seq)}</h2>
      </div>

      <div className="scorebox">
        <div className="big">
          {s.composite === null ? '–' : score100(s.composite)}<small>/100</small>
        </div>
        <div className="scorebox-sub">
          {b ? <Badge tone={BAND_TONE[b]}>{b}</Badge> : <Badge>Not scored</Badge>}
          {delta && <span className={deltaDown ? 'delta delta--down' : 'delta'}>{delta}</span>}
        </div>
      </div>

      {isCollapse && bd && (
        <Callout tone="collapse" title="This is where it broke.">
          The biggest fall in shape score across the move, mostly from {bd.drop.label.toLowerCase()} ({pct(bd.drop.from)} → {pct(bd.drop.to)}).
        </Callout>
      )}
      {markingCollapse && (
        <Callout tone="collapse" title="This is where it broke.">
          {s.unmarked_in_box} {seq.attacking_team_name} {s.unmarked_in_box === 1 ? 'player is' : 'players are'} free in the box
          {cause?.metric_from !== null && cause?.metric_from !== undefined ? `, up from ${cause.metric_from}` : ''}.
          {' '}The shape score didn't fall: a crowded box looks compact even when runners are unmarked.
        </Callout>
      )}
      {!s.reliable && (
        <Callout tone="warning">
          Only {s.defenders_visible} of {seq.defending_team_name}'s outfield players are in camera view, so this
          moment isn't scored. Positions shown are still real.
        </Callout>
      )}

      <div className="meters">
        {METRICS.map((m) => {
          const hot = bd?.drop.key === m.key
          return (
            <Meter
              key={m.key}
              label={m.label}
              value={s[m.key]}
              tone={hot ? 'collapse' : 'defence'}
              description={<>{describe[m.key]}{hot && bd && <b className="meter-drop"> Down from {pct(bd.drop.from)}.</b>}</>}
            />
          )
        })}
      </div>

      <dl className="facts">
        <div className="fact"><dt>Last line</dt><dd><span className="mono">{Math.round(s.line_height)}</span> yd from goal</dd></div>
        <div className="fact"><dt>{seq.defending_team_name} in view</dt><dd><span className="mono">{s.defenders_visible}</span> of 10 outfield</dd></div>
        <div className="fact fact--wide">
          <dt>Free in the box</dt>
          <dd>
            {s.attackers_in_box === 0
              ? `No ${seq.attacking_team_name} player in the box`
              : <><span className="mono">{s.unmarked_in_box}</span> of {s.attackers_in_box} with no defender within 2 yd</>}
          </dd>
        </div>
      </dl>
    </section>
  )
}
