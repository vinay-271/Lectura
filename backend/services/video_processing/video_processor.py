"""Video processing pipeline: validation, sampling, scene detection,
content-driven important-frame selection and optimization.

``VideoProcessor`` is the public entry point of this module. It stays
independent from the FastAPI layer (per the project architecture) and
returns plain dataclasses so any caller can consume the results.

Selection is **content-driven**: sampled frames become *candidates*,
an importance scorer judges how much each frame looks like a useful
educational visual (diagram, chart, slide, table), and a segment
selector commits only the best representative of each dwelling visual —
so a 1-minute video with 4 real diagrams yields about 4 screenshots,
regardless of duration.
"""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

from .exceptions import (
    InvalidVideoError,
    VideoNotFoundError,
    VideoProcessingError,
)
from .frame_extractor import FrameExtractor
from .importance import FrameImportanceScorer
from .important_frame_selector import ImportantFrameSelector
from .metrics import ProcessingMetrics
from .models import ExtractedFrame, VideoInfo, VideoProcessingResult
from .scene_detector import SceneDetector

# Default fps used when a container reports 0/NaN. Choosing a small
# value keeps ``frame_step`` at 1 frame so no footage is skipped.
FALLBACK_FPS = 10.0

# Videos shorter than this many seconds cannot produce meaningful
# "important" screenshots on their own.
MIN_VIDEO_DURATION_SECONDS = 1.0

# Maximum pixels for video dimensions accepted from metadata; guards
# against corrupt headers reporting absurd sizes.
MAX_VIDEO_DIMENSION_PIXELS = 10_000


