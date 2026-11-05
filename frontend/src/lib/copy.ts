/**
 * Words for the analysis screen: plain-language events, score bands and the headline finding.
 * Pure functions over the existing DTOs; nothing here fetches or stores anything.
 */
import type {
  CauseMetric,
  CollapseCause,
  FrameAction,
  FrameData,
  GoalSequenceResponse,
  GoalSummary,
} from '../types/frame'
import { frameGeometry } from './geometry'

export type Band = 'Solid' | 'Stretched' | 'Broken'

export function band(composite: number | null): Band | null {
  if (composite === null) return null
  if (composite >= 0.7) return 'Solid'
  if (composite >= 0.4) return 'Stretched'
  return 'Broken'
}

export const score100 = (v: number) => Math.round(v * 100)
export const pct = (v: number) => `${Math.round(v * 100)}%`

export function clock(f: Pick<FrameData, 'minute' | 'second' | 'period'>): string {
  return f.period === 5 ? 'Shootout' : `${f.minute}:${String(f.second).padStart(2, '0')}`
}

export function goalMinute(g: Pick<GoalSummary, 'minute' | 'period'>): string {
  return g.period === 5 ? 'Pens' : `${g.minute}′`
}

const EVENT_PHRASE: Record<string, (team: string) => string> = {
  'Pass': (t) => `${t} play a pass`,
  'Ball Receipt*': (t) => `${t} receive the ball`,
  'Carry': (t) => `${t} carry the ball`,
  'Pressure': (t) => `${t} close down the ball`,
  'Shot': (t) => `${t} shoot`,
  'Goal Keeper': (t) => `${t}'s keeper deals with it`,
  'Ball Recovery': (t) => `${t} win the ball back`,
  'Clearance': (t) => `${t} clear the ball`,
  'Duel': (t) => `${t} contest a duel`,
  'Dribble': (t) => `${t} take a player on`,
  'Interception': (t) => `${t} intercept`,
  'Block': (t) => `${t} block`,
  'Foul Committed': (t) => `${t} commit a foul`,
  'Foul Won': (t) => `${t} win a foul`,
  'Dispossessed': (t) => `${t} lose the ball`,
  'Miscontrol': (t) => `${t} miscontrol the ball`,
  'Dribbled Past': (t) => `${t} get dribbled past`,
}

const EVENT_SHORT: Record<string, string> = {
  'Ball Receipt*': 'Receives',
  'Goal Keeper': 'Keeper',
  'Ball Recovery': 'Recovery',
  'Foul Committed': 'Foul',
  'Foul Won': 'Foul won',
  'Dribbled Past': 'Beaten',
}

export const shortEvent = (type: string) => EVENT_SHORT[type] ?? type.replace('*', '')

/** Which team made this event, from the actor flag. Null when the actor is out of shot. */
export function eventTeam(frame: FrameData, seq: GoalSequenceResponse): string | null {
  const actor = frame.players.find((p) => p.actor)
  if (!actor) return null
  return actor.is_attacker ? seq.attacking_team_name : seq.defending_team_name
}

export function describeEvent(frame: FrameData, seq: GoalSequenceResponse): string {
  const team = eventTeam(frame, seq)
  const type = frame.event_type.replace('*', '')
  if (!team) return `${type} (player out of shot)`
  const phrase = EVENT_PHRASE[frame.event_type]
  return phrase ? phrase(team) : `${team}: ${type.toLowerCase()}`
}

export const METRICS = [
  { key: 'compactness', label: 'Compactness' },
  { key: 'goal_side_share', label: 'Goal-side' },
  { key: 'cover_shadow_coverage', label: 'Lanes blocked' },
] as const

export type MetricKey = (typeof METRICS)[number]['key']

export interface MetricDrop {
  key: MetricKey
  label: string
  from: number
  to: number
}

/** Index of the nearest earlier frame that has a composite score, or -1. */
export function previousScored(seq: GoalSequenceResponse, index: number): number {
  for (let i = index - 1; i >= 0; i--) if (seq.frames[i].scores.composite !== null) return i
  return -1
}

/** At the collapse: the metric that fell furthest since the previous scored moment. */
export function biggestDrop(seq: GoalSequenceResponse, index: number): { prevIndex: number; drop: MetricDrop } | null {
  const p = previousScored(seq, index)
  if (p < 0) return null
  const a = seq.frames[p].scores
  const b = seq.frames[index].scores
  const drops = METRICS.map((m) => ({ key: m.key, label: m.label, from: a[m.key], to: b[m.key] }))
  drops.sort((x, y) => (x.to - x.from) - (y.to - y.from))
  return { prevIndex: p, drop: drops[0] }
}

/** "A cross", "A through ball", "A corner", "A run with the ball", ... */
export function actionPhrase(a: FrameAction): string {
  if (a.kind === 'Pass') {
    if (a.set_piece) return a.set_piece === 'Kick Off' ? 'The kick-off' : `A ${a.set_piece.toLowerCase()}`
    if (a.cross) return 'A cross'
    if (a.through_ball) return 'A through ball'
    if (a.cut_back) return 'A cut-back'
    if (a.switch) return 'A switch of play'
    if (a.height === 'High Pass') return 'A high ball'
    return 'A pass'
  }
  if (a.kind === 'Carry') return 'A run with the ball'
  if (a.kind === 'Dribble') return 'A take-on'
  return 'A shot'
}

const SHAPE_CONSEQUENCE: Record<Exclude<CauseMetric, 'unmarked_in_box'>, { effect: (def: string) => string; label: string }> = {
  goal_side_share: { effect: (def) => `left ${def} defenders on the wrong side of the ball`, label: 'goal-side' },
  cover_shadow_coverage: { effect: () => 'opened up passing lanes', label: 'lanes blocked' },
  compactness: { effect: (def) => `pulled ${def}'s unit apart`, label: 'compactness' },
}

