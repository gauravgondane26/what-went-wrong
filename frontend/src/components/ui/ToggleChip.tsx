import type { ButtonHTMLAttributes, ReactNode } from 'react'
import { Icon } from './Icon'

interface ToggleChipProps extends Omit<ButtonHTMLAttributes<HTMLButtonElement>, 'onChange'> {
  pressed: boolean
  onPressedChange: (pressed: boolean) => void
  /** Leading mark; defaults to a check that shows when pressed. Pass a legend swatch to make the chip its own key. */
  leading?: ReactNode
  children: ReactNode
}

/** On/off chip, e.g. for pitch overlay toggles. Exposes state via aria-pressed. */
export function ToggleChip({ pressed, onPressedChange, leading, className = '', children, ...rest }: ToggleChipProps) {
  return (
    <button
      type="button"
      className={`chip ${leading ? 'chip--swatch' : ''} ${className}`.trim()}
      aria-pressed={pressed}
      onClick={() => onPressedChange(!pressed)}
      {...rest}
    >
      {leading ?? <Icon name="check" className="chip__check" />}
      <span>{children}</span>
    </button>
  )
}
