import { create } from 'zustand'
import {
  fetchCompetitions,
  fetchGoals,
  fetchMatches,
  fetchSequence,
} from '../api/client'
import type {
  CompetitionSummary,
  FrameData,
  GoalSequenceResponse,
  GoalSummary,
  MatchSummary,
} from '../types/frame'

interface AnalysisState {
  // --- Browse data ---
  competitions: CompetitionSummary[]
  matches: MatchSummary[]
  goals: GoalSummary[]

  // --- Selections ---
  selectedCompetition: CompetitionSummary | null
  selectedMatch: MatchSummary | null
  selectedGoal: GoalSummary | null

  // --- Sequence ---
  sequence: GoalSequenceResponse | null
  currentFrameIndex: number

  // --- Loading / error ---
  loading: boolean
  error: string | null

  // --- Derived ---
  currentFrame: FrameData | null

  // --- Actions ---
  loadCompetitions: () => Promise<void>
  selectCompetition: (competition: CompetitionSummary) => Promise<void>
  selectMatch: (match: MatchSummary) => Promise<void>
  selectGoal: (goal: GoalSummary) => Promise<void>
  setFrameIndex: (index: number) => void
  stepForward: () => void
  stepBack: () => void
  reset: () => void
}

export const useAnalysisStore = create<AnalysisState>((set, get) => ({
  competitions: [],
  matches: [],
  goals: [],

  selectedCompetition: null,
  selectedMatch: null,
  selectedGoal: null,

  sequence: null,
  currentFrameIndex: 0,

  loading: false,
  error: null,

  get currentFrame() {
    const { sequence, currentFrameIndex } = get()
    return sequence?.frames[currentFrameIndex] ?? null
  },

  loadCompetitions: async () => {
    set({ loading: true, error: null })
    try {
      const competitions = await fetchCompetitions()
      set({ competitions, loading: false })
    } catch (e) {
      set({ error: String(e), loading: false })
    }
  },

  selectCompetition: async (competition) => {
    set({
      selectedCompetition: competition,
      selectedMatch: null,
      selectedGoal: null,
      matches: [],
      goals: [],
      sequence: null,
      currentFrameIndex: 0,
      loading: true,
      error: null,
    })
    try {
      const matches = await fetchMatches(
        competition.competition_id,
        competition.season_id,
      )
      set({ matches, loading: false })
    } catch (e) {
      set({ error: String(e), loading: false })
    }
  },

  selectMatch: async (match) => {
    set({
      selectedMatch: match,
      selectedGoal: null,
      goals: [],
      sequence: null,
      currentFrameIndex: 0,
      loading: true,
      error: null,
    })
    try {
      const goals = await fetchGoals(match.match_id)
      set({ goals, loading: false })
    } catch (e) {
      set({ error: String(e), loading: false })
    }
  },

  selectGoal: async (goal) => {
    const { selectedMatch } = get()
    if (!selectedMatch) return
    set({
      selectedGoal: goal,
      sequence: null,
      currentFrameIndex: 0,
      loading: true,
      error: null,
    })
    try {
      const sequence = await fetchSequence(
        selectedMatch.match_id,
        goal.goal_event_id,
      )
      set({ sequence, currentFrameIndex: 0, loading: false })
    } catch (e) {
      set({ error: String(e), loading: false })
    }
  },

  setFrameIndex: (index) => {
    const { sequence } = get()
    if (!sequence) return
    const clamped = Math.max(0, Math.min(index, sequence.frames.length - 1))
    set({ currentFrameIndex: clamped })
  },

  stepForward: () => {
    const { currentFrameIndex, sequence } = get()
    if (!sequence) return
    const next = Math.min(currentFrameIndex + 1, sequence.frames.length - 1)
    set({ currentFrameIndex: next })
  },

  stepBack: () => {
    const { currentFrameIndex } = get()
    set({ currentFrameIndex: Math.max(currentFrameIndex - 1, 0) })
  },

  reset: () =>
    set({
      selectedCompetition: null,
      selectedMatch: null,
      selectedGoal: null,
      matches: [],
      goals: [],
      sequence: null,
      currentFrameIndex: 0,
      error: null,
    }),
}))
