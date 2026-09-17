"""Content-driven important-frame selection.

``ImportantFrameSelector`` turns a stream of *candidate* frames (sampled
frames that represent a visual state of the video) into a small set of
*selected* frames that each show one genuinely useful visual — a diagram,
chart, slide, table or formula-heavy board.

Design
------
The video is treated as a sequence of **visual segments**. While the
content stays visually the same (small changes between consecutive
candidates), the segment is *dwelling*: a talking head, a slowly panning
camera, or a slide left on screen. For every dwelling segment the
selector tracks the **best representative candidate** seen so far and
keeps improving it while better-scoring frames arrive.

A representative is *committed* (saved as a screenshot) only when:

1. the segment ends — a real visual change interrupts it — or the video
   ends (``flush``); and
2. the representative is **prominent enough**: its importance score
   exceeds an adaptive bar derived from the video's own score
   distribution, so diagram-heavy videos and talking-head videos are
   judged by their own content, not by a fixed per-minute quota.

Promotion rule: a candidate replaces the current representative only if
it scores better **and** the previous representative had a fair chance
(``min_dwell`` since promotion). This prevents slight flicker or focus
breathing from churning the representative every sample.

Nothing in this class knows about video length or frames-per-minute;
duration in, screenshots out, depends purely on the visuals.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .importance import FrameImportanceScorer, ScoreBreakdown
from .scene_detector import SceneDetector


@dataclass(frozen=True)
class SelectionDecision:
    """Outcome of feeding one candidate frame to the selector."""

    # True when this frame became the segment's (improved) representative.
    promoted: bool
    # Set when the previous representative was committed because this
    # frame starts a new visual segment.
    committed_timestamp: float | None = None
    committed_score: float = 0.0


@dataclass
class _Segment:
    """The currently dwelling visual segment."""

    representative_timestamp: float
    representative_score: float
    # Timestamp (video time) when the current representative was promoted.
    promoted_at: float
    # Highest timestamp reached inside this segment; used for dwell checks.
    last_timestamp: float


@dataclass
class ImportantFrameSelector:
    """Selects the most important representative frame per visual segment."""

    scorer: FrameImportanceScorer = field(
        default_factory=FrameImportanceScorer
    )
    # Minimum importance score (0-1) for a committed representative.
    # Calibrated on synthetic slides/diagrams (~0.11-0.55) vs talking
    # heads/whiteboards (~0.01); the adaptive bar can only raise it.
    min_importance: float = 0.08
    # How similar (0-1 combined difference) two candidates must be to
    # count as the same visual segment. Below this, the segment ends.
    segment_change_threshold: float = 0.02
    # Seconds a candidate must dwell before it may be promoted over the
    # current representative (guards against flicker/transient overlays).
    promotion_dwell: float = 0.5
    # Seconds of score improvement chance a representative gets before a
    # better candidate may replace it.
    promotion_gap: float = 1.0

    # Adaptive bookkeeping -------------------------------------------------
    _committed_scores: list[float] = field(default_factory=list)

    _segment: _Segment | None = None
    _previous_frame: np.ndarray | None = None
    # Built lazily so the threshold check stays cheap per candidate.
    _segment_change_detector: SceneDetector | None = None

    # ------------------------------------------------------------------
    # Adaptive bar
    # ------------------------------------------------------------------

    @property
    def _slide_commit_score(self) -> float:
        """Importance bar for committing a representative.

        Adapts to the video's own content: once clearly useful visuals
        have been committed, later representatives must be comparably
        good to avoid committing near-duplicates or weak frames. The
        bar never rises above what the video itself has demonstrated.
        """
        bar = self.min_importance
        if self._committed_scores:
            mean_committed = sum(self._committed_scores) / len(
                self._committed_scores
            )
            bar = max(bar, mean_committed * 0.75)
        return bar

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def decide(
        self,
        frame: np.ndarray,
        timestamp: float,
        score: ScoreBreakdown,
    ) -> SelectionDecision:
        """Feed one candidate frame; returns promotion/commit info."""
        committed_timestamp: float | None = None
        committed_score = 0.0

        is_new_segment = (
            self._previous_frame is not None
            and self._scene_changed(self._previous_frame, frame)
        )

        if is_new_segment and self._segment is not None:
            # The dwelling segment ended: commit its best representative
            # if it is prominent enough.
            committed_timestamp, committed_score = (
                self._maybe_commit_segment()
            )
            self._segment = None

        if self._segment is None:
            # Start a new segment with this candidate as representative.
            self._segment = _Segment(
                representative_timestamp=timestamp,
                representative_score=score.score,
                promoted_at=timestamp,
                last_timestamp=timestamp,
            )
        else:
            dwell = timestamp - self._segment.last_timestamp
            since_promotion = timestamp - self._segment.promoted_at
            clearly_better = (
                score.score > self._segment.representative_score + 0.05
            )

            if (
                clearly_better
                and dwell >= self.promotion_dwell
                and since_promotion >= self.promotion_gap
            ):
                # This frame shows the same visual, better: promote it.
                self._segment.representative_timestamp = timestamp
                self._segment.representative_score = score.score
                self._segment.promoted_at = timestamp

            self._segment.last_timestamp = timestamp

        self._previous_frame = frame
        return SelectionDecision(
            promoted=(
                self._segment is not None
                and self._segment.representative_timestamp == timestamp
            ),
            committed_timestamp=committed_timestamp,
            committed_score=committed_score,
        )

    def flush(
        self,
    ) -> tuple[float | None, float]:
        """Commit the final segment's representative (end of video).

        Returns ``(timestamp, score)`` or ``(None, 0.0)`` when the last
        segment did not qualify.
        """
        result = self._maybe_commit_segment()
        self._segment = None
        return result

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _scene_changed(
        self,
        previous_frame: np.ndarray,
        frame: np.ndarray,
    ) -> bool:
        if self._segment_change_detector is None:
            self._segment_change_detector = SceneDetector(
                threshold=self.segment_change_threshold,
                min_scene_gap=0.0,
            )
        return self._segment_change_detector.is_scene_change(
            previous_frame,
            frame,
        )

    def _maybe_commit_segment(
        self,
    ) -> tuple[float | None, float]:
        segment = self._segment
        if segment is None:
            return None, 0.0

        if segment.representative_score >= self._slide_commit_score:
            self._committed_scores.append(segment.representative_score)
            return segment.representative_timestamp, segment.representative_score

        return None, 0.0
