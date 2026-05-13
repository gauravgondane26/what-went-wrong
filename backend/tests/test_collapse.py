"""Tests for collapse frame detection."""
import pytest

from app.models.frame import CoverShadow, DefensiveScores, FrameData
from app.services.collapse import collapse_frame_index, detect_collapse


def _make_frame(index: int, composite: float) -> FrameData:
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
            compactness=composite,
            line_height=10.0,
            cover_shadow_coverage=0.0,
            composite=composite,
        ),
        cover_shadows=[],
        pressure_grid=[0.0] * 384,
        is_collapse_frame=False,
        score_delta=0.0,
    )


def test_empty_frames():
    assert detect_collapse([]) == []


def test_single_frame_marked_as_collapse():
    frames = [_make_frame(0, 0.8)]
    detect_collapse(frames)
    assert frames[0].score_delta == 0.0
    assert frames[0].is_collapse_frame is True


def test_two_frames_second_drops():
    frames = [_make_frame(0, 0.8), _make_frame(1, 0.5)]
    detect_collapse(frames)
    assert frames[0].is_collapse_frame is False
    assert frames[1].is_collapse_frame is True
    assert frames[1].score_delta == pytest.approx(-0.3)


def test_two_frames_no_actual_drop():
    # Second frame improves — collapse still annotated at only non-first frame
    frames = [_make_frame(0, 0.5), _make_frame(1, 0.8)]
    detect_collapse(frames)
    assert frames[1].is_collapse_frame is True
    assert frames[1].score_delta == pytest.approx(0.3)


def test_three_frames_middle_collapse():
    # composite=[0.9, 0.4, 0.3] → deltas=[0, -0.5, -0.1] → worst at index 1
    frames = [_make_frame(0, 0.9), _make_frame(1, 0.4), _make_frame(2, 0.3)]
    detect_collapse(frames)
    assert frames[1].is_collapse_frame is True
    assert frames[0].is_collapse_frame is False
    assert frames[2].is_collapse_frame is False


def test_three_frames_last_collapse():
    # composite=[0.9, 0.8, 0.2] → deltas=[0, -0.1, -0.6] → worst at index 2
    frames = [_make_frame(0, 0.9), _make_frame(1, 0.8), _make_frame(2, 0.2)]
    detect_collapse(frames)
    assert frames[2].is_collapse_frame is True
    assert frames[2].score_delta == pytest.approx(-0.6)


def test_score_delta_values_are_correct():
    frames = [_make_frame(0, 1.0), _make_frame(1, 0.7), _make_frame(2, 0.4)]
    detect_collapse(frames)
    assert frames[0].score_delta == 0.0
    assert frames[1].score_delta == pytest.approx(-0.3)
    assert frames[2].score_delta == pytest.approx(-0.3)


def test_tie_broken_by_earliest_frame():
    # composite=[0.9, 0.6, 0.3] → deltas=[0, -0.3, -0.3] → Python min returns first tie → index 1
    frames = [_make_frame(0, 0.9), _make_frame(1, 0.6), _make_frame(2, 0.3)]
    detect_collapse(frames)
    assert frames[1].is_collapse_frame is True
    assert frames[2].is_collapse_frame is False


def test_collapse_frame_index_returns_correct():
    frames = [_make_frame(0, 0.8), _make_frame(1, 0.5), _make_frame(2, 0.4)]
    detect_collapse(frames)
    # biggest drop: index 1 (0.8→0.5 = -0.3 vs 0.5→0.4 = -0.1)
    assert collapse_frame_index(frames) == 1


def test_collapse_frame_index_no_marked_frame():
    # detect_collapse not called — all is_collapse_frame stay False → returns 0
    frames = [_make_frame(0, 0.8), _make_frame(1, 0.5)]
    assert collapse_frame_index(frames) == 0
