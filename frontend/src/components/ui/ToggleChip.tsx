import type { ButtonHTMLAttributes, ReactNode } from 'react'
import { Icon } from './Icon'

interface ToggleChipProps extends Omit<ButtonHTMLAttributes<HTMLButtonElement>, 'onChange'> {
  pressed: boolean
  onPressedChange: (pressed: boolean) => void
  children: ReactNode
}

/** On/off chip, e.g. for pitch overlay toggles. Exposes state via aria-pressed. */
export function ToggleChip({ pressed, onPressedChange, className = '', children, ...rest }: ToggleChipProps) {
  return (
    <button
      type="button"
      className={`chip ${className}`.trim()}
      aria-pressed={pressed}
      onClick={() => onPressedChange(!pressed)}
      {...rest}
    >
      <Icon name="check" className="chip__check" />
      {children}
    </button>
  )
}
