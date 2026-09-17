"""Lightweight, local visual-importance scoring for candidate frames.

Scores how much a frame looks like a *useful educational visual* — a
diagram, chart, slide, table or formula-heavy board — using only OpenCV
arithmetic (no ML models, no network calls).

Three signals are combined:

1. **Edge-structure density** — diagrams and text are built from strong,
   organized edges; talking heads and plain backgrounds are mostly smooth
   gradients.
2. **Straight-line structure** — diagrams/charts/tables are dominated by
   long straight segments (axes, boxes, connectors); faces produce almost
   none.
3. **Grayscale detail** — high-frequency energy of diagrams/text (line
   drawings) is higher than for smooth photographic regions.

The score is a weighted mean, deliberately simple and interpretable so
thresholds can be tuned per project. ``explain_score`` exposes the
components for debugging.
"""

from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np


@dataclass(frozen=True)
class ScoreBreakdown:
    """The individual signals behind one importance score."""

    edge_density: float
    line_density: float
    detail: float
    score: float

    def as_dict(self) -> dict[str, float]:
        return {
            "edge_density": round(self.edge_density, 4),
            "line_density": round(self.line_density, 4),
            "detail": round(self.detail, 4),
            "score": round(self.score, 4),
        }


class FrameImportanceScorer:
    """Scores frames 0-1 for "useful educational visual" content."""

    def __init__(
        self,
        weights: tuple[float, float, float] = (0.45, 0.35, 0.20),
        analysis_width: int = 480,
        analysis_height: int = 270,
    ):
        if abs(sum(weights) - 1.0) > 1e-6:
            raise ValueError("weights must sum to 1.0")
        if any(w < 0 for w in weights):
            raise ValueError("weights cannot be negative")
        if analysis_width < 1 or analysis_height < 1:
            raise ValueError("analysis dimensions must be at least 1x1")

        self.edge_weight, self.line_weight, self.detail_weight = weights
        # Per-signal scale factors: thin-line diagram content on a large
        # canvas has inherently small raw densities (a few percent), so
        # each signal is rescaled to span a useful part of 0-1 before
        # the weighted mix. Tuned on slide/diagram vs talking-head data.
        self.edge_scale = 10.0
        self.line_scale = 10.0
        self.detail_scale = 5.0
        self.analysis_width = analysis_width
        self.analysis_height = analysis_height

        # Canny bounds follow the common low:high = 1:3 guideline.
        # Deliberately sensitive: rendered slides use thin anti-aliased
        # strokes that strict thresholds miss.
        self._canny_low = 40
        self._canny_high = 120
        # Minimum run length (px) for HoughP to count a segment as a
        # "long straight line" (box/axis/connector strokes).
        self._min_line_length = 40
        # Max gap between collinear segments to merge them.
        self._max_line_gap = 6

    # ------------------------------------------------------------------
    # Preprocessing
    # ------------------------------------------------------------------

    def _prepare(self, frame: np.ndarray) -> np.ndarray:
        """Aspect-preserving downscale + grayscale."""
        height, width = frame.shape[:2]
        scale = min(
            self.analysis_width / width,
            self.analysis_height / height,
        )
        small = cv2.resize(
            frame,
            (max(1, int(width * scale)), max(1, int(height * scale))),
            interpolation=cv2.INTER_AREA,
        )
        if small.ndim == 2:
            return small
        return cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)

    # ------------------------------------------------------------------
    # Individual signals
    # ------------------------------------------------------------------

    def _edge_density(self, gray: np.ndarray) -> float:
        edges = cv2.Canny(gray, self._canny_low, self._canny_high)
        return float(np.count_nonzero(edges)) / edges.size

    def _line_density(self, gray: np.ndarray, edges: np.ndarray) -> float:
        lines = cv2.HoughLinesP(
            edges,
            rho=1,
            theta=np.pi / 180,
            threshold=50,
            minLineLength=self._min_line_length,
            maxLineGap=self._max_line_gap,
        )
        if lines is None:
            return 0.0

        # OpenCV 4 returns shape (N, 1, 4); OpenCV 5 returns (N, 4).
        segments = lines.reshape(-1, 4)

        # Total ink length of detected segments, normalized by image
        # area so the value is comparable across resolutions.
        total_length = sum(
            np.hypot(float(x2) - float(x1), float(y2) - float(y1))
            for x1, y1, x2, y2 in segments
        )
        return float(total_length) / float(gray.shape[0] * gray.shape[1])

    def _detail(self, gray: np.ndarray) -> float:
        # Mean absolute Laplacian response: high-frequency energy.
        # Text-rich slides score ~2-4x higher than smooth photos.
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        return float(np.abs(laplacian).mean()) / 255.0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def score_frame(self, frame: np.ndarray) -> ScoreBreakdown:
        """Return the score and its components for one frame."""
        gray = self._prepare(frame)

        edge_density = self._edge_density(gray)
        edges = cv2.Canny(gray, self._canny_low, self._canny_high)
        line_density = self._line_density(gray, edges)
        detail = self._detail(gray)

        score = (
            min(1.0, edge_density * self.edge_scale) * self.edge_weight
            + min(1.0, line_density * self.line_scale) * self.line_weight
            + min(1.0, detail * self.detail_scale) * self.detail_weight
        )
        normalized_score = min(1.0, score)

        return ScoreBreakdown(
            edge_density=edge_density,
            line_density=line_density,
            detail=detail,
            score=normalized_score,
        )

    def is_important(self, frame: np.ndarray, threshold: float) -> bool:
        """Convenience wrapper: True when the frame scores >= threshold."""
        return self.score_frame(frame).score >= threshold
