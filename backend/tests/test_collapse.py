"""Tests for collapse frame detection."""
import pytest

from app.models.frame import DefensiveScores, FrameData
from app.services.collapse import collapse_frame_index, detect_collapse


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
