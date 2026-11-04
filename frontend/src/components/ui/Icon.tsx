import type { SVGProps } from 'react'

const PATHS = {
  play: <path d="M5 3.5v9l7.5-4.5L5 3.5Z" fill="currentColor" stroke="none" />,
  pause: (
    <>
      <rect x="4" y="3.5" width="2.75" height="9" rx="0.75" fill="currentColor" stroke="none" />
      <rect x="9.25" y="3.5" width="2.75" height="9" rx="0.75" fill="currentColor" stroke="none" />
    </>
  ),
  prev: <path d="M10 3.5 5.5 8l4.5 4.5" />,
  next: <path d="M6 3.5 10.5 8 6 12.5" />,
  chevronDown: <path d="M3.5 6 8 10.5 12.5 6" />,
  info: (
    <>
      <circle cx="8" cy="8" r="6.25" />
      <path d="M8 7.25v4" />
      <circle cx="8" cy="5" r="0.5" fill="currentColor" />
    </>
  ),
  alert: (
    <>
      <path d="M8 1.75 14.75 13.5H1.25L8 1.75Z" strokeLinejoin="round" />
      <path d="M8 6.25v3.5" />
      <circle cx="8" cy="11.5" r="0.5" fill="currentColor" />
    </>
  ),
  close: <path d="M4 4l8 8M12 4l-8 8" />,
  external: (
    <>
      <path d="M9.5 2.5h4v4" />
      <path d="M13.5 2.5 7.5 8.5" />
      <path d="M11.5 9.5v3a1 1 0 0 1-1 1h-7a1 1 0 0 1-1-1v-7a1 1 0 0 1 1-1h3" />
    </>
  ),
  check: <path d="M3.5 8.5 6.5 11.5 12.5 4.5" />,
  target: (
    <>
      <circle cx="8" cy="8" r="6.25" />
      <circle cx="8" cy="8" r="2.5" />
    </>
  ),
} as const

export type IconName = keyof typeof PATHS

interface IconProps extends Omit<SVGProps<SVGSVGElement>, 'name'> {
  name: IconName
  size?: 'md' | 'lg'
  /** Accessible label. Omit for decorative icons (default: aria-hidden). */
  title?: string
}

/** Inline SVG icon set, 16px grid, stroke follows currentColor. */
export function Icon({ name, size = 'md', title, className = '', ...rest }: IconProps) {
  return (
    <svg
      viewBox="0 0 16 16"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.5}
      strokeLinecap="round"
      strokeLinejoin="round"
      className={`icon ${size === 'lg' ? 'icon--lg' : ''} ${className}`.trim()}
      aria-hidden={title ? undefined : true}
      role={title ? 'img' : undefined}
      focusable="false"
      {...rest}
    >
      {title && <title>{title}</title>}
      {PATHS[name]}
    </svg>
  )
}
