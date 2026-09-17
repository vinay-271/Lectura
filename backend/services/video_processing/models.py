"""Data models for the video-processing module.

Only lightweight dataclasses live here so the module stays independent
from any web framework (per the project architecture).
"""

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class ExtractedFrame:
    """A single important frame saved to disk.

    Attributes:
        timestamp: Time of the frame inside the video, in seconds.
        image_path: Path of the saved (already optimized) image.
        width: Final image width in pixels, after optional resizing.
        height: Final image height in pixels, after optional resizing.
        file_size_bytes: Size of the saved image file on disk.
        importance: Content-driven visual-importance score (0-1) of the
            saved frame, when importance selection is used. ``0.0`` when
            unknown.
    """

    timestamp: float
    image_path: str
    width: int = 0
    height: int = 0
    file_size_bytes: int = 0
    importance: float = 0.0

    @property
    def filename(self) -> str:
        return Path(self.image_path).name


@dataclass(frozen=True)
class VideoInfo:
    """Basic properties of a video, as reported by OpenCV.

    Attributes:
        width: Frame width in pixels.
        height: Frame height in pixels.
        fps: Frames per second (never <= 0; falls back to a safe default).
        frame_count: Total number of frames (negative if unknown).
        duration_seconds: Video duration in seconds (0 if unknown).
    """

    width: int
    height: int
    fps: float
    frame_count: int
    duration_seconds: float

    @property
    def is_duration_known(self) -> bool:
        return self.frame_count > 0


@dataclass
class VideoProcessingResult:
    """Everything produced by one run of ``VideoProcessor.process``.

    Attributes:
        frames: The selected important frames, in chronological order.
        info: Basic properties of the processed video.
        metrics: Timing/counters for this run (see ``metrics.py``).
    """

    frames: list[ExtractedFrame] = field(default_factory=list)
    info: VideoInfo | None = None
    metrics: "ProcessingMetrics | None" = None
