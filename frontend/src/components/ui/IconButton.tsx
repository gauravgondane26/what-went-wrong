import type { ButtonHTMLAttributes } from 'react'
import { Icon, type IconName } from './Icon'

interface IconButtonProps extends Omit<ButtonHTMLAttributes<HTMLButtonElement>, 'children'> {
  icon: IconName
  /** Required: becomes aria-label. */
  label: string
  variant?: 'default' | 'primary'
  size?: 'md' | 'lg'
}

export function IconButton({
  icon,
  label,
  variant = 'default',
  size = 'md',
  className = '',
  type = 'button',
  ...rest
}: IconButtonProps) {
  const classes = [
    'icon-btn',
    variant === 'primary' && 'icon-btn--primary',
    size === 'lg' && 'icon-btn--lg',
    className,
  ].filter(Boolean).join(' ')

  return (
    <button type={type} className={classes} aria-label={label} {...rest}>
      <Icon name={icon} size={size === 'lg' ? 'lg' : 'md'} />
    </button>
  )
}