class VideoProcessor:
    """Validates, samples and analyzes a video, saving important frames."""

    def __init__(
        self,
        video_path: str,
        output_dir: str = "temp/frames",
    ):
        self.video_path = Path(video_path)
        self.frame_extractor = FrameExtractor(output_dir)
        self.scene_detector = SceneDetector()
        self.importance_scorer = FrameImportanceScorer()
        self.frame_selector = ImportantFrameSelector(
            scorer=self.importance_scorer,
        )

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def validate_video(self) -> None:
        """Validate the file path; raise if it is missing or not a file."""
        if not self.video_path.exists():
            raise VideoNotFoundError(
                f"Video file not found: {self.video_path}"
            )

        if not self.video_path.is_file():
            raise InvalidVideoError(
                f"Video path is not a file: {self.video_path}"
            )

    def open_video(self) -> cv2.VideoCapture:
        """Validate and open the video; raise if OpenCV cannot decode it."""
        self.validate_video()

        video = cv2.VideoCapture(str(self.video_path))

        if not video.isOpened():
            video.release()
            raise InvalidVideoError(
                f"Unable to open video: {self.video_path}"
            )

        return video

    def get_video_info(self) -> VideoInfo:
        """Return metadata about the video without processing it."""
        video = self.open_video()
        try:
            return self._read_video_info(video)
        finally:
            video.release()

    def _read_video_info(self, video: cv2.VideoCapture) -> VideoInfo:
        raw_fps = float(video.get(cv2.CAP_PROP_FPS))
        fps = raw_fps if np.isfinite(raw_fps) and raw_fps > 0 else FALLBACK_FPS

        raw_width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
        raw_height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
        width = raw_width if raw_width > 0 else 0
        height = raw_height if raw_height > 0 else 0

        raw_frame_count = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
        frame_count = (
            raw_frame_count
            if np.isfinite(raw_frame_count) and raw_frame_count > 0
            else 0
        )

        duration_seconds = frame_count / fps if frame_count > 0 else 0.0

        return VideoInfo(
            width=width,
            height=height,
            fps=fps,
            frame_count=frame_count,
            duration_seconds=duration_seconds,
        )

    def _validate_dimensions(self, info: VideoInfo) -> None:
        """Reject videos whose header reports unusable dimensions."""
        if info.width <= 0 or info.height <= 0:
            raise InvalidVideoError(
                f"Video has invalid dimensions: {info.width}x{info.height}"
            )

        if (
            info.width > MAX_VIDEO_DIMENSION_PIXELS
            or info.height > MAX_VIDEO_DIMENSION_PIXELS
        ):
            raise InvalidVideoError(
                "Video dimensions are too large to process safely: "
                f"{info.width}x{info.height}"
            )

    @staticmethod
    def _validate_sample_interval(sample_interval: float) -> None:
        if sample_interval <= 0:
            raise ValueError("sample_interval must be positive")

    # ------------------------------------------------------------------
    # Core pipeline
    # ------------------------------------------------------------------

    def process(
        self,
        sample_interval: float = 0.5,
        max_frames: int | None = None,
    ) -> list[ExtractedFrame]:
        """Process the video and return its important frames.

        Kept for backward compatibility with the original API. New code
        should prefer :meth:`process_with_result`, which also returns
        video info and metrics.

        Args:
            sample_interval: Seconds between sampled candidate frames.
            max_frames: Optional cap on how many frames may be saved.
        """
        return self.process_with_result(
            sample_interval=sample_interval,
            max_frames=max_frames,
        ).frames

    def process_with_result(
        self,
        sample_interval: float = 0.5,
        max_frames: int | None = None,
    ) -> VideoProcessingResult:
        """Full pipeline: validate, sample, select, extract, measure.

        Args:
            sample_interval: Seconds between sampled candidate frames.
            max_frames: Optional cap on how many frames may be saved.

        Raises:
            VideoProcessingError: If the video is missing, unreadable,
                or too short to produce meaningful screenshots.
            ValueError: If arguments are invalid.
        """
        self._validate_sample_interval(sample_interval)

        if max_frames is not None and max_frames < 1:
            raise ValueError("max_frames must be at least 1")

        metrics = ProcessingMetrics()
        metrics.start()

        video = self.open_video()
        try:
            info = self._read_video_info(video)
            self._validate_dimensions(info)

            if info.duration_seconds < MIN_VIDEO_DURATION_SECONDS:
                raise VideoProcessingError(
                    "Video is too short to process: "
                    f"{info.duration_seconds:.2f}s "
                    f"(minimum {MIN_VIDEO_DURATION_SECONDS:.0f}s)"
                )

            frames = self._scan_video(
                video,
                info,
                sample_interval,
                max_frames,
                metrics,
            )
        finally:
            video.release()

        metrics.stop()

        return VideoProcessingResult(
            frames=frames,
            info=info,
            metrics=metrics,
        )

    def _scan_video(
        self,
        video: cv2.VideoCapture,
        info: VideoInfo,
        sample_interval: float,
        max_frames: int | None,
        metrics: ProcessingMetrics,
    ) -> list[ExtractedFrame]:
        """Sample candidates and run content-driven selection over them.

        Committed representatives are saved to disk immediately (kept
        frames are never held in memory longer than one segment), so a
        2-hour lecture costs constant memory.
        """
        frame_step = max(1, int(info.fps * sample_interval))

        previous_frame: np.ndarray | None = None
        # Small version of the last *saved* frame, for slow-drift checks.
        previous_saved_small: np.ndarray | None = None

        frame_number = 0
        # Set far in the past so the first check always passes.
        last_saved_timestamp = -999.0

        selected_frames: list[ExtractedFrame] = []

        # The current dwelling segment's representative. A commit always
        # saves *this* frame — the best one seen for the visual — never
        # the frame that merely happened to end the segment.
        current_representative: tuple[float, np.ndarray, float] | None = None

        # First non-blank candidate, kept as a fallback anchor so videos
        # with no genuinely useful visuals still yield one thumbnail.
        first_candidate: tuple[float, np.ndarray, float] | None = None

        selector = self.frame_selector
        scorer = self.importance_scorer

        def commit(
            representative: tuple[float, np.ndarray, float],
        ) -> None:
            """Save a committed representative (min-gap aware)."""
            nonlocal last_saved_timestamp
            commit_time, commit_frame, commit_score = representative

            if commit_time - last_saved_timestamp < (
                self.scene_detector.min_scene_gap
            ):
                metrics.scene_changes_skipped_gap += 1
                return

            saved = self._save_frame(commit_frame, commit_time, metrics)
            selected_frames.append(
                ExtractedFrame(
                    timestamp=saved.timestamp,
                    image_path=saved.image_path,
                    width=saved.width,
                    height=saved.height,
                    file_size_bytes=saved.file_size_bytes,
                    importance=round(commit_score, 4),
                )
            )
            metrics.importance_selected += 1
            metrics.importance_scores.append(commit_score)
            last_saved_timestamp = commit_time

        while True:
            metrics.start_timer("read")
            success, frame = video.read()
            metrics.finish_active_timer()

            if not success:
                break

            metrics.frames_read += 1

            # Skip frames that are outside the sampling interval.
            if frame_number % frame_step != 0:
                frame_number += 1
                continue

            timestamp = frame_number / info.fps
            metrics.frames_analyzed += 1

            metrics.start_timer("analysis")

            is_first_frame = previous_frame is None

            # ------------------------------------------------------------
            # Candidate generation (scene detection as a gate, drift as a
            # safety net). A candidate is any frame representing a visual
            # state worth judging by the importance scorer.
            # ------------------------------------------------------------
            is_scene_change = is_first_frame or (
                self.scene_detector.is_scene_change(previous_frame, frame)
            )

            is_drift_change = (
                not is_scene_change
                and previous_saved_small is not None
                and self.scene_detector.is_scene_change(
                    previous_saved_small,
                    frame,
                )
            )

            is_candidate = is_first_frame or is_scene_change or is_drift_change

            if is_scene_change and not is_first_frame:
                metrics.scene_changes_detected += 1
            if is_drift_change:
                metrics.drift_frames_saved += 1

            metrics.finish_active_timer()

            if not is_candidate:
                previous_frame = frame
                frame_number += 1
                continue

            # ------------------------------------------------------------
            # Blank rejection first: black intros/fades are never useful.
            # ------------------------------------------------------------
            if self.scene_detector.is_blank_frame(frame):
                metrics.frames_skipped_blank += 1
                previous_frame = frame
                frame_number += 1
                continue

            # ------------------------------------------------------------
            # Importance scoring + segment selection.
            # ------------------------------------------------------------
            metrics.importance_candidates += 1

            previous_representative = current_representative

            metrics.start_timer("analysis")
            score = scorer.score_frame(frame)
            decision = selector.decide(frame, timestamp, score)
            metrics.finish_active_timer()

            if first_candidate is None:
                first_candidate = (timestamp, frame, score.score)

            if (
                decision.committed_timestamp is not None
                and previous_representative is not None
            ):
                # The previous segment ended: save its best frame.
                commit(previous_representative)

            if decision.promoted:
                # This candidate is the current segment's best so far.
                current_representative = (timestamp, frame, score.score)
                # Track a small version of the last *kept* visual so slow
                # drift (changes too small per sample to cross the
                # threshold) still triggers candidates over time.
                previous_saved_small = self.scene_detector.downscale_frame(
                    frame
                )

            previous_frame = frame
            frame_number += 1

        # End of video: commit the last dwelling segment.
        final_timestamp, _final_score = selector.flush()
        if final_timestamp is not None and current_representative is not None:
            commit(current_representative)

        # Fallback anchor: when the video contained no visually useful
        # content at all (solid colors, plain webcam), still provide one
        # representative so downstream consumers keep their thumbnail.
        if not selected_frames and first_candidate is not None:
            fallback_time, fallback_frame, fallback_score = first_candidate
            saved = self._save_frame(fallback_frame, fallback_time, metrics)
            selected_frames.append(
                ExtractedFrame(
                    timestamp=saved.timestamp,
                    image_path=saved.image_path,
                    width=saved.width,
                    height=saved.height,
                    file_size_bytes=saved.file_size_bytes,
                    importance=round(fallback_score, 4),
                )
            )
            metrics.importance_selected += 1
            metrics.importance_scores.append(fallback_score)

        # Apply the optional cap by dropping the *least important* saved
        # frames, so a limit trims quantity without losing the best.
        return self._enforce_max_frames(selected_frames, max_frames, metrics)

    @staticmethod
    def _enforce_max_frames(
        selected_frames: list[ExtractedFrame],
        max_frames: int | None,
        metrics: ProcessingMetrics,
    ) -> list[ExtractedFrame]:
        """Trim the least important saved frames down to ``max_frames``."""
        if max_frames is None or len(selected_frames) <= max_frames:
            return selected_frames

        ranked = sorted(
            selected_frames,
            key=lambda frame: frame.importance,
            reverse=True,
        )
        kept = sorted(ranked[:max_frames], key=lambda frame: frame.timestamp)
        dropped = ranked[max_frames:]

        for frame in dropped:
            image_path = Path(frame.image_path)
            image_path.unlink(missing_ok=True)

        dropped_scores = [frame.importance for frame in dropped]
        metrics.frames_saved -= len(dropped)
        metrics.importance_selected -= len(dropped)
        metrics.saved_bytes -= sum(frame.file_size_bytes for frame in dropped)
        metrics.importance_scores = [
            frame.importance for frame in kept
        ]

        return kept

    def _save_frame(
        self,
        frame: np.ndarray,
        timestamp: float,
        metrics: ProcessingMetrics,
    ) -> ExtractedFrame:
        """Save one frame and update the save-related metrics."""
        metrics.start_timer("save")
        saved_frame = self.frame_extractor.save_frame(frame, timestamp)
        metrics.finish_active_timer()

        metrics.frames_saved += 1
        metrics.saved_bytes += saved_frame.file_size_bytes
        return saved_frame
