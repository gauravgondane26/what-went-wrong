import { CompetitionList } from './CompetitionList'
import { GoalList } from './GoalList'
import { MatchList } from './MatchList'

export function BrowsePanel() {
  return (
    <aside className="browse-panel">
      <CompetitionList />
      <MatchList />
      <GoalList />
    </aside>
  )
}
