# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

"What Went Wrong" is a soccer defensive collapse analyzer. It loads StatsBomb open-data events for a goal, reconstructs the possession sequence leading to it, renders all visible players on a pitch frame-by-frame, scores the defensive shape at each frame, and highlights the moment the shape fell apart.

**Only matches with StatsBomb 360 data are exposed** — 360 data provides all visible player positions per event (not just the ball carrier). This limits the dataset to ~11 free-tier competitions (EURO 2020, Women's WWC 2019, select club matches).

## UI work

All UI work follows DESIGN.md in the project root. Do not change data fetching or business logic during UI work.

## Commands

```bash
# Backend (Python 3.11+; deployed on 3.12)
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8081

# Frontend (Node 18+)
cd frontend
npm install
npm run dev          # Vite dev server on :5173, proxies /api → :8081
npm run build        # TypeScript type-check + production build

# Backend tests
cd backend
pytest tests/ -v
pytest tests/test_normalizer.py -v   # run a single test file

# Frontend type-check only
cd frontend && npx tsc --noEmit
```

## Architecture

### Data Flow

```
StatsBomb GitHub (raw JSON) → httpx (async) → in-memory TTL/LRU cache
  → FastAPI routes → pipeline services → GoalSequenceResponse JSON
  → React/Zustand store → useD3 hook → D3 mutates SVG in-place
```

### Backend (`backend/`)

FastAPI app (`main.py`) with three routers under `/api/v1`:
- `competitions` — list 360-enabled competitions/seasons
- `matches` — two endpoints: list matches for a competition/season, and list goals within a match
- `analysis` — the main endpoint: load events + 360 data for a match, extract the possession sequence leading to a selected goal, normalize coordinates, score each frame, detect collapse, return `GoalSequenceResponse`

Environment variables are declared in `app/config.py` (loaded via `python-dotenv`). The async httpx client is created at startup and shared via `app.state.http_client`.

**Critical service: `normalizer.py`**
StatsBomb coordinates are always from the event actor's perspective — their team attacks toward x=120. This applies to **both** `event.location` (ball) and the 360 freeze-frame player positions; the `teammate` flag is actor-relative too. So when consecutive events alternate teams, the coordinate system mirrors. The normalizer applies one flip (`x' = 120 − x, y' = 80 − y`) to ball and players alike, gated by `do_flip = not actor_is_defender`. This was confirmed against real data (EURO 2020 Russia vs Denmark, match 3788769). An earlier approach that treated freeze frames as absolute coordinates was wrong and has been removed, so don't bring it back. This is the most likely source of subtle bugs (defenders appearing on the wrong side of the pitch every other frame).

Two safeguards sit on top of the flip:
- **Actor–ball distance check** (`normalizer.py`): if the actor ends up >30 units from the ball after normalization (e.g. some Duel events store the freeze frame in the opponent's coordinate system), the frame is auto-corrected. Prefer this self-healing check over adding event types to a skip list.
- **`Ball Receipt*` events are filtered out** in `routers/analysis.py`. They reuse the preceding event's freeze frame and add no new shape information.

**Key invariant for testing**: After normalization, `mean(defender.x) < mean(attacker.x)` must hold for every frame. The defending goal is always drawn on the left (x=0), whichever team scores and in either half. That is intentional, so metrics stay comparable across sequences.

Other services: `possession.py` (extract events for one possession sequence), `scorer.py` (compactness/line-height/cover-shadows/pressure grid), `collapse.py` (find sharpest composite score drop), `cache.py` (TTL LRU for events/360 JSON), `data_loader.py` (async httpx with retry/backoff).

**Scoring formulas** (all coordinates normalized so defending goal is at x=0):

| Metric | Formula |
|---|---|
| Compactness | Mean distance from their centroid of the 6 outfield defenders nearest the ball, mapped 5 → 1.0, 15 → 0.0 |
| Goal-side share | Fraction of outfield defenders with `x < ball_x` |
| Cover shadows | Fraction of attackers (excluding carrier and keeper) with a defender on the ball→attacker ray; 1.0 if none |
| Line height | Average x of the 4 deepest defenders. Display only, not in the composite |
| Composite | `0.4 × compactness + 0.3 × goal_side + 0.3 × shadows`; `null` when fewer than 6 outfield defenders are visible (`reliable = false`) |
| Pressure grid | Summed Gaussians / 2.0, clipped to 1 (fixed scale, comparable across frames) |
| Collapse frame | Over reliable frames: largest drop of mean(next 2) − mean(previous 2) composite; steps where visible defenders change by ≥3 are skipped and windows don't cross them. `null` if nothing drops |

Earlier definitions (absolute line height, bounding-box compactness, raw single-step drop) tracked ball position and camera framing instead of shape; see `docs/preprocessing-audit-2026-11-03.md` C1–C4, D1.

StatsBomb coordinate system: `0–120` (length) × `0–80` (width). Data fetched from `raw.githubusercontent.com/statsbomb/open-data/master/data/`.

### Frontend (`frontend/src/`)

React 18 + TypeScript + Vite. State managed by Zustand in `stores/analysisStore.ts`. All backend calls go through `api/client.ts` — the typed fetch wrapper for the API.

**D3 integration pattern**: React owns the `<svg>` element via `useRef`; D3 exclusively owns everything rendered inside it. `hooks/useD3.ts` is the escape hatch. All files under `components/Pitch/` except `PitchContainer.tsx` have **zero React imports** — pure D3 functions called from the container. Player dot transitions use `d3.transition().duration(200)`.

Pitch rendering is orchestrated by `pitchRenderer.ts`, which composes four layers in order (bottom to top): `pitchMarkings.ts` (static, drawn once) → `pressureLayer.ts` (24×16 heatmap) → `shadowLayer.ts` (cover shadow cones) → `playerLayer.ts` (dots + ball).

### Core Data Model

`FrameData` (defined in `backend/app/models/frame.py`, mirrored in `frontend/src/types/frame.ts`) is the central DTO:
- `players: PlayerPosition[]` — normalized x/y + `is_attacker` / `keeper` / `actor` flags
- `scores: DefensiveScores` — compactness, goal_side_share, cover_shadow_coverage, composite (nullable), line_height (display), defenders_visible, reliable
- `cover_shadows: CoverShadow[]` — cone geometry for rendering
- `pressure_grid: float[384]` — 24×16 Gaussian coverage heatmap, row-major
- `is_collapse_frame: bool` — true on at most one frame (see collapse rule above)
- `score_delta: float | None` — composite change vs previous reliable frame

### Known Risks

1. **360 frame incompleteness**: Camera occlusion means only 9–20 of 22 players are visible per event. `player_count` is included in `FrameData`; UI shows a warning when `< 6 defenders` are visible.
2. **Own goals**: Use `possession_team.id` (not `team.id`) when identifying the attacking team for sequence extraction.
3. **GitHub rate limits**: `data_loader.py` retries with exponential backoff. Set `STATSBOMB_LOCAL_PATH` env var to a local clone of `statsbomb/open-data` to bypass HTTP entirely. Other tunables: `HTTP_TIMEOUT_SECONDS` (default 30), `HTTP_MAX_RETRIES` (default 3), `CACHE_MAX_SIZE` (default 20), `CACHE_TTL_SECONDS` (default 3600), `CORS_ORIGINS` (default `http://localhost:5173`).
4. **Missing 360 files**: Some matches report `match_status_360='available'` in StatsBomb metadata but have no corresponding file on GitHub. `load_frames360` handles this by catching the 404 and caching an empty dict — these matches will silently return no frame data.
5. **Excluded competitions**: `routers/competitions.py` hard-codes `_EXCLUDED_COMPETITIONS` (La Liga, Ligue 1, MLS). These are flagged 360-enabled but return no usable frames. The competitions list is also cached in module memory for the lifetime of the process.
6. **No cache-clear endpoint**: All caches are in-process. Restart the backend to clear them.
7. **Collapse detection weakness**: The collapse rule works for build-up goals but can miss instant collapses on cross-and-header goals. There, the Duel and Shot at the goal moment share an identical freeze frame, so the biggest drop lands earlier in the sequence. This is an open problem.

## Deployment

- **Backend**: Render (`https://what-went-wrong.onrender.com`). No `render.yaml`; the service is configured in the Render dashboard (root `backend/`, `uvicorn main:app --host 0.0.0.0 --port $PORT`). `CORS_ORIGINS` on Render must include the Netlify URL.
- **Frontend**: Netlify via `netlify.toml` (base `frontend`, SPA redirect to `index.html`).
- In production builds, `api/client.ts` **hard-codes** the Render URL. `VITE_API_URL` in `frontend/.env.production` is currently unused. In dev, the client uses the relative `/api/v1` through the Vite proxy.
- `.github/workflows/keep-alive.yml` pings `/api/v1/health` every 10 minutes so the Render free tier doesn't sleep.

## Environment notes

Development happens on Windows. In PowerShell, `curl` is an alias for `Invoke-WebRequest` and doesn't accept POSIX flags. Use `Invoke-WebRequest -Uri ... -UseBasicParsing`, or run curl from the Bash tool. Interactive API docs are at `http://localhost:8081/docs`.
