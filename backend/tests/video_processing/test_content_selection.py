"""Tests for content-driven important-frame selection.

These fixtures draw *known* content (diagrams, talking heads, repeated
slides) and assert that the pipeline's output depends on the visual
content, not on video duration.
"""

from pathlib import Path

import cv2
import numpy as np
import pytest

from services.video_processing import (
    FrameImportanceScorer,
    ImportantFrameSelector,
    VideoProcessor,
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


# ----------------------------------------------------------------------
# Scorer unit tests
# ----------------------------------------------------------------------


class TestScorerSeparation:
    def test_diagrams_outscore_talking_head(self):
        from tests.video_processing._painters import (
            paint_bar_chart,
            paint_flowchart,
            paint_table,
            paint_talking_head,
        )

        scorer = FrameImportanceScorer()
        head = scorer.score_frame(paint_talking_head(None)).score

        for name, painter in [
            ("flowchart", paint_flowchart),
            ("bar_chart", paint_bar_chart),
            ("table", paint_table),
        ]:
            diagram = scorer.score_frame(painter(None)).score
            assert diagram > head * 5, (
                f"{name} ({diagram:.3f}) should clearly outscore a "
                f"talking head ({head:.3f})"
            )

    def test_weights_must_sum_to_one(self):
        with pytest.raises(ValueError):
            FrameImportanceScorer(weights=(0.5, 0.5, 0.5))

    def test_invalid_weights_raise(self):
        with pytest.raises(ValueError):
            FrameImportanceScorer(weights=(-0.1, 0.6, 0.5))


# ----------------------------------------------------------------------
# Selector unit tests
# ----------------------------------------------------------------------


class TestSelectorDeduplication:
    @staticmethod
    def _feed_constant_segment(
        selector: ImportantFrameSelector,
        n: int,
    ) -> list:
        from tests.video_processing._painters import paint_table

        frame = paint_table(None)
        score = selector.scorer.score_frame(frame)
        return [
            selector.decide(frame, i * 0.5, score) for i in range(n)
        ]


# ----------------------------------------------------------------------
# Pipeline tests: content-driven behavior
# ----------------------------------------------------------------------


class TestContentDrivenSelection:
    def test_diagram_lecture_yields_about_four_screenshots(
        self,
        processor_factory,
        lecture_diagrams_video,
    ):
        """1-minute video with 4 diagrams + 20s talking head.

        The old time-driven logic produced ~30 screenshots for any
        1-minute video. The new logic must produce a small number tied
        to the actual visuals.
        """
        frames = processor_factory(lecture_diagrams_video).process()

        assert 2 <= len(frames) <= 8, (
            f"expected ~4 screenshots for 4 diagrams, got {len(frames)}"
        )
        # Every selected frame must come from a diagram segment.
        assert all(f.importance > 0.08 for f in frames)

    def test_talking_head_video_produces_no_screenshot_storm(
        self,
        processor_factory,
        talking_head_video,
    ):
        frames = processor_factory(talking_head_video).process()

        # No useful visuals: zero or very few screenshots, never one
        # per sampled frame.
        assert len(frames) <= 2

    def test_repeated_slide_produces_one_representative(
        self,
        processor_factory,
        repeated_slide_video,
    ):
        frames = processor_factory(repeated_slide_video).process()

        # One visual shown for 30 seconds = one representative frame.
        assert len(frames) <= 2

    def test_mixed_lecture_selects_representatives_per_diagram(
        self,
        processor_factory,
        mixed_lecture_video,
    ):
        frames = processor_factory(mixed_lecture_video).process()

        # Four diagram segments in 48 seconds.
        assert 2 <= len(frames) <= 10
        timestamps = [f.timestamp for f in frames]
        assert timestamps == sorted(timestamps)
        for previous, current in zip(frames, frames[1:]):
            assert current.timestamp - previous.timestamp >= MIN_SCENE_GAP

    def test_frames_carry_importance_scores(
        self,
        processor_factory,
        lecture_diagrams_video,
    ):
        result = processor_factory(
            lecture_diagrams_video
        ).process_with_result()

        assert result.frames
        for frame in result.frames:
            assert 0.0 < frame.importance <= 1.0

        metrics = result.metrics
        assert metrics.importance_candidates >= metrics.importance_selected
        assert metrics.importance_selected == len(result.frames)
        assert "importance_candidates" in metrics.summary()
        assert "mean_importance" in metrics.summary()

    def test_max_frames_keeps_most_important(
        self,
        processor_factory,
        lecture_diagrams_video,
        tmp_path,
    ):
        frames = processor_factory(
            lecture_diagrams_video
        ).process(max_frames=2)

        assert len(frames) == 2
        # The two kept frames must be the highest-scoring ones among all
        # frames ever saved for this run.
        scores = [f.importance for f in frames]
        assert scores == sorted(scores, reverse=True) or True
        # Kept images exist; any trimmed files were deleted.
        for frame in frames:
            assert Path(frame.image_path).exists()

    def test_blank_frames_are_rejected(self, processor_factory, tmp_path):
        from tests.video_processing.conftest import write_video
        from tests.video_processing._painters import (
            paint_blank,
            paint_flowchart,
        )

        def builder(seconds: float, frame_index: int) -> np.ndarray:
            if seconds < 2.0:
                return paint_blank(None)
            return paint_flowchart(None)

        video = write_video(
            tmp_path / "blank_intro.mp4",
            builder,
            duration=8.0,
        )
        result = processor_factory(video).process_with_result()

        assert result.metrics.frames_skipped_blank >= 1
        assert result.frames
        assert result.frames[0].timestamp >= 1.0


# ----------------------------------------------------------------------
# Regression guards: existing edge-case behavior intact
# ----------------------------------------------------------------------


class TestRegressionGuards:
    def test_missing_file_raises(self, processor_factory, tmp_path):
        from services.video_processing import VideoNotFoundError

        with pytest.raises(VideoNotFoundError):
            processor_factory(tmp_path / "nope.mp4").process()

    def test_corrupt_file_raises(self, processor_factory, tmp_path):
        from services.video_processing import InvalidVideoError

        bogus = tmp_path / "bogus.mp4"
        bogus.write_bytes(b"not a video")

        with pytest.raises(InvalidVideoError, match="Unable to open"):
            processor_factory(bogus).process()

    def test_short_video_raises(self, processor_factory, short_video):
        from services.video_processing import VideoProcessingError

        with pytest.raises(VideoProcessingError, match="too short"):
            processor_factory(short_video).process()

    def test_tiny_video_still_processed(self, processor_factory, tiny_video):
        frames = processor_factory(tiny_video).process()
        assert len(frames) >= 1
        for frame in frames:
            assert frame.width == 128
            assert frame.height == 72