/** "A cross from Denmark", or just "A cross" when the passer is out of shot. */
function causeSubject(cause: CollapseCause, seq: GoalSequenceResponse): string | null {
  if (!cause.action || cause.action_frame_index === null) return null
  const team = eventTeam(seq.frames[cause.action_frame_index], seq)
  const phrase = actionPhrase(cause.action)
  return team ? `${phrase} from ${team}` : phrase
}

export interface Finding {
  /** Headline text; `clock` is set when the headline ends in a match time. */
  title: string
  clock?: string
  body: { text: string; strong?: boolean }[]
}

/** The screen's answer: when (or whether) the defence's shape broke. */
export function finding(seq: GoalSequenceResponse, scorer: string): Finding {
  const def = seq.defending_team_name
  const c = seq.collapse_frame_index
  const n = seq.frames.length
  if (c !== null) {
    const f = seq.frames[c]
    const after = n - 1 - c
    const body: Finding['body'] = [
      { text: `${scorer} scored ${after === 0 ? 'from this moment' : `${after} ${after === 1 ? 'moment' : 'moments'} later`}. ` },
    ]
    const cause = seq.collapse_cause
    const subject = cause ? causeSubject(cause, seq) : null

    if (cause?.kind === 'marking') {
      const to = cause.metric_to ?? f.scores.unmarked_in_box
      const from = cause.metric_from
      body.push(
        { text: `${subject ?? 'The move'} left ` }, { text: String(to), strong: true },
        { text: ` ${seq.attacking_team_name} ${to === 1 ? 'player' : 'players'} unmarked in the box, with no ${def} defender within 2 yards` },
        { text: from === null ? '.' : `, up from ${from}.` },
      )
      if (f.scores.composite !== null) {
        body.push(
          { text: ' The shape score held at ' }, { text: String(score100(f.scores.composite)), strong: true },
          { text: ': a crowded box looks compact even when runners are free.' },
        )
      }
      return { title: `${def} lost the runners in the box at`, clock: clock(f), body }
    }

    if (subject && cause?.metric && cause.metric !== 'unmarked_in_box' && cause.metric_from !== null && cause.metric_to !== null) {
      const m = SHAPE_CONSEQUENCE[cause.metric]
      body.push(
        { text: `${subject} ${m.effect(def)} (${m.label} ` },
        { text: `${pct(cause.metric_from)} → ${pct(cause.metric_to)}`, strong: true },
        { text: '). ' },
      )
      if (cause.compared_to_index !== null && f.scores.composite !== null) {
        const prev = seq.frames[cause.compared_to_index].scores.composite as number
        body.push(
          { text: 'The shape score fell from ' }, { text: String(score100(prev)), strong: true },
          { text: ' to ' }, { text: String(score100(f.scores.composite)), strong: true }, { text: '.' },
        )
      }
      return { title: `${def}'s shape broke at`, clock: clock(f), body }
    }

    const bd = biggestDrop(seq, c)
    if (bd && f.scores.composite !== null) {
      const prev = seq.frames[bd.prevIndex].scores.composite as number
      body.push(
        { text: 'The shape score fell from ' }, { text: String(score100(prev)), strong: true },
        { text: ' to ' }, { text: String(score100(f.scores.composite)), strong: true },
        { text: ` as ${describeEvent(f, seq)}. Biggest drop: ` }, { text: bd.drop.label.toLowerCase(), strong: true },
        { text: `, ${pct(bd.drop.from)} → ${pct(bd.drop.to)}.` },
      )
    }
    return { title: `${def}'s shape broke at`, clock: clock(f), body }
  }
  const ks = seq.frames.filter((f) => f.scores.composite !== null).map((f) => score100(f.scores.composite as number))
  if (ks.length < 2) {
    return {
      title: `Too little of ${def}'s defence in view to judge`,
      body: [{ text: `The camera showed fewer than 6 ${def} outfield players for most of this move, so ${ks.length === 0 ? 'no moment' : 'only one moment'} could be scored. You can still replay where everyone was.` }],
    }
  }
  const lo = Math.min(...ks)
  const hi = Math.max(...ks)
  const mean = ks.reduce((a, b) => a + b, 0) / ks.length
  const range = lo === hi ? `${lo}` : `${lo} and ${hi}`
  if (mean < 40) {
    return {
      title: `${def}'s shape was broken from the start`,
      body: [{ text: `There was no single collapse: the shape score stayed between ${range} out of 100 across the ${ks.length} scored moments, already in the broken range when this move began.` }],
    }
  }
  if (mean >= 70) {
    return {
      title: `${def}'s shape held until the goal`,
      body: [{ text: `The shape score stayed between ${range} out of 100 with no clear fall. ${scorer} found a way through a defence that was still in position.` }],
    }
  }
  return {
    title: `${def}'s shape stayed stretched, with no single collapse`,
    body: [{ text: `The shape score moved between ${range} out of 100 across the ${ks.length} scored moments without one clear fall.` }],
  }
}

/** Screen-reader summary of one frame. */
export function frameSummary(seq: GoalSequenceResponse, index: number): string {
  const f = seq.frames[index]
  const g = frameGeometry(f)
  const open = g.lanes.filter((l) => !l.blocked).length
  const score = f.scores.composite === null ? 'Not scored' : `Shape score ${score100(f.scores.composite)}`
  return `Moment ${index + 1} of ${seq.frames.length}, ${clock(f)}. ${describeEvent(f, seq)}. ` +
    `${f.scores.defenders_visible} ${seq.defending_team_name} outfield players in view. ${score}. ` +
    `${open} open passing ${open === 1 ? 'lane' : 'lanes'}.`
}
