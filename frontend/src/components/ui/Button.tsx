import type { ButtonHTMLAttributes, ReactNode } from 'react'
import { Icon, type IconName } from './Icon'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost'
  size?: 'sm' | 'md'
  icon?: IconName
  children: ReactNode
}

export function Button({
  variant = 'secondary',
  size = 'sm',
  icon,
  className = '',
  type = 'button',
  children,
  ...rest
}: ButtonProps) {
  return (
    <button
      type={type}
      className={`btn btn--${variant} ${size === 'md' ? 'btn--md' : ''} ${className}`.trim()}
      {...rest}
    >
      {icon && <Icon name={icon} />}
      {children}
    </button>
  )
}
