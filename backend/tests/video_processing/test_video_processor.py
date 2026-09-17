"""End-to-end tests for ``VideoProcessor``."""

from pathlib import Path

import cv2
import numpy as np
import pytest

from services.video_processing import (
    VideoProcessor,
    VideoProcessingResult,
)
from services.video_processing.exceptions import (
    InvalidVideoError,
    VideoNotFoundError,
    VideoProcessingError,
)

MIN_SCENE_GAP = 2.0


@pytest.fixture
def processor_factory(tmp_path: Path):
    """Return a factory that builds a processor writing to a temp dir."""

    def build(video_path: Path) -> VideoProcessor:
        return VideoProcessor(
            video_path=str(video_path),
            output_dir=str(tmp_path / "out"),
        )

    return build


class TestHappyPath:
    def test_returns_result_and_frames(self, processor_factory, scene_video):
        result = processor_factory(scene_video).process_with_result()

        assert isinstance(result, VideoProcessingResult)
        assert result.info is not None
        assert result.info.width == 640
        assert result.info.height == 360
        assert result.info.fps == pytest.approx(24.0)
        assert result.info.frame_count == 144
        assert result.info.duration_seconds == pytest.approx(6.0)
        assert result.metrics is not None
        assert result.metrics.total_time_seconds > 0
        assert result.metrics.frames_saved == len(result.frames)

    def test_solid_color_scenes_do_not_storm_screenshots(
        self, processor_factory, scene_video
    ):
        # Content-driven selection: six flat solid-color scenes carry no
        # useful educational visual, so they must NOT produce one
        # screenshot per scene change (the old time-driven behavior).
        frames = processor_factory(scene_video).process()

        assert 1 <= len(frames) <= 3
        assert all(frame.importance >= 0.0 for frame in frames)

    def test_frames_are_chronological_and_respect_min_gap(
        self, processor_factory, scene_video
    ):
        frames = processor_factory(scene_video).process()

        timestamps = [f.timestamp for f in frames]
        assert timestamps == sorted(timestamps)
        for previous, current in zip(frames, frames[1:]):
            assert current.timestamp - previous.timestamp >= MIN_SCENE_GAP

    def test_saved_images_exist_and_are_valid_jpegs(
        self, processor_factory, scene_video
    ):
        frames = processor_factory(scene_video).process()

        assert frames
        for frame in frames:
            image_path = Path(frame.image_path)
            assert image_path.exists()
            assert image_path.suffix == ".jpg"
            assert frame.file_size_bytes > 0
            assert image_path.stat().st_size == frame.file_size_bytes

            decoded = cv2.imread(str(image_path))
            assert decoded is not None
            assert decoded.shape[0] == frame.height
            assert decoded.shape[1] == frame.width

    def test_images_are_resized_to_max_bounds(
        self, processor_factory, scene_video
    ):
        processor = processor_factory(scene_video)
        processor.frame_extractor.max_width = 320
        processor.frame_extractor.max_height = 180

        frames = processor.process()

        assert frames
        for frame in frames:
            assert frame.width <= 320
            assert frame.height <= 180

    def test_max_frames_cap(self, processor_factory, scene_video):
        frames = processor_factory(scene_video).process(max_frames=2)

        assert len(frames) <= 2


