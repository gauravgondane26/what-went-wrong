"""Tests for collapse frame detection."""
import pytest

from app.models.frame import DefensiveScores, FrameData
from app.services.collapse import (
    SHAPE_MIN_DROP,
    collapse_frame_index,
    collapse_kind,
    detect_collapse,
)


def _make_frame(index: int, composite: float | None, defenders: int = 8) -> FrameData:
    return FrameData(
        frame_index=index,
        event_id=f"evt-{index}",
        event_type="Carry",
        minute=0,
        second=index,
        period=1,
        timestamp_seconds=float(index),
        ball_x=60.0,
        ball_y=40.0,
        players=[],
        player_count=0,
        scores=DefensiveScores(
            compactness=0.5,
            line_height=10.0,
            goal_side_share=0.5,
            cover_shadow_coverage=0.0,
            composite=composite,
            defenders_visible=defenders,
            reliable=composite is not None,
        ),
        cover_shadows=[],
        pressure_grid=[0.0] * 384,
        is_collapse_frame=False,
        score_delta=0.0,
    )


def _frames(*composites):
    return [_make_frame(i, c) for i, c in enumerate(composites)]


def _marked(frames):
    return [i for i, f in enumerate(frames) if f.is_collapse_frame]


def test_empty_frames():
    assert detect_collapse([]) == []


def test_single_frame_has_no_collapse():
    frames = _frames(0.8)
    detect_collapse(frames)
    assert frames[0].score_delta is None
    assert _marked(frames) == []
    assert collapse_frame_index(frames) is None


def test_two_frames_second_drops():
    frames = _frames(0.8, 0.5)
    detect_collapse(frames)
    assert _marked(frames) == [1]
    assert frames[1].score_delta == pytest.approx(-0.3)


def test_no_drop_means_no_collapse():
    frames = _frames(0.5, 0.6, 0.8)
    detect_collapse(frames)
    assert _marked(frames) == []


def test_score_delta_values():
    frames = _frames(1.0, 0.7, 0.4)
    detect_collapse(frames)
    assert frames[0].score_delta is None
    assert frames[1].score_delta == pytest.approx(-0.3)
    assert frames[2].score_delta == pytest.approx(-0.3)


def test_sustained_drop_beats_bigger_one_frame_dip():
    # Frame 2 dips by 0.4 and recovers; frames 5+ drop by 0.3 and stay down.
    frames = _frames(0.8, 0.8, 0.4, 0.8, 0.8, 0.5, 0.5)
    detect_collapse(frames)
    assert _marked(frames) == [5]


def test_collapse_marks_first_frame_after_drop():
    frames = _frames(0.9, 0.9, 0.3, 0.3)
    detect_collapse(frames)
    assert _marked(frames) == [2]


def test_unreliable_frames_are_skipped():
    # Frame 1 has no composite; the drop is measured from frame 0 to frame 2.
    frames = _frames(0.8, None, 0.4, 0.4)
    detect_collapse(frames)
    assert frames[1].score_delta is None
    assert frames[2].score_delta == pytest.approx(-0.4)
    assert _marked(frames) == [2]


def test_all_unreliable():
    frames = _frames(None, None)
    detect_collapse(frames)
    assert _marked(frames) == []
    assert all(f.score_delta is None for f in frames)


def test_defender_count_jump_is_not_a_collapse():
    # The big drop coincides with the camera picking up 4 more defenders.
    frames = [
        _make_frame(0, 0.9, defenders=6),
        _make_frame(1, 0.9, defenders=6),
        _make_frame(2, 0.5, defenders=10),
        _make_frame(3, 0.5, defenders=10),
        _make_frame(4, 0.4, defenders=10),
        _make_frame(5, 0.4, defenders=10),
    ]
    detect_collapse(frames)
    assert _marked(frames) == [4]


def test_tie_broken_by_earliest_frame():
    frames = _frames(0.9, 0.6, 0.3)
    detect_collapse(frames)
    # step 1: mean(0.6,0.3) - 0.9 = -0.45; step 2: 0.3 - mean(0.9,0.6) = -0.45
    assert _marked(frames) == [1]


