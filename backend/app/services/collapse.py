"""
Collapse detection: find the frame where the defensive shape's composite score
falls most sharply and stays down.

Only reliable frames (enough visible defenders, see scorer.MIN_RELIABLE_DEFENDERS)
take part. For each step between consecutive reliable frames, the drop is the mean
composite of the WINDOW frames from that step onward minus the mean of the WINDOW
frames before it. A one-frame dip that recovers scores half as much as a drop
that holds, so camera noise loses to a real break. Steps where the visible-defender
count jumps by MAX_COUNT_JUMP or more are skipped, and no window reaches across
one: those drops mostly come from the camera seeing more (or fewer) players,
not from the shape changing.
"""
from __future__ import annotations

from app.models.frame import FrameData

WINDOW = 2
MAX_COUNT_JUMP = 3


def _mean(values: list[float]) -> float:
    return sum(values) / len(values)


def detect_collapse(frames: list[FrameData]) -> list[FrameData]:
    """
    Annotates `is_collapse_frame` and `score_delta` on each frame (mutates in place).

    score_delta: composite minus the previous reliable frame's composite; None for
    unreliable frames and the first reliable one.
    is_collapse_frame: True on at most one frame, the first frame after the
    steepest sustained drop. No frame is marked if no eligible step falls.
    """
    for f in frames:
        f.score_delta = None
        f.is_collapse_frame = False

    reliable = [i for i, f in enumerate(frames) if f.scores.reliable]
    if not reliable:
        return frames

    composite = [frames[i].scores.composite for i in reliable]
    counts = [frames[i].scores.defenders_visible for i in reliable]

    # Split at count jumps; windows never reach across one, so the camera
    # artifact can't leak into a neighbouring step's drop.
    segment = [0]
    for k in range(1, len(reliable)):
        jump = abs(counts[k] - counts[k - 1]) >= MAX_COUNT_JUMP
        segment.append(segment[-1] + jump)

    best_k, best_drop = None, 0.0
    for k in range(1, len(reliable)):
        frames[reliable[k]].score_delta = round(composite[k] - composite[k - 1], 4)
        if segment[k] != segment[k - 1]:
            continue
        before = [composite[j] for j in range(max(0, k - WINDOW), k) if segment[j] == segment[k]]
        after = [composite[j] for j in range(k, min(len(reliable), k + WINDOW)) if segment[j] == segment[k]]
        drop = _mean(after) - _mean(before)
        if drop < best_drop:  # strict: ties go to the earliest step
            best_k, best_drop = k, drop

    if best_k is not None:
        frames[reliable[best_k]].is_collapse_frame = True
    return frames


def collapse_frame_index(frames: list[FrameData]) -> int | None:
    for i, f in enumerate(frames):
        if f.is_collapse_frame:
            return i
    return None
