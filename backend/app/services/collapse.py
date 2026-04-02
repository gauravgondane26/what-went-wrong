"""
Collapse detection: find the frame with the steepest single-step drop
in composite defensive score.
"""
from __future__ import annotations

from app.models.frame import FrameData


def detect_collapse(frames: list[FrameData]) -> list[FrameData]:
    """
    Annotates `is_collapse_frame` and `score_delta` on each frame (mutates in place).

    collapse_frame_index = the frame where composite score dropped most sharply
    (i.e., where score_delta is most negative).

    The first frame always gets score_delta=0.0 and is_collapse_frame=False.
    """
    if not frames:
        return frames

    scores = [f.scores.composite for f in frames]
    deltas = [0.0] + [scores[i] - scores[i - 1] for i in range(1, len(scores))]

    # index of the most negative delta (worst single-step collapse)
    # ties broken by earliest frame
    worst_idx = min(range(1, len(deltas)), key=lambda i: deltas[i]) if len(frames) > 1 else 0

    for i, frame in enumerate(frames):
        frame.score_delta = round(deltas[i], 4)
        frame.is_collapse_frame = i == worst_idx

    return frames


def collapse_frame_index(frames: list[FrameData]) -> int:
    for i, f in enumerate(frames):
        if f.is_collapse_frame:
            return i
    return 0