def test_detect_resets_previous_annotations():
    frames = _frames(0.5, 0.6)
    frames[0].is_collapse_frame = True
    detect_collapse(frames)
    assert _marked(frames) == []


def test_collapse_frame_index_returns_marked():
    frames = _frames(0.8, 0.8, 0.5, 0.5)
    detect_collapse(frames)
    assert collapse_frame_index(frames) == 2


# ---------------------------------------------------------------------------
# Shape vs marking
# ---------------------------------------------------------------------------

def _with_marking(composites, unmarked, defenders=None):
    frames = _frames(*composites)
    for i, (f, u) in enumerate(zip(frames, unmarked)):
        f.scores.unmarked_in_box = u
        if defenders is not None:
            f.scores.defenders_visible = defenders[i]
    return frames


def test_real_shape_drop_wins_and_is_labelled_shape():
    frames = _with_marking([0.8, 0.8, 0.5, 0.5, 0.5], [0, 0, 0, 2, 2])
    detect_collapse(frames)
    assert _marked(frames) == [2]
    assert frames[2].collapse_kind == "shape"
    assert collapse_kind(frames) == "shape"


def test_marking_used_when_shape_holds():
    # Composite rises as the ball enters the box; two runners come free at frame 3.
    frames = _with_marking([0.55, 0.6, 0.65, 0.7, 0.7], [0, 0, 0, 2, 2])
    detect_collapse(frames)
    assert _marked(frames) == [3]
    assert collapse_kind(frames) == "marking"


def test_marking_beats_a_small_shape_drop():
    drop = SHAPE_MIN_DROP / 2
    frames = _with_marking([0.6, 0.6, 0.6 - drop, 0.6 - drop, 0.6], [0, 0, 0, 0, 3])
    detect_collapse(frames)
    assert collapse_kind(frames) == "marking"
    assert _marked(frames) == [4]


def test_small_shape_drop_kept_when_marking_never_breaks():
    drop = SHAPE_MIN_DROP / 2
    frames = _with_marking([0.6, 0.6, 0.6 - drop, 0.6 - drop], [1, 1, 1, 1])
    detect_collapse(frames)
    assert _marked(frames) == [2]
    assert collapse_kind(frames) == "shape"


def test_marking_counts_unreliable_frames():
    # Few defenders in view (composite None) but the box is visible: marking still counts.
    frames = _with_marking([None, None, None, None], [0, 0, 2, 2])
    detect_collapse(frames)
    assert _marked(frames) == [2]
    assert collapse_kind(frames) == "marking"


def test_marking_rise_across_camera_cut_is_ignored():
    # The jump in unmarked runners coincides with 4 more defenders coming into view.
    frames = _with_marking([0.6, 0.6, 0.65, 0.65], [0, 0, 3, 3], defenders=[6, 6, 10, 10])
    detect_collapse(frames)
    assert _marked(frames) == []
    assert collapse_kind(frames) is None


def test_single_frame_marking_blip_is_too_small():
    # Window 2: one free runner on one frame averages to a rise of 0.5 < MARKING_MIN_JUMP.
    frames = _with_marking([0.6, 0.62, 0.64, 0.66, 0.68], [0, 0, 1, 0, 0])
    detect_collapse(frames)
    assert _marked(frames) == []


def test_no_drop_and_no_marking_rise_means_no_collapse():
    frames = _with_marking([0.5, 0.6, 0.7], [2, 1, 0])
    detect_collapse(frames)
    assert _marked(frames) == []
    assert collapse_kind(frames) is None


def test_collapse_kind_is_reset():
    frames = _with_marking([0.55, 0.6, 0.65, 0.7, 0.7], [0, 0, 0, 2, 2])
    frames[0].collapse_kind = "shape"
    detect_collapse(frames)
    assert frames[0].collapse_kind is None


def test_score_delta_unchanged_by_marking():
    frames = _with_marking([0.5, None, 0.7, 0.6], [0, 0, 3, 3])
    detect_collapse(frames)
    assert [f.score_delta for f in frames] == [None, None, 0.2, -0.1]
