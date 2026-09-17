"""Scene-change detection for the video-processing module.

Compares consecutive sampled frames with two cheap signals:
a grayscale pixel difference and an edge-structure difference.
The detector also rejects black/blank frames so intros and fades do
not produce near-identical screenshots.
"""

from __future__ import annotations

import cv2
import numpy as np


class SceneDetector:
    """Decides whether a new sampled frame is a new visual scene."""

    def __init__(
        self,
        threshold: float = 0.02,
        min_scene_gap: float = 2.0,
        analysis_width: int = 320,
        analysis_height: int = 180,
        blank_mean_threshold: float = 6.0,
    ):
        """Create a detector.

        Args:
            threshold: Combined difference (0-1) needed to call a scene change.
            min_scene_gap: Minimum seconds between two selected frames.
            analysis_width: Width frames are shrunk to before comparing.
            analysis_height: Height frames are shrunk to before comparing.
            blank_mean_threshold: Grayscale mean below which a frame is
                considered black/blank and never selected.
        """
        if threshold <= 0:
            raise ValueError("threshold must be positive")
        if min_scene_gap < 0:
            raise ValueError("min_scene_gap cannot be negative")
        if analysis_width < 1 or analysis_height < 1:
            raise ValueError("analysis dimensions must be at least 1x1")

        self.threshold = threshold
        self.min_scene_gap = min_scene_gap
        self.analysis_width = analysis_width
        self.analysis_height = analysis_height
        self.blank_mean_threshold = blank_mean_threshold

    def _resize_for_analysis(self, frame: np.ndarray) -> np.ndarray:
        """Shrink a frame while keeping its aspect ratio."""
        height, width = frame.shape[:2]
        scale = min(
            self.analysis_width / width,
            self.analysis_height / height,
        )
        new_width = max(1, int(width * scale))
        new_height = max(1, int(height * scale))
        return cv2.resize(
            frame,
            (new_width, new_height),
            interpolation=cv2.INTER_AREA,
        )

    @staticmethod
    def _to_grayscale(small_frame: np.ndarray) -> np.ndarray:
        if small_frame.ndim == 2:
            return small_frame
        return cv2.cvtColor(small_frame, cv2.COLOR_BGR2GRAY)

    def downscale_frame(self, frame: np.ndarray) -> np.ndarray:
        """Public wrapper around the internal analysis-size resize."""
        return self._resize_for_analysis(frame)

    def is_blank_frame(self, frame: np.ndarray) -> bool:
        """Return True when a frame is (almost) completely black."""
        small = self._resize_for_analysis(frame)
        gray = self._to_grayscale(small)
        return float(gray.mean()) < self.blank_mean_threshold

    def calculate_difference(
        self,
        previous_frame: np.ndarray,
        current_frame: np.ndarray,
    ) -> float:
        """Mean grayscale pixel difference, normalized to 0-1."""
        previous_gray = self._to_grayscale(
            self._resize_for_analysis(previous_frame)
        )
        current_gray = self._to_grayscale(
            self._resize_for_analysis(current_frame)
        )

        difference = cv2.absdiff(previous_gray, current_gray)
        return float(difference.mean() / 255.0)

    def calculate_edge_difference(
        self,
        previous_frame: np.ndarray,
        current_frame: np.ndarray,
    ) -> float:
        """Edge-structure difference between two frames, normalized to 0-1."""
        previous_gray = self._to_grayscale(
            self._resize_for_analysis(previous_frame)
        )
        current_gray = self._to_grayscale(
            self._resize_for_analysis(current_frame)
        )

        previous_edges = cv2.Canny(previous_gray, 50, 150)
        current_edges = cv2.Canny(current_gray, 50, 150)

        edge_difference = cv2.absdiff(previous_edges, current_edges)
        return float(edge_difference.mean() / 255.0)

    def combined_difference(
        self,
        previous_frame: np.ndarray,
        current_frame: np.ndarray,
    ) -> float:
        """Weighted mix of pixel and edge differences."""
        pixel_difference = self.calculate_difference(
            previous_frame,
            current_frame,
        )
        edge_difference = self.calculate_edge_difference(
            previous_frame,
            current_frame,
        )
        return pixel_difference * 0.6 + edge_difference * 0.4

    def is_scene_change(
        self,
        previous_frame: np.ndarray,
        current_frame: np.ndarray,
    ) -> bool:
        """Return True when the combined difference crosses the threshold."""
        return (
            self.combined_difference(previous_frame, current_frame)
            >= self.threshold
        )
