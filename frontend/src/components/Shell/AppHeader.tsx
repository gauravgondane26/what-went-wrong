import { Button, Icon } from '../ui'

interface Crumb { label: string; current?: boolean }

interface Props {
  view: 'picker' | 'analysis'
  crumbs: Crumb[]
  onHome: () => void
  onHowTo: () => void
}

/** The product's mark: a defensive shape with one side broken open (red). */
export function BrandMark() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" className="brand-mark">
      <path d="M5 7.5 12 3l7 4.5" fill="none" stroke="var(--color-defence)" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M19 7.5v8.5L12 21 5 16V7.5" fill="none" stroke="var(--color-defence)" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M19 12.5 21.5 11" stroke="var(--color-collapse)" strokeWidth="2.2" strokeLinecap="round" />
      <circle cx="12" cy="12" r="2.2" fill="var(--color-ink)" />
    </svg>
  )
}

export function AppHeader({ view, crumbs, onHome, onHowTo }: Props) {
  return (
    <header className="bar" data-view={view}>
      <a
        className="brand"
        href="/"
        onClick={(e) => { e.preventDefault(); onHome() }}
        aria-label={view === 'analysis' ? 'What Went Wrong, back to all goals' : 'What Went Wrong'}
      >
        <BrandMark />
        <span className="brand-name">What Went Wrong</span>
      </a>
      {crumbs.length > 0 && (
        <nav className="crumbs" aria-label="Current goal">
          {crumbs.map((c, i) => (
            <span key={i} className={c.current ? 'crumb crumb--current' : 'crumb'} aria-current={c.current ? 'page' : undefined}>
              {c.label}
            </span>
          ))}
        </nav>
      )}
      <div className="bar-actions">
        <Button variant="ghost" onClick={onHowTo} aria-label="How to read it" className="bar-btn">
          <Icon name="help" /><span className="bar-btn-label">How to read it</span>
        </Button>
        {view === 'analysis' && (
          <Button variant="secondary" onClick={onHome} aria-label="All goals" className="bar-btn">
            <Icon name="list" /><span className="bar-btn-label">All goals</span>
          </Button>
        )}
      </div>
    </header>
  )
}
