/**
 * Data-viz theme for the D3 pitch layers. Pure TS, zero React imports.
 *
 * Mirrors the data and pitch colours in src/styles/tokens.css (source: DESIGN.md).
 * Keep the two in sync. Values are duplicated because D3 sets SVG attributes
 * and interpolates them in transitions, which doesn't work with var(--…).
 */
export const PITCH_THEME = {
  pitch: '#f7f8f7',
  line: '#c8c8c8',
  defence: '#1d5fd0',
  defenceDeep: '#174a9f',
  attack: '#171717',
  collapse: '#c4261b',
  ball: '#ffffff',
  ink: '#171717',
  canvas: '#ffffff',
  warning: '#b45309',
  mute: '#6b6b6b',
  fontSans: "Inter, system-ui, -apple-system, 'Segoe UI', sans-serif",
  fontMono: "'JetBrains Mono', ui-monospace, Consolas, monospace",
  durationFrame: 250,
} as const

/** True when the user asked the OS for reduced motion. Safe outside the browser. */
export function prefersReducedMotion(): boolean {
  return typeof window !== 'undefined'
    && typeof window.matchMedia === 'function'
    && window.matchMedia('(prefers-reduced-motion: reduce)').matches
}

/** Frame transition duration, 0 under reduced motion. */
export function frameDuration(): number {
  return prefersReducedMotion() ? 0 : PITCH_THEME.durationFrame
}
