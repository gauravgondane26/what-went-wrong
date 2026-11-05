import type { ReactNode } from 'react'
import type { PitchLayers } from '../Pitch/pitchRenderer'
import { ToggleChip } from '../ui'

/**
 * Legend swatches, drawn as the marks themselves at small size. Colours come from the CSS tokens
 * so the key and the D3 layers stay in step (both mirror DESIGN.md).
 */
const D = 'var(--color-defence)'
const DS = 'var(--color-defence-soft)'
const INK = 'var(--color-ink)'
const W = 'var(--color-canvas)'
const MUTE = 'var(--color-mute)'

const sw = (children: ReactNode) => <svg viewBox="0 0 18 14" className="key-swatch" aria-hidden="true">{children}</svg>

export const SWATCH = {
  defender: sw(<circle cx="9" cy="7" r="5" fill={D} stroke={W} strokeWidth="1.5" />),
  upfield: sw(<circle cx="9" cy="7" r="4.5" fill={DS} stroke={D} strokeWidth="1.5" />),
  attacker: sw(<circle cx="9" cy="7" r="4.5" fill={W} stroke={INK} strokeWidth="2" />),
  keeper: sw(<rect x="4" y="2" width="10" height="10" rx="2.5" fill={D} stroke={W} strokeWidth="1.5" />),
  actor: sw(<><circle cx="9" cy="7" r="3.5" fill={MUTE} /><circle cx="9" cy="7" r="6" fill="none" stroke={INK} strokeWidth="1.25" /></>),
  ball: sw(<circle cx="9" cy="7" r="3.5" fill={W} stroke={INK} strokeWidth="1.5" />),
  unit: sw(<path d="M2 9 7 2l9 3-2 7H5z" fill={D} fillOpacity=".12" stroke={D} strokeWidth="1.25" strokeLinejoin="round" />),
  openLane: sw(<path d="M1 11 17 3" stroke={INK} strokeWidth="1.5" strokeDasharray="3 2.5" strokeLinecap="round" />),
  blockedLane: sw(<path d="M1 11 17 3" stroke={D} strokeOpacity=".45" strokeWidth="1.5" strokeLinecap="round" />),
  lanes: sw(<><path d="M1 9 17 1" stroke={INK} strokeWidth="1.5" strokeDasharray="3 2.5" strokeLinecap="round" /><path d="M1 13 17 5" stroke={D} strokeOpacity=".45" strokeWidth="1.5" strokeLinecap="round" /></>),
  line: sw(<path d="M9 0v14" stroke={D} strokeWidth="1.5" strokeDasharray="2.5 2" />),
  path: sw(<><path d="M1 11 13 4" stroke={INK} strokeWidth="1.75" strokeLinecap="round" /><path d="M17 2 11.2 2.6 13.6 6.7Z" fill={INK} /></>),
  pressure: sw(<><rect x="0" y="1" width="6" height="12" fill={D} fillOpacity=".08" /><rect x="6" y="1" width="6" height="12" fill={D} fillOpacity=".2" /><rect x="12" y="1" width="6" height="12" fill={D} fillOpacity=".34" /></>),
  whole: sw(<><rect x="1" y="2" width="16" height="10" rx="1" fill="none" stroke={MUTE} strokeWidth="1.25" /><path d="M9 2v10" stroke={MUTE} strokeWidth="1.25" /></>),
}

interface Props {
  defending: string
  attacking: string
  layers: PitchLayers
  wholePitch: boolean
  onLayer: (key: keyof PitchLayers, on: boolean) => void
  onWholePitch: (on: boolean) => void
}

/** Static marks first, then each overlay's toggle doubling as its legend entry. */
export function PitchKey({ defending, attacking, layers, wholePitch, onLayer, onWholePitch }: Props) {
  const chip = (key: keyof PitchLayers, label: string, swatch: ReactNode) => (
    <li>
      <ToggleChip pressed={layers[key]} onPressedChange={(on) => onLayer(key, on)} leading={swatch}>{label}</ToggleChip>
    </li>
  )
  return (
    <ul className="key" aria-label="Pitch key and layers">
      <li className="key-item">{SWATCH.defender}{defending}</li>
      <li className="key-item">{SWATCH.upfield}Upfield of the ball</li>
      <li className="key-item">{SWATCH.attacker}{attacking}</li>
      <li className="key-item">{SWATCH.actor}On the ball</li>
      <li className="key-sep" aria-hidden="true" />
      {chip('unit', 'Unit around the ball', SWATCH.unit)}
      {chip('lanes', 'Passing lanes', SWATCH.lanes)}
      {chip('path', "Ball's path", SWATCH.path)}
      {chip('line', 'Last line', SWATCH.line)}
      {chip('pressure', 'Pressure', SWATCH.pressure)}
      <li>
        <ToggleChip pressed={wholePitch} onPressedChange={onWholePitch} leading={SWATCH.whole}>Whole pitch</ToggleChip>
      </li>
    </ul>
  )
}
