"""
Offline evaluation of collapse detection over every goal of a competition.

Runs each goal through sequence_builder.build_goal_sequence (the same code the
API serves) and summarises where the collapse lands relative to the shot. This
is the yardstick for detection changes: run it before and after, and compare
the summaries (and the per-goal JSON) in the PR.

Usage (from backend/):
    python scripts/eval_collapse.py                          # EURO 2020
    python scripts/eval_collapse.py --competition 55 --season 43 \
        --out ../docs/eval/collapse-baseline.md --json ../docs/eval/collapse-baseline.json
Set STATSBOMB_LOCAL_PATH to read from a local open-data clone instead of HTTP.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import statistics
import sys
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

import httpx  # noqa: E402

from app.config import HTTP_TIMEOUT_SECONDS  # noqa: E402
from app.models.frame import GoalSequenceResponse  # noqa: E402
from app.services import data_loader, possession  # noqa: E402
from app.services.sequence_builder import No360DataError, build_goal_sequence  # noqa: E402

# A final reliable step falling at least this much (composite, 0-1 scale) counts as
# a late drop. If the collapse is marked elsewhere, the late drop was "missed".
LATE_DROP = 0.10
CONCURRENCY = 4


@dataclass
class GoalRow:
    match_id: int
    goal_event_id: str
    minute: int
    scoring_team: str
    conceding_team: str
    penalty: bool
    status: str                     # "ok" | "no_360"
    play_pattern: str | None = None
    from_cross: bool = False        # the shot's key pass was a cross
    header: bool = False            # the goal was headed
    frames: int = 0
    reliable_frames: int = 0
    collapse_index: int | None = None
    frames_after_collapse: int | None = None   # 0 = collapse on the last frame
    seconds_before_end: float | None = None    # last frame time - collapse frame time
    collapse_delta: float | None = None        # score_delta on the collapse frame
    end_delta: float | None = None             # change over the last reliable step
    late_drop_missed: bool = False


def _row(seq: GoalSequenceResponse, base: dict) -> GoalRow:
    frames = seq.frames
    reliable = [f for f in frames if f.scores.reliable]
    row = GoalRow(**base, status="ok", frames=len(frames), reliable_frames=len(reliable))

    if len(reliable) >= 2:
        row.end_delta = round(reliable[-1].scores.composite - reliable[-2].scores.composite, 4)

    idx = seq.collapse_frame_index
    row.collapse_index = idx
    if idx is not None:
        cf, last = frames[idx], frames[-1]
        row.frames_after_collapse = len(frames) - 1 - idx
        if cf.period == last.period:
            row.seconds_before_end = round(last.timestamp_seconds - cf.timestamp_seconds, 2)
        row.collapse_delta = cf.score_delta

    late_drop = row.end_delta is not None and row.end_delta <= -LATE_DROP
    collapse_on_last_reliable = idx is not None and frames[idx].frame_index == reliable[-1].frame_index
    row.late_drop_missed = late_drop and not collapse_on_last_reliable
    return row


async def _eval_match(client, match: dict, sem: asyncio.Semaphore) -> list[GoalRow]:
    match_id = match["match_id"]
    async with sem:
        events = await data_loader.load_events(client, match_id)
        try:
            frames360 = await data_loader.load_frames360(client, match_id)
        except Exception:
            frames360 = {}

    by_id = {e["id"]: e for e in events}
    rows = []
    for goal in possession.find_goal_events(events):
        scoring, conceding = possession.goal_teams(events, goal)
        shot = goal.get("shot") or {}
        key_pass = (by_id.get(shot.get("key_pass_id")) or {}).get("pass") or {}
        base = dict(
            match_id=match_id,
            goal_event_id=goal["id"],
            minute=goal.get("minute", 0),
            scoring_team=scoring["name"],
            conceding_team=conceding["name"],
            penalty=possession.is_penalty_goal(goal),
            play_pattern=(goal.get("play_pattern") or {}).get("name"),
            from_cross=bool(key_pass.get("cross", False)),
            header=(shot.get("body_part") or {}).get("name") == "Head",
        )
        try:
            seq = build_goal_sequence(match_id, events, frames360, goal)
        except No360DataError:
            rows.append(GoalRow(**base, status="no_360"))
            continue
        rows.append(_row(seq, base))
    return rows


def _bucket(n: int) -> str:
    if n == 0:
        return "0 (last frame)"
    if n == 1:
        return "1"
    if n == 2:
        return "2"
    if n <= 5:
        return "3-5"
    return "6+"


BUCKETS = ["0 (last frame)", "1", "2", "3-5", "6+"]


def summarise(rows: list[GoalRow], title: str) -> str:
    ok = [r for r in rows if r.status == "ok"]
    open_play = [r for r in ok if not r.penalty]
    found = [r for r in open_play if r.collapse_index is not None]
    pct = lambda n, d: f"{n} ({100 * n / d:.0f}%)" if d else "0"  # noqa: E731

    lines = [
        f"# Collapse detection: {title}",
        "",
        "Generated by `backend/scripts/eval_collapse.py`. Penalties are excluded from the "
        "rates below because they have no build-up shape to break.",
        "",
        "| | Goals |",
        "|---|---|",
        f"| All goals | {len(rows)} |",
        f"| No 360 frames | {len(rows) - len(ok)} |",
        f"| Penalties (with frames) | {len(ok) - len(open_play)} |",
        f"| **Open-play goals analysed** | **{len(open_play)}** |",
        f"| Collapse found | {pct(len(found), len(open_play))} |",
        f"| No collapse (null) | {pct(len(open_play) - len(found), len(open_play))} |",
        f"| Late drop missed (last reliable step ≤ −{LATE_DROP:.2f}, collapse elsewhere) | "
        f"{pct(sum(r.late_drop_missed for r in open_play), len(open_play))} |",
        "",
        "## Where the collapse lands",
        "",
        "Frames between the collapse frame and the last frame of the sequence (usually the shot).",
        "",
        "| Frames before the end | Goals |",
        "|---|---|",
    ]
    counts = Counter(_bucket(r.frames_after_collapse) for r in found)
    lines += [f"| {b} | {pct(counts.get(b, 0), len(found))} |" for b in BUCKETS]

    secs = [r.seconds_before_end for r in found if r.seconds_before_end is not None]
    if secs:
        lines += [
            "",
            f"Seconds from collapse to the last frame: median {statistics.median(secs):.1f}s, "
            f"interquartile {statistics.quantiles(secs, n=4)[0]:.1f}–"
            f"{statistics.quantiles(secs, n=4)[2]:.1f}s.",
        ]
    frames = [r.frames for r in open_play]
    if frames:
        lines.append(
            f"Frames per sequence: median {statistics.median(frames):.0f}, "
            f"max {max(frames)}; reliable frames median "
            f"{statistics.median(r.reliable_frames for r in open_play):.0f}."
        )

    lines += ["", "## By how the goal was made", "", *_group_table(open_play, _goal_shape)]
    lines += ["", "## By play pattern", "", *_group_table(open_play, lambda r: r.play_pattern or "Unknown")]
    return "\n".join(lines) + "\n"


def _goal_shape(r: GoalRow) -> str:
    if r.from_cross and r.header:
        return "Cross, headed"
    if r.from_cross:
        return "Cross, other finish"
    return "Not from a cross"


def _group_table(rows: list[GoalRow], key) -> list[str]:
    """Per group: size, null rate, collapses on the last 2 frames, missed late drops."""
    groups: dict[str, list[GoalRow]] = {}
    for r in rows:
        groups.setdefault(key(r), []).append(r)
    out = [
        "| Group | Goals | No collapse | Collapse in last 2 frames | Late drop missed | Median frames before end |",
        "|---|---|---|---|---|---|",
    ]
    for name, rs in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        found = [r for r in rs if r.collapse_index is not None]
        late = sum(r.frames_after_collapse <= 1 for r in found)
        median = f"{statistics.median(r.frames_after_collapse for r in found):.0f}" if found else "–"
        out.append(
            f"| {name} | {len(rs)} | {len(rs) - len(found)} | {late} | "
            f"{sum(r.late_drop_missed for r in rs)} | {median} |"
        )
    return out


async def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--competition", type=int, default=55, help="StatsBomb competition id (55 = EURO)")
    ap.add_argument("--season", type=int, default=43, help="StatsBomb season id (43 = 2020)")
    ap.add_argument("--out", type=Path, help="write the markdown summary here")
    ap.add_argument("--json", type=Path, help="write per-goal rows here")
    args = ap.parse_args()

    sem = asyncio.Semaphore(CONCURRENCY)
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT_SECONDS) as client:
        comps = await data_loader.load_competitions(client)
        comp = next(
            (c for c in comps if c["competition_id"] == args.competition and c["season_id"] == args.season),
            None,
        )
        title = f"{comp['competition_name']} {comp['season_name']}" if comp else (
            f"competition {args.competition} / season {args.season}"
        )
        matches = await data_loader.load_matches(client, args.competition, args.season)
        matches = [m for m in matches if m.get("match_status_360") == "available"]
        print(f"{title}: {len(matches)} matches with 360 data", file=sys.stderr)
        results = await asyncio.gather(*(_eval_match(client, m, sem) for m in matches))

    rows = sorted((r for rs in results for r in rs), key=lambda r: (r.match_id, r.minute))
    summary = summarise(rows, title)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(summary, encoding="utf-8")
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps([asdict(r) for r in rows], indent=1) + "\n", encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")  # Windows consoles default to cp1252
    print(summary)


if __name__ == "__main__":
    asyncio.run(main())