class TestEdgeCases:
    def test_missing_file_raises(self, processor_factory, tmp_path):
        with pytest.raises(VideoNotFoundError):
            processor_factory(tmp_path / "nope.mp4").process()

    def test_missing_file_raises_filenotfound_compat(
        self, processor_factory, tmp_path
    ):
        # Backward compatibility: FileNotFoundError handlers keep working.
        with pytest.raises(FileNotFoundError):
            processor_factory(tmp_path / "nope.mp4").process()

    def test_directory_path_raises(self, processor_factory, tmp_path):
        with pytest.raises(InvalidVideoError, match="not a file"):
            processor_factory(tmp_path).process()

    def test_corrupt_file_raises(self, processor_factory, tmp_path):
        bogus = tmp_path / "bogus.mp4"
        bogus.write_bytes(b"this is not a video file at all")

        with pytest.raises(InvalidVideoError, match="Unable to open"):
            processor_factory(bogus).process()

    def test_short_video_raises(self, processor_factory, short_video):
        with pytest.raises(VideoProcessingError, match="too short"):
            processor_factory(short_video).process()

    def test_invalid_sample_interval_raises(
        self, processor_factory, scene_video
    ):
        with pytest.raises(ValueError, match="sample_interval"):
            processor_factory(scene_video).process(sample_interval=0)

    def test_invalid_max_frames_raises(self, processor_factory, scene_video):
        with pytest.raises(ValueError, match="max_frames"):
            processor_factory(scene_video).process(max_frames=0)

    def test_static_video_yields_few_frames(
        self, processor_factory, static_video
    ):
        frames = processor_factory(static_video).process()

        # One anchor plus at most one drift catch; never a storm of
        # near-identical screenshots.
        assert 1 <= len(frames) <= 3

    def test_drift_video_does_not_storm_screenshots(
        self, processor_factory, drift_video
    ):
        frames = processor_factory(drift_video).process()

        # 20 seconds of slowly fading flat gray: the drift guard keeps
        # evaluating candidates, but flat color is not a useful visual,
        # so only the fallback anchor is saved (no per-drift storm).
        assert 1 <= len(frames) <= 3

    def test_tiny_video_is_processed(self, processor_factory, tiny_video):
        frames = processor_factory(tiny_video).process()

        assert len(frames) >= 1
        for frame in frames:
            assert frame.width == 128
            assert frame.height == 72


class TestMetrics:
    def test_metrics_counts_are_consistent(
        self, processor_factory, scene_video
    ):
        result = processor_factory(scene_video).process_with_result()
        metrics = result.metrics

        assert metrics.frames_read == 144
        # 144 frames at fps 24 with a 0.5s interval -> frame_step 12 ->
        # 12 sampled frames analyzed.
        assert metrics.frames_analyzed == 12
        assert metrics.frames_saved == len(result.frames)
        assert metrics.saved_bytes == sum(
            f.file_size_bytes for f in result.frames
        )
        assert metrics.total_time_seconds > 0
        assert metrics.read_time_seconds >= 0
        assert metrics.analysis_time_seconds >= 0
        assert metrics.save_time_seconds >= 0

    def test_metrics_summary_is_json_ready(
        self, processor_factory, scene_video
    ):
        result = processor_factory(scene_video).process_with_result()
        summary = result.metrics.summary()

        assert set(summary) == {
            "total_time_seconds",
            "read_time_seconds",
            "analysis_time_seconds",
            "save_time_seconds",
            "frames_read",
            "frames_analyzed",
            "scene_changes_detected",
            "scene_changes_skipped_gap",
            "frames_skipped_blank",
            "drift_frames_saved",
            "frames_saved",
            "importance_candidates",
            "importance_selected",
            "mean_importance",
            "saved_bytes",
            "analysis_fps",
            "processing_speed",
        }
        assert all(
            isinstance(value, (int, float)) for value in summary.values()
        )

    def test_blank_frames_are_counted(self, processor_factory, tmp_path):
        from tests.video_processing.conftest import write_video

        def builder(seconds: float, frame_index: int) -> np.ndarray:
            if seconds < 2.0:
                return np.zeros((360, 640, 3), dtype=np.uint8)
            return np.full((360, 640, 3), (200, 40, 40), dtype=np.uint8)

        video = write_video(
            tmp_path / "blank_intro.mp4",
            builder,
            duration=4.0,
        )
        result = processor_factory(video).process_with_result()

        assert result.metrics.frames_skipped_blank >= 1
        assert result.frames
        # The first *useful* frame must not be the black intro.
        assert result.frames[0].timestamp >= 1.0
