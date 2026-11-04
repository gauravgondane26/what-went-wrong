import type { HTMLAttributes, ReactNode } from 'react'

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  tone?: 'neutral' | 'defence' | 'collapse' | 'warning'
  children: ReactNode
}

export function Badge({ tone = 'neutral', className = '', children, ...rest }: BadgeProps) {
  const toneClass = tone === 'neutral' ? '' : `badge--${tone}`
  return (
    <span className={`badge ${toneClass} ${className}`.trim()} {...rest}>
      {children}
    </span>
  )
}
