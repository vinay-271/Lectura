"""Unit tests for ``SceneDetector``."""

import numpy as np
import pytest

from services.video_processing import SceneDetector


def solid_frame(
    color: tuple[int, int, int],
    width: int = 640,
    height: int = 360,
) -> np.ndarray:
    return np.full((height, width, 3), color, dtype=np.uint8)


class TestValidation:
    def test_invalid_threshold_raises(self):
        with pytest.raises(ValueError):
            SceneDetector(threshold=0)

    def test_negative_min_gap_raises(self):
        with pytest.raises(ValueError):
            SceneDetector(min_scene_gap=-1)

    def test_invalid_analysis_size_raises(self):
        with pytest.raises(ValueError):
            SceneDetector(analysis_width=0)
        with pytest.raises(ValueError):
            SceneDetector(analysis_height=0)


class TestDifferences:
    def test_identical_frames_have_zero_difference(self):
        detector = SceneDetector()
        frame = solid_frame((100, 100, 100))

        assert detector.calculate_difference(frame, frame) == 0.0
        assert detector.calculate_edge_difference(frame, frame) == 0.0
        assert not detector.is_scene_change(frame, frame)

    def test_different_frames_have_high_difference(self):
        detector = SceneDetector()
        frame_a = solid_frame((0, 0, 0))
        frame_b = solid_frame((255, 255, 255))

        assert detector.calculate_difference(frame_a, frame_b) > 0.5
        assert detector.is_scene_change(frame_a, frame_b)

    def test_difference_is_symmetric(self):
        detector = SceneDetector()
        frame_a = solid_frame((30, 30, 30))
        frame_b = solid_frame((220, 220, 220))

        forward = detector.calculate_difference(frame_a, frame_b)
        backward = detector.calculate_difference(frame_b, frame_a)

        assert forward == pytest.approx(backward)

    def test_difference_is_normalized_to_unit_range(self):
        detector = SceneDetector()
        frame_a = solid_frame((0, 0, 0))
        frame_b = solid_frame((255, 255, 255))

        assert 0.0 <= detector.calculate_difference(frame_a, frame_b) <= 1.0
        assert (
            0.0
            <= detector.calculate_edge_difference(frame_a, frame_b)
            <= 1.0
        )

    def test_odd_and_large_resolutions_are_handled(self):
        detector = SceneDetector()
        frame_a = solid_frame((10, 10, 10), width=1001, height=713)
        frame_b = solid_frame((240, 240, 240), width=1001, height=713)

        assert detector.is_scene_change(frame_a, frame_b)

    def test_portrait_video_keeps_aspect_ratio(self):
        detector = SceneDetector()
        frame_a = solid_frame((10, 10, 10), width=360, height=640)
        frame_b = solid_frame((240, 240, 240), width=360, height=640)

        assert detector.is_scene_change(frame_a, frame_b)


class TestBlankFrames:
    def test_black_frame_is_blank(self):
        detector = SceneDetector()
        assert detector.is_blank_frame(solid_frame((0, 0, 0)))

    def test_visible_frame_is_not_blank(self):
        detector = SceneDetector()
        assert not detector.is_blank_frame(solid_frame((150, 150, 150)))
