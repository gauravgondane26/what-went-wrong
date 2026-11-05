import type {
  CompetitionSummary,
  GoalSequenceResponse,
  GoalSummary,
  MatchSummary,
} from '../types/frame'

// Production builds call the API named by VITE_API_URL. It is set per Netlify
// context (netlify.toml): the live API on main, the staging API on the staging
// branch and on deploy previews. Dev uses the Vite proxy.
const PROD_API = 'https://what-went-wrong.onrender.com'
const BASE = import.meta.env.PROD
  ? `${(import.meta.env.VITE_API_URL || PROD_API).replace(/\/+$/, '')}/api/v1`
  : '/api/v1'

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`)
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText)
    let message = `API ${res.status}: ${text}`
    try {
      const json = JSON.parse(text)
      if (json.detail) message = json.detail
    } catch { /* leave as raw text */ }
    throw new Error(message)
  }
  return res.json() as Promise<T>
}

export function fetchCompetitions(): Promise<CompetitionSummary[]> {
  return get('/competitions')
}

export function fetchMatches(
  competitionId: number,
  seasonId: number,
): Promise<MatchSummary[]> {
  return get(`/competitions/${competitionId}/seasons/${seasonId}/matches`)
}

export function fetchGoals(matchId: number): Promise<GoalSummary[]> {
  return get(`/matches/${matchId}/goals`)
}

export function fetchSequence(
  matchId: number,
  goalEventId: string,
): Promise<GoalSequenceResponse> {
  return get(`/matches/${matchId}/goals/${goalEventId}/sequence`)
}
