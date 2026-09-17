"""Video processing package.

Public entry points:
    - ``VideoProcessor``: the main pipeline (validate, sample, select, save).
    - ``FrameImportanceScorer``: scores frames for educational-visual
      content (diagrams, slides, charts, tables).
    - ``ImportantFrameSelector``: content-driven segment selection that
      commits one representative per distinct useful visual.
    - ``SceneDetector``: scene-change detection between sampled frames.
    - ``FrameExtractor``: frame resizing, compression and saving.
    - ``ProcessingMetrics``: timing and counters for a processing run.
    - ``models``: dataclasses describing the results.
    - ``exceptions``: module error hierarchy for API-layer mapping.
"""

from .exceptions import (
    InvalidVideoError,
    VideoNotFoundError,
    VideoProcessingError,
)
from .frame_extractor import FrameExtractor
from .importance import FrameImportanceScorer, ScoreBreakdown
from .important_frame_selector import ImportantFrameSelector, SelectionDecision
from .metrics import ProcessingMetrics
from .models import ExtractedFrame, VideoInfo, VideoProcessingResult
from .scene_detector import SceneDetector
from .video_processor import VideoProcessor

__all__ = [
    "ExtractedFrame",
    "FrameExtractor",
    "FrameImportanceScorer",
    "ImportantFrameSelector",
    "InvalidVideoError",
    "ProcessingMetrics",
    "ScoreBreakdown",
    "SceneDetector",
    "SelectionDecision",
    "VideoInfo",
    "VideoNotFoundError",
    "VideoProcessor",
    "VideoProcessingError",
    "VideoProcessingResult",
]
