# Roadmap

What Went Wrong is moving from **one goal at a time** to finding patterns, comparing goals and detecting collapses more reliably. This file is the progress tracker:

- When a task is done, its box is ticked in that task's last commit.
- Commit messages start with the task id (e.g. `P1.5`), so `git log --oneline` reads in the same order as this list, and `git log --oneline --grep P1.5` finds one task's commits.
- Each phase has its own branch off `redesign` and its own draft PR.

The order is foundations → detection → reports → compare. Reports and compare both rely on the collapse frame and its cause, so detection has to be settled first.

The backend stays **one containerised FastAPI service** (Docker plus compose, deployed on Render). We decided against microservices and Kubernetes: the in-process cache and the single pipeline would make splitting a net loss. A worker and Redis are added only if reports turn out slow (P2.9).

---

## Phase 0: Foundations · `feat/p0-foundations`
- [x] **P0.1** Add this roadmap
- [x] **P0.2** Move the pipeline out of the route into `services/sequence_builder.py` (no behaviour change)
- [x] **P0.3** Golden fixture of 12 real sequences, plus invariant and collapse snapshot tests
- [x] **P0.4** Wire `CACHE_MAX_SIZE` / `CACHE_TTL_SECONDS` into the caches
- [x] **P0.5** Backend `Dockerfile` + `.dockerignore`
- [x] **P0.6** Root `docker-compose.yml`, with the Vite proxy target set by an env var
- [x] **P0.7** Docs: Docker usage and the switch to Render's Docker runtime
- [ ] **P0.8** `scripts/eval_collapse.py`, plus a baseline in `docs/eval/collapse-baseline.md`

## Phase 1: Smarter detection and "what broke it" · `feat/p1-detection`
- [ ] **P1.1** `FrameAction` model (kind, end location, cross / through ball / cut-back / switch, under pressure) and a helper that normalises the end location
- [ ] **P1.2** Fill `FrameData.action` and `GoalSequenceResponse.play_pattern`
- [ ] **P1.3** Mirror the new fields in the frontend types
- [ ] **P1.4** Eval breakdown by play pattern and by whether the last pass was a cross; refresh the baseline
- [ ] **P1.5** Late-collapse rule: a one-sided window at the end of the sequence
- [ ] **P1.6** *Only if still needed:* use the shot's own freeze frame as the final frame
- [ ] **P1.7** Update the golden snapshot; write `docs/eval/collapse-after.md`
- [ ] **P1.8** `collapse.attribute()`: the action into the collapse, plus the metric that dropped most
- [ ] **P1.9** Expose `collapse_cause` on the response, plus frontend types
- [ ] **P1.10** The finding text names the cause
- [ ] **P1.11** Arrow layer for the action, with a key chip and a how-to-read entry
- [ ] **P1.12** Manual check on a cross-and-header goal, then the draft PR

## Phase 2: Match and team reports · `feat/p2-reports`
- [ ] **P2.1** Report models, plus a pure `aggregate()` function with tests
- [ ] **P2.2** `GET /matches/{id}/report`
- [ ] **P2.3** `GET /competitions/{c}/seasons/{s}/teams/{team}/report`, with limited concurrency
- [ ] **P2.4** Client fetchers + `reportStore`
- [ ] **P2.5** View union in `App.tsx`, plus an empty report view
- [ ] **P2.6** `collapseMapLayer.ts`
- [ ] **P2.7** Report content: map, "what fails most" meters, goal list
- [ ] **P2.8** Entry points from the picker and the analysis view, then the draft PR
- [ ] **P2.9** *Only if needed:* a worker and Redis in compose

## Phase 3: Compare and counterfactual · `feat/p3-compare`
- [ ] **P3.1** Backend ghost v1: the shape from just before the collapse, moved with the ball
- [ ] **P3.2** `ghostLayer.ts` with a chip ("shape 2 moments earlier, moved with the ball")
- [ ] **P3.3** Swap the hard-coded heading ids for `useId()`
- [ ] **P3.4** `createAnalysisStore()` factory
- [ ] **P3.5** `usePlayback(store, { ownsKeyboard })`
- [ ] **P3.6** Compare view: two panes, a shared scrubber aligned on the collapse
- [ ] **P3.7** *Research:* optimised ghost with limits on how far each defender could run
