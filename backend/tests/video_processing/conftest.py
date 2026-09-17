"""Shared pytest fixtures for the video-processing test suite."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import cv2
import numpy as np
import pytest

from tests.video_processing._painters import (
    paint_bar_chart,
    paint_flowchart,
    paint_formula_slide,
    paint_table,
    paint_talking_head,
    paint_whiteboard,
)

# OpenCV container used to write all synthetic test videos.
_FOURCC = cv2.VideoWriter_fourcc(*"mp4v")

# Frame builder signature: (seconds, frame_index) -> BGR frame.
FrameBuilder = Callable[[float, int], np.ndarray]


def write_video(
    path: Path,
    frame_builder: FrameBuilder,
    duration: float,
    fps: int = 24,
    width: int = 640,
    height: int = 360,
) -> Path:
    """Write a synthetic video of ``duration`` seconds.

    ``frame_builder(seconds_in_video, frame_index)`` is called once per
    frame and must return a BGR ``numpy`` array of shape
    ``(height, width, 3)``.
    """
    writer = cv2.VideoWriter(str(path), _FOURCC, fps, (width, height))
    assert writer.isOpened(), "VideoWriter failed to open"

    total_frames = int(duration * fps)
    for frame_index in range(total_frames):
        seconds = frame_index / fps
        frame = frame_builder(seconds, frame_index)
        assert frame is not None, (
            "frame_builder must always return a frame; "
            "use the duration parameter to set the video length"
        )
        writer.write(frame)

    writer.release()
    return path


def solid_frame(
    color: tuple[int, int, int],
    width: int = 640,
    height: int = 360,
) -> FrameBuilder:
    """Return a frame builder that always paints the same solid color."""
    return lambda seconds, frame_index: np.full(
        (height, width, 3), color, dtype=np.uint8
    )


def render(painter) -> FrameBuilder:
    """Wrap a painter as a time-independent frame builder."""
    return lambda seconds, frame_index: painter(None)


# ----------------------------------------------------------------------
# Original fixtures
# ----------------------------------------------------------------------


@pytest.fixture
def scene_video(tmp_path: Path) -> Path:
    """A 6-second video with a distinct solid color every second."""
    colors = [
        (200, 40, 40),
        (40, 200, 40),
        (40, 40, 200),
        (200, 200, 40),
        (40, 200, 200),
        (200, 40, 200),
    ]

    def builder(seconds: float, frame_index: int) -> np.ndarray:
        return np.full(
            (360, 640, 3), colors[int(seconds)], dtype=np.uint8
        )

    return write_video(tmp_path / "scenes.mp4", builder, duration=6.0)


@pytest.fixture
def static_video(tmp_path: Path) -> Path:
    """A 4-second video showing one unchanging solid color."""
    return write_video(
        tmp_path / "static.mp4",
        solid_frame((120, 120, 120)),
        duration=4.0,
    )


@pytest.fixture
def short_video(tmp_path: Path) -> Path:
    """A video shorter than the minimum supported duration (0.4s)."""
    return write_video(
        tmp_path / "short.mp4",
        solid_frame((90, 90, 90)),
        duration=10 / 24,
    )


@pytest.fixture
def drift_video(tmp_path: Path) -> Path:
    """A 20-second video whose color slowly fades between two tones."""
    def builder(seconds: float, frame_index: int) -> np.ndarray:
        # Very slow linear drift: far below any per-pair threshold, but
        # very different from the first frame by the end.
        value = int(60 + seconds * 6)  # 60 -> 180 over 20s
        return np.full((360, 640, 3), (value, value, value), dtype=np.uint8)

    return write_video(tmp_path / "drift.mp4", builder, duration=20.0)


@pytest.fixture
def tiny_video(tmp_path: Path) -> Path:
    """A 2-second, 128x72 video (below the resize bounds)."""
    return write_video(
        tmp_path / "tiny.mp4",
        solid_frame((30, 180, 90), width=128, height=72),
        duration=2.0,
        width=128,
        height=72,
    )


# ----------------------------------------------------------------------
# Content-driven selection fixtures
# ----------------------------------------------------------------------


@pytest.fixture
def lecture_diagrams_video(tmp_path: Path) -> Path:
    """A 1-minute lecture: 4 diagram slides (10s each) + 20s talking head.

    The desired outcome is ~4 screenshots (the diagrams), not one every
    two seconds.
    """
    schedule = [
        (0.0, 10.0, paint_flowchart),
        (10.0, 20.0, paint_bar_chart),
        (20.0, 30.0, paint_table),
        (30.0, 40.0, paint_formula_slide),
        (40.0, 60.0, paint_talking_head),  # 20s of talking head
    ]

    def builder(seconds: float, frame_index: int) -> np.ndarray:
        for start, end, painter in schedule:
            if start <= seconds < end:
                return painter(None)
        return paint_talking_head(None)

    return write_video(tmp_path / "lecture_diagrams.mp4", builder, duration=60.0)


@pytest.fixture
def talking_head_video(tmp_path: Path) -> Path:
    """A 12-second webcam-style lecture with no useful visuals."""
    return write_video(
        tmp_path / "talking_head.mp4",
        render(paint_talking_head),
        duration=12.0,
    )


@pytest.fixture
def repeated_slide_video(tmp_path: Path) -> Path:
    """A 30-second video showing the *same* table slide throughout.

    The desired outcome is exactly one screenshot (the representative),
    not one per scene-scan glitch.
    """
    return write_video(
        tmp_path / "repeated_slide.mp4",
        render(paint_table),
        duration=30.0,
    )


@pytest.fixture
def mixed_lecture_video(tmp_path: Path) -> Path:
    """A 48-second lecture alternating diagrams and talking heads."""
    schedule = [
        (0.0, 8.0, paint_flowchart),
        (8.0, 12.0, paint_talking_head),
        (12.0, 20.0, paint_bar_chart),
        (20.0, 24.0, paint_talking_head),
        (24.0, 32.0, paint_table),
        (32.0, 36.0, paint_talking_head),
        (36.0, 44.0, paint_formula_slide),
        (44.0, 48.0, paint_talking_head),
    ]

    def builder(seconds: float, frame_index: int) -> np.ndarray:
        for start, end, painter in schedule:
            if start <= seconds < end:
                return painter(None)
        return paint_talking_head(None)

    return write_video(tmp_path / "mixed_lecture.mp4", builder, duration=48.0)


@pytest.fixture
def whiteboard_video(tmp_path: Path) -> Path:
    """A 10-second whiteboard-only video (no diagrams, no face)."""
    return write_video(
        tmp_path / "whiteboard.mp4",
        render(paint_whiteboard),
        duration=10.0,
    )
