"""
Collapse detection: find the frame where the defence fell apart.

Two signals, tried in order:

1. Shape. Only reliable frames (enough visible defenders, see
   scorer.MIN_RELIABLE_DEFENDERS) take part. For each step between consecutive
   reliable frames, the drop is the mean composite of the WINDOW frames from
   that step onward minus the mean of the WINDOW frames before it. A one-frame
   dip that recovers scores half as much as a drop that holds, so camera noise
   loses to a real break. Steps where the visible-defender count jumps by
   MAX_COUNT_JUMP or more are skipped, and no window reaches across one: those
   drops mostly come from the camera seeing more (or fewer) players, not from
   the shape changing. A drop of at least SHAPE_MIN_DROP is a shape collapse.

2. Marking. A packed box reads as "compact", so crosses and set pieces often
   beat the composite without moving it. Over all frames, the same windowed
   step is taken on the number of unmarked attackers in the box; a rise of at
   least MARKING_MIN_JUMP is a marking collapse.

If neither qualifies, a smaller shape drop is still reported (kind "shape")
rather than nothing; only a sequence with no drop and no marking rise has no
collapse. Thresholds were chosen on EURO 2020 (docs/eval/collapse-after.md).
"""
from __future__ import annotations

from typing import Literal

from app.models.frame import CollapseCause, FrameData

WINDOW = 2
MAX_COUNT_JUMP = 3
SHAPE_MIN_DROP = 0.05
MARKING_MIN_JUMP = 1.0

CollapseKind = Literal["shape", "marking"]


def _mean(values: list[float]) -> float:
    return sum(values) / len(values)


def _steepest_step(values: list[float], counts: list[int], sign: int) -> tuple[int | None, float]:
    """Index k maximising sign * (mean(values[k:k+W]) - mean(values[k-W:k])).

    Windows stay inside segments split where `counts` jumps by MAX_COUNT_JUMP or
    more, and steps across a split are skipped. Returns (None, 0.0) if no step
    moves in the requested direction. Ties go to the earliest step.
    """
    segment = [0]
    for k in range(1, len(values)):
        segment.append(segment[-1] + (abs(counts[k] - counts[k - 1]) >= MAX_COUNT_JUMP))

    best_k, best = None, 0.0
    for k in range(1, len(values)):
        if segment[k] != segment[k - 1]:
            continue
        before = [values[j] for j in range(max(0, k - WINDOW), k) if segment[j] == segment[k]]
        after = [values[j] for j in range(k, min(len(values), k + WINDOW)) if segment[j] == segment[k]]
        step = sign * (_mean(after) - _mean(before))
        if step > best:  # strict: ties go to the earliest step
            best_k, best = k, step
    return best_k, best


def _shape_collapse(frames: list[FrameData]) -> tuple[int | None, float]:
    """(frame index of the steepest sustained composite drop, its size >= 0)."""
    reliable = [i for i, f in enumerate(frames) if f.scores.reliable]
    k, drop = _steepest_step(
        [frames[i].scores.composite for i in reliable],
        [frames[i].scores.defenders_visible for i in reliable],
        sign=-1,
    )
    return (reliable[k] if k is not None else None), drop


def _marking_collapse(frames: list[FrameData]) -> tuple[int | None, float]:
    """(frame index of the steepest sustained rise in unmarked attackers in the box, its size)."""
    return _steepest_step(
        [float(f.scores.unmarked_in_box) for f in frames],
        [f.scores.defenders_visible for f in frames],
        sign=+1,
    )


def detect_collapse(frames: list[FrameData]) -> list[FrameData]:
    """
    Annotates `score_delta`, `is_collapse_frame` and `collapse_kind` on each
    frame (mutates in place).

    score_delta: composite minus the previous reliable frame's composite; None for
    unreliable frames and the first reliable one.
    is_collapse_frame: True on at most one frame (see module docstring), whose
    collapse_kind says which signal found it.
    """
    for f in frames:
        f.score_delta = None
        f.is_collapse_frame = False
        f.collapse_kind = None

    previous = None
    for f in frames:
        if not f.scores.reliable:
            continue
        if previous is not None:
            f.score_delta = round(f.scores.composite - previous, 4)
        previous = f.scores.composite

    shape_i, shape_drop = _shape_collapse(frames)
    marking_i, marking_jump = _marking_collapse(frames)

    chosen: tuple[int, CollapseKind] | None = None
    if shape_i is not None and shape_drop >= SHAPE_MIN_DROP:
        chosen = (shape_i, "shape")
    elif marking_i is not None and marking_jump >= MARKING_MIN_JUMP:
        chosen = (marking_i, "marking")
    elif shape_i is not None:
        chosen = (shape_i, "shape")

    if chosen is not None:
        i, kind = chosen
        frames[i].is_collapse_frame = True
        frames[i].collapse_kind = kind
    return frames


def collapse_frame_index(frames: list[FrameData]) -> int | None:
    for i, f in enumerate(frames):
        if f.is_collapse_frame:
            return i
    return None


def collapse_kind(frames: list[FrameData]) -> CollapseKind | None:
    i = collapse_frame_index(frames)
    return frames[i].collapse_kind if i is not None else None


SHAPE_METRICS = ("compactness", "goal_side_share", "cover_shadow_coverage")


def attribute(frames: list[FrameData], index: int | None) -> CollapseCause | None:
    """Explain the collapse at `index`: the measure that moved most and the action into it.

    - shape: compared with the previous reliable frame; the sub-score of the
      composite that fell furthest (ties: compactness, goal-side, lanes, in that
      order — the frontend's former biggestDrop).
    - marking: compared with the previous frame; unmarked attackers in the box.
    - action: the latest ball-moving action on a frame from the compared frame up
      to the collapse (exclusive). A snapshot shows positions as its event
      happens, so what moved the defence into frame k happened before k.
    """
    if index is None:
        return None
    f = frames[index]
    kind = f.collapse_kind or "shape"

    if kind == "marking":
        prev = index - 1 if index > 0 else None
    else:
        prev = next((j for j in range(index - 1, -1, -1) if frames[j].scores.reliable), None)

    metric = metric_from = metric_to = None
    if prev is not None:
        a, b = frames[prev].scores, f.scores
        if kind == "marking":
            metric, metric_from, metric_to = "unmarked_in_box", float(a.unmarked_in_box), float(b.unmarked_in_box)
        else:
            metric = min(SHAPE_METRICS, key=lambda m: getattr(b, m) - getattr(a, m))
            metric_from, metric_to = getattr(a, metric), getattr(b, metric)

    start = prev if prev is not None else max(0, index - 1)
    action_index = next(
        (j for j in range(index - 1, start - 1, -1) if frames[j].action is not None), None
    )
    return CollapseCause(
        kind=kind,
        frame_index=index,
        compared_to_index=prev,
        metric=metric,
        metric_from=metric_from,
        metric_to=metric_to,
        action=frames[action_index].action if action_index is not None else None,
        action_frame_index=action_index,
    )
