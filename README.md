# What Went Wrong

A soccer defensive collapse analyzer. Pick a goal from StatsBomb open data, step through the possession sequence that led to it frame by frame, and see exactly where the defensive shape fell apart.

![Status](https://img.shields.io/badge/status-in%20progress-yellow)

---

## What it does

1. **Browse** StatsBomb open-data competitions and matches (360-data enabled only)
2. **Pick a goal** to analyze — see xG, minute, and which team conceded
3. **Step through** every event in the possession sequence, from the moment the attacking team won the ball to the moment it hit the net
4. **See the shape** — all visible players rendered on a top-down pitch, updating each frame
5. **Score the defense** — three metrics computed per frame:
   - **Compactness** — how tightly grouped the defensive unit is
   - **Line height** — how deep the last line of defense is sitting
   - **Cover shadows** — which passing lanes are actively blocked
6. **Find the collapse** — the single frame where the composite score dropped most sharply is highlighted as *the moment it went wrong*
7. **Pressure overlay** — a color-coded heatmap showing defensive coverage zones, fading as the shape breaks

---

## Stack

| Layer | Tech |
|-------|------|
| Data | [StatsBomb open data](https://github.com/statsbomb/open-data) (free) |
| Backend | Python 3.11 · FastAPI · httpx · numpy · Pydantic v2 |
| Frontend | React 18 · TypeScript · D3.js v7 · Zustand · Vite |

---

## Project structure

```
what-went-wrong/
├── backend/
│   ├── main.py                  # FastAPI app entry point
│   ├── requirements.txt
│   └── app/
│       ├── config.py            # env-var config
│       ├── models/
│       │   └── frame.py         # Pydantic DTOs (API contract)
│       ├── services/
│       │   ├── cache.py         # in-memory TTL LRU cache
│       │   ├── data_loader.py   # async StatsBomb data fetcher
│       │   ├── possession.py    # possession sequence extraction
│       │   ├── normalizer.py    # coordinate normalization
│       │   ├── scorer.py        # shape scoring + pressure grid
│       │   └── collapse.py      # collapse frame detection
│       ├── routers/
│       │   ├── competitions.py  # GET /api/v1/competitions
│       │   ├── matches.py       # GET /api/v1/.../matches + goals
│       │   └── analysis.py      # GET /api/v1/.../sequence
│       └── tests/
│           ├── test_normalizer.py
│           ├── test_scorer.py
│           └── test_possession.py
└── frontend/                    # React app (in progress)
```

---

## Getting started

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Visit `http://localhost:8000/docs` for the interactive API docs.

#### Optional: use a local StatsBomb data clone

The backend fetches data from GitHub by default. To avoid rate limits, clone the StatsBomb open-data repo (~5 GB) and point the backend at it:

```bash
git clone https://github.com/statsbomb/open-data.git /path/to/open-data
export STATSBOMB_LOCAL_PATH=/path/to/open-data/data
```

### Run tests

```bash
cd backend
pytest tests/ -v
```

---

## API endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/health` | Health check |
| GET | `/api/v1/competitions` | List 360-enabled competitions |
| GET | `/api/v1/competitions/{cid}/seasons/{sid}/matches` | List matches with 360 data |
| GET | `/api/v1/matches/{mid}/goals` | List goals in a match |
| GET | `/api/v1/matches/{mid}/goals/{gid}/sequence` | Full frame-by-frame sequence |

---

## Why only 360-data matches?

StatsBomb events record the position of the player *performing* an action — not all 22 players. The full defensive shape (all visible players per frame) requires **StatsBomb 360 data**, which is available for ~11 competitions in the free tier: EURO 2020, FIFA Women's World Cup 2019, and select club matches. Matches without 360 data are hidden from the browser.

---

## How the scoring works

All coordinates are normalized so the **defending team's goal is always at x = 0**.

| Metric | Formula |
|--------|---------|
| Compactness | `1 − (bounding box area of defenders / 2400)` |
| Line height | Average x of the 4 deepest defenders (lower = safer) |
| Cover shadows | Fraction of attackers with a defender on the ball→attacker ray |
| **Composite** | `0.4 × compactness + 0.3 × (1 − line/60) + 0.3 × shadows` |

The **collapse frame** is the one with the largest single-step drop in composite score.

---

## Status

| Component | Status |
|-----------|--------|
| Backend API | Done |
| Data models (Pydantic) | Done |
| Scoring pipeline | Done |
| Collapse detection | Done |
| Backend tests | Done |
| React frontend | In progress |
