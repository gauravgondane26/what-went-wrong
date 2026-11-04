import type { HTMLAttributes, ReactNode } from 'react'

interface CardProps extends Omit<HTMLAttributes<HTMLElement>, 'title'> {
  as?: 'section' | 'article' | 'div'
  title?: ReactNode
  subtitle?: ReactNode
  /** Heading level for the title; pick to keep the page outline h1 → h2 → h3. */
  headingLevel?: 2 | 3
  children?: ReactNode
}

export function Card({
  as: Tag = 'section',
  title,
  subtitle,
  headingLevel = 2,
  className = '',
  children,
  ...rest
}: CardProps) {
  const Heading = headingLevel === 2 ? 'h2' : 'h3'
  return (
    <Tag className={`card ${className}`.trim()} {...rest}>
      {(title || subtitle) && (
        <header>
          {title && <Heading className="card__title">{title}</Heading>}
          {subtitle && <p className="card__subtitle">{subtitle}</p>}
        </header>
      )}
      {children}
    </Tag>
  )
}
