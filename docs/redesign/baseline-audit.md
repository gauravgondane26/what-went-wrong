# Baseline Audit (before redesign)

Date: 2026-11-04 · Branch: `redesign` @ `9ae293a`
Rules: Vercel Web Interface Guidelines (`vercel-labs/web-interface-guidelines/command.md`, fetched 2026-11-04).

The skill could not be installed (see note at the end), so these rules were applied by hand to every file under `frontend/src/` plus `index.html`.
Contrast ratios were computed with the WCAG 2.x formula.

Scope: presentational code only. `api/client.ts`, `stores/analysisStore.ts` and `types/frame.ts` hold no markup or styles and are out of scope under the redesign ground rules.

Tags: **[A11y]** accessibility · **[UX]** usability / interaction · **[Perf]** performance · **[Comp]** comprehension (does a first-time user understand what they're looking at?). Comp isn't a Vercel category. It's added because it's the main complaint behind this redesign.

---

## frontend/index.html

frontend/index.html:5 - [A11y] no `<meta name="theme-color">` matching dark background
frontend/index.html:6 - [Comp] `<title>` and no `<meta name="description">`; nothing states the app's purpose

## frontend/src/index.css

frontend/src/index.css:16 - [Perf] `Inter` declared but never loaded (no @font-face / preload) → silently falls back to system-ui
frontend/src/index.css:17 - [Perf] `JetBrains Mono` declared but never loaded → falls back to generic monospace
frontend/src/index.css:20 - [A11y] dark UI without `color-scheme: dark` on `html` (native range input, scrollbars render light)
frontend/src/index.css:20 - [UX] no `touch-action: manipulation` / intentional `-webkit-tap-highlight-color`
frontend/src/index.css:22 - [A11y] no `:focus-visible` style defined anywhere; buttons rely on UA default, custom list items have none
frontend/src/index.css:45 - [UX] fixed `260px 1fr 260px` grid, no breakpoints → unusable below ~900px; `overflow: hidden` clips content
frontend/src/index.css:98 - [A11y] 10px heading text (also :131, :328, :330); below a readable minimum
frontend/src/index.css:121 - [A11y] 11px muted text (also :137, :172, :219, :287, :290, :291); muted `#7a82a0` on `--surface` = 4.43:1, on `--surface2` = 3.93:1 (fails 4.5:1 for small text)
frontend/src/index.css:115 - [A11y] transitions not gated by `prefers-reduced-motion` (also :205, :239, :252, :315)
frontend/src/index.css:208 - [A11y] disabled buttons at `opacity: 0.3` → glyphs near-invisible
frontend/src/index.css:232 - [UX] timeline dots are 10×10px hit targets (min ~24px)
frontend/src/index.css:241 - [A11y] hover `transform: scale` with no reduced-motion variant
frontend/src/index.css:243 - [UX] `.timeline-dot--collapse` overrides `--active` (same specificity, later rule) → on the collapse frame the "you are here" state disappears
frontend/src/index.css:315 - [Perf] animates `width` instead of `transform: scaleX`
frontend/src/index.css:13 - [Comp] `--collapse` and `--danger` share defender colour `#e05c2a` → "defender" and "something went wrong" read as the same thing

## frontend/src/App.tsx

frontend/src/App.tsx:13 - [A11y] no skip link to main content
frontend/src/App.tsx:14 - [A11y] h1 followed directly by h3 in children (BrowsePanel, ScorePanel); h2 level skipped
frontend/src/App.tsx:15 - [Comp] subtitle "Soccer defensive collapse analyzer" is the only explanation of purpose
frontend/src/App.tsx:24 - [A11y] error banner not `role="alert"` / `aria-live`
frontend/src/App.tsx:24 - [UX] error shows raw message, no next step (retry, pick another goal, backend waking up)
frontend/src/App.tsx:27 - [Comp] empty state is one line of instruction; no explanation of what you'll see or why it matters, no suggested example goal
frontend/src/App.tsx:33 - [UX] "Loading…" with no context; analysis on a cold Render instance can take 30s+ with no indication why
frontend/src/App.tsx:33 - [A11y] loading state not announced (`aria-live="polite"` / `aria-busy`)
frontend/src/App.tsx:41 - [UX] pitch hard-coded `width={640}`; doesn't scale with viewport
frontend/src/App.tsx:49 - [A11y] two unlabeled `<aside>` landmarks (BrowsePanel also renders `<aside>`); need `aria-label`
frontend/src/App.tsx:49 - [UX] right column renders empty 260px column until a goal is chosen
frontend/src/App.tsx:8 - [UX] selection (competition/match/goal/frame) not reflected in URL; can't share or deep-link an analysis *(needs store/routing change; out of scope without approval)*

## frontend/src/components/BrowsePanel/BrowsePanel.tsx

frontend/src/components/BrowsePanel/BrowsePanel.tsx:7 - [A11y] `<aside>` without accessible name
frontend/src/components/BrowsePanel/BrowsePanel.tsx:8 - [Comp] three stacked lists with no step indication (1 Competition → 2 Match → 3 Goal); lists grow unbounded and push goals far below the fold

## frontend/src/components/BrowsePanel/CompetitionList.tsx

frontend/src/components/BrowsePanel/CompetitionList.tsx:19 - [UX] any store error (e.g. analysis failure) replaces the whole competition list
frontend/src/components/BrowsePanel/CompetitionList.tsx:23 - [A11y] h3 under h1 (skips h2)
frontend/src/components/BrowsePanel/CompetitionList.tsx:25 - [A11y] loading not `aria-live`
frontend/src/components/BrowsePanel/CompetitionList.tsx:29 - [A11y] `<li onClick>`: not focusable, no keyboard activation, no role → use `<button>`
frontend/src/components/BrowsePanel/CompetitionList.tsx:31 - [A11y] selected state is visual only; needs `aria-current` / `aria-pressed`

## frontend/src/components/BrowsePanel/MatchList.tsx

frontend/src/components/BrowsePanel/MatchList.tsx:20 - [Comp] "No 360-data matches available." uses jargon, no next step
frontend/src/components/BrowsePanel/MatchList.tsx:24 - [A11y] `<li onClick>` not keyboard accessible → `<button>`
frontend/src/components/BrowsePanel/MatchList.tsx:26 - [A11y] selected state visual only
frontend/src/components/BrowsePanel/MatchList.tsx:30 - [Typography] score lacks `tabular-nums`
frontend/src/components/BrowsePanel/MatchList.tsx:33 - [Locale] raw ISO `match_date` → `Intl.DateTimeFormat`

## frontend/src/components/BrowsePanel/GoalList.tsx

frontend/src/components/BrowsePanel/GoalList.tsx:24 - [A11y] `<li onClick>` not keyboard accessible → `<button>`
frontend/src/components/BrowsePanel/GoalList.tsx:26 - [A11y] selected state visual only
frontend/src/components/BrowsePanel/GoalList.tsx:31 - [A11y] "PEN" abbreviation without expansion
frontend/src/components/BrowsePanel/GoalList.tsx:38 - [Comp] "xG" unexplained to non-analysts
frontend/src/components/BrowsePanel/GoalList.tsx:29 - [Comp] goal row doesn't show the scorer, which is how people remember goals *(field not in `GoalSummary`; would need backend data)*

## frontend/src/components/FrameStepper/FrameStepper.tsx

frontend/src/components/FrameStepper/FrameStepper.tsx:54 - [A11y] global `window` keydown ignores focus target and modifiers: arrows on the focused range input step twice, Space hijacked on focused buttons/list items
frontend/src/components/FrameStepper/FrameStepper.tsx:80 - [Comp] raw StatsBomb event type ("Ball Receipt*", "Carry", "Pressure") in monospace; no plain-language description of what happened
frontend/src/components/FrameStepper/FrameStepper.tsx:82 - [Comp] "collapse" label lowercase, 11px, no explanation of what a collapse is
frontend/src/components/FrameStepper/FrameStepper.tsx:95 - [UX] Prev disabled while playing (Next isn't); inconsistent, blocks interrupting playback backwards
frontend/src/components/FrameStepper/FrameStepper.tsx:107 - [UX] `⏸` renders as a colour emoji on Windows; use SVG icons
frontend/src/components/FrameStepper/FrameStepper.tsx:110 - [A11y] range input has no `aria-label` / `aria-valuetext`
frontend/src/components/FrameStepper/FrameStepper.tsx:131 - [Typography] lowercase "frame 1 / N"; not announced on change
frontend/src/components/FrameStepper/FrameStepper.tsx:136 - [A11y] timeline dots: no `aria-current` on active, collapse conveyed by colour only
frontend/src/components/FrameStepper/FrameStepper.tsx:145 - [A11y] `title` tooltip only (not keyboard/touch reachable)
frontend/src/components/FrameStepper/FrameStepper.tsx:135 - [Comp] slider + dot row duplicate each other; neither shows the score trend, so you can't see where the shape broke

## frontend/src/components/Pitch/PitchContainer.tsx

frontend/src/components/Pitch/PitchContainer.tsx:33 - [A11y] `<svg>` has no `role="img"`, `aria-label` or text alternative; frame content invisible to screen readers
frontend/src/components/Pitch/PitchContainer.tsx:35 - [UX] fixed pixel width/height instead of `viewBox` + fluid width
frontend/src/components/Pitch/PitchContainer.tsx:39 - [Theming] hard-coded colours bypass tokens
frontend/src/components/Pitch/PitchContainer.tsx:33 - [Comp] **no legend**: nothing says blue = attacking team, orange = defending team, yellow = keeper, white ring = player on the ball, yellow cones = cover shadows, blue haze = pressure
frontend/src/components/Pitch/PitchContainer.tsx:33 - [Comp] team names not shown; no "attacking →" direction or "goal being defended" label on the pitch

## frontend/src/components/Pitch/pitchRenderer.ts

frontend/src/components/Pitch/pitchRenderer.ts:33 - [Comp] all three overlays (pressure, shadows, players) always on, no toggles → visual noise; the collapse moment isn't marked on the pitch itself

## frontend/src/components/Pitch/playerLayer.ts

frontend/src/components/Pitch/playerLayer.ts:5 - [A11y] attacker `#3a86e8` on pitch `#2d5a1b` = 2.22:1 (fails 3:1 non-text contrast)
frontend/src/components/Pitch/playerLayer.ts:6 - [A11y] defender `#e05c2a` on pitch = 2.21:1 (fails 3:1); red/blue-vs-green also weak for deuteranopes
frontend/src/components/Pitch/playerLayer.ts:7 - [Comp] keeper yellow is the same hue as cover-shadow cones
frontend/src/components/Pitch/playerLayer.ts:10 - [UX] 5px dots / 1.5px actor ring too small to read at 640px
frontend/src/components/Pitch/playerLayer.ts:13 - [A11y] D3 transitions ignore `prefers-reduced-motion` (also :72, :78, :91, :127)
frontend/src/components/Pitch/playerLayer.ts:58 - [Comp] dots keyed by array index → between frames dots glide between *different* players, which implies movement that didn't happen *(no stable player id in `PlayerPosition`; mitigate with crossfade instead of slide)*
frontend/src/components/Pitch/playerLayer.ts:150 - [A11y] warning drawn as 11px SVG text, not exposed to AT; duplicates the score panel message

## frontend/src/components/Pitch/shadowLayer.ts

frontend/src/components/Pitch/shadowLayer.ts:4 - [Comp] cones at 12% fill are barely visible and unlabeled; unexplained what a "cover shadow" is
frontend/src/components/Pitch/shadowLayer.ts:7 - [A11y] transitions ignore `prefers-reduced-motion`
frontend/src/components/Pitch/shadowLayer.ts:41 - [Comp] keyed by index → cones morph between unrelated attackers

## frontend/src/components/Pitch/pressureLayer.ts

frontend/src/components/Pitch/pressureLayer.ts:10 - [Comp] `interpolateBlues` at ≤45% opacity on green → muddy teal; same blue as attackers; no scale/legend
frontend/src/components/Pitch/pressureLayer.ts:63 - [Comp] low values map to near-white → faint white wash over the whole pitch
frontend/src/components/Pitch/pressureLayer.ts:6 - [A11y] transitions ignore `prefers-reduced-motion`

## frontend/src/components/ScorePanel/ScorePanel.tsx

frontend/src/components/ScorePanel/ScorePanel.tsx:16 - [A11y] h3 under h1 (skips h2)
frontend/src/components/ScorePanel/ScorePanel.tsx:23 - [Comp] "Composite" is jargon; a bare 0–100 number with no "good / weak / broken" banding
frontend/src/components/ScorePanel/ScorePanel.tsx:27 - [Comp] delta only shown on drops; mixed scale (points vs %), not explained
frontend/src/components/ScorePanel/ScorePanel.tsx:43 - [A11y] metric explanations only in `title` (also :49, :55, :58); not keyboard/touch reachable, most users never see them
frontend/src/components/ScorePanel/ScorePanel.tsx:59 - [Comp] "units from goal" is internal jargon (StatsBomb units)
frontend/src/components/ScorePanel/ScorePanel.tsx:63 - [Comp] sparkline (the one chart that shows *when* the shape broke) is 220×48px, tucked at the bottom of the side column, no axis or labels
frontend/src/components/ScorePanel/ScorePanel.tsx:74 - [Typography] legend uses box-drawing glyph "╌" as a key

## frontend/src/components/ScorePanel/ScoreBar.tsx

frontend/src/components/ScorePanel/ScoreBar.tsx:12 - [A11y] hint only via `title`
frontend/src/components/ScorePanel/ScoreBar.tsx:17 - [A11y] bar lacks `role="meter"` + `aria-valuenow/min/max`; AT hears only "62%"
frontend/src/components/ScorePanel/ScoreBar.tsx:15 - [Typography] value lacks `tabular-nums`

## frontend/src/components/ScorePanel/Sparkline.tsx

frontend/src/components/ScorePanel/Sparkline.tsx:66 - [A11y] `<svg>` no `role="img"` / label / text alternative
frontend/src/components/ScorePanel/Sparkline.tsx:37 - [Theming] hard-coded colours (also :48, :59, :60)
frontend/src/components/ScorePanel/Sparkline.tsx:69 - [UX] fixed width; not responsive
frontend/src/components/ScorePanel/Sparkline.tsx:66 - [UX] not interactive; can't click a point to jump to that frame

## frontend/src/hooks/useD3.ts

✓ pass (unused by components; PitchContainer/Sparkline call `d3.select` directly; worth noting for cleanup in Step 5)

## frontend/src/main.tsx · frontend/src/components/Pitch/pitchMarkings.ts

✓ pass

---

## Totals

| Category | Findings |
|---|---|
| Accessibility | 39 |
| UX / interaction | 16 |
| Comprehension | 24 |
| Performance | 3 |
| Typography / locale / theming | 7 |
| **Total** | **89** |

Counts are per distinct issue. Where one line lists several locations ("also :x"), it counts once.

## Note on tooling

`npx skills add vercel-labs/agent-skills --skill web-design-guidelines` was blocked by the session's permission classifier (it executes externally downloaded code). The skill is only a wrapper: it fetches `command.md` and applies it. So the same rules were applied directly. To install it for future runs, run the command yourself or allow it in settings.
