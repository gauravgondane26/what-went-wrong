import type { ReactNode } from 'react'
import { Icon, type IconName } from './Icon'

type Tone = 'info' | 'warning' | 'collapse'

const TONE_ICON: Record<Tone, IconName> = {
  info: 'info',
  warning: 'alert',
  collapse: 'target',
}

interface CalloutProps {
  tone?: Tone
  title?: ReactNode
  children?: ReactNode
  action?: ReactNode
  /** 'status' announces politely; 'alert' interrupts (errors only). */
  live?: 'status' | 'alert'
  className?: string
}

export function Callout({ tone = 'info', title, children, action, live, className = '' }: CalloutProps) {
  const toneClass = tone === 'info' ? '' : `callout--${tone}`
  return (
    <div className={`callout ${toneClass} ${className}`.trim()} role={live}>
      <Icon name={TONE_ICON[tone]} className="callout__icon" />
      <div className="callout__body">
        {title && <p className="callout__title">{title}</p>}
        {children && <div>{children}</div>}
        {action && <div className="callout__action">{action}</div>}
      </div>
    </div>
  )
}
