"""Processing metrics and benchmarking for the video-processing module.

Collects timing, frame counts and image statistics for a single
processing run so performance can be measured without external
dependencies. ``ProcessingMetrics.summary()`` is deliberately a plain
``dict`` so other modules (e.g. the FastAPI layer) can serialize it or
log it without importing anything extra.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ProcessingMetrics:
    """Timing and volume counters for one video-processing run."""

    # Total wall-clock time of the whole run, in seconds.
    total_time_seconds: float = 0.0
    # Time spent decoding/reading frames from the video, in seconds.
    read_time_seconds: float = 0.0
    # Time spent on scene-change analysis, in seconds.
    analysis_time_seconds: float = 0.0
    # Time spent resizing/encoding/saving images, in seconds.
    save_time_seconds: float = 0.0

    # Video frames that were read and decoded from the file.
    frames_read: int = 0
    # Video frames that were actually analyzed (a subset of frames_read).
    frames_analyzed: int = 0
    # Scene changes that passed the threshold check.
    scene_changes_detected: int = 0
    # Scene changes rejected by the minimum-gap rule.
    scene_changes_skipped_gap: int = 0
    # Scene changes rejected because the frame looked black/blank.
    frames_skipped_blank: int = 0
    # Frames saved thanks to slow-drift detection (small changes that
    # never trigger the per-pair threshold but accumulate over time).
    drift_frames_saved: int = 0
    # Images written to disk.
    frames_saved: int = 0

    # Content-driven selection: sampled frames that entered the
    # importance-selection stage as candidates.
    importance_candidates: int = 0
    # Candidates judged visually important enough to keep.
    importance_selected: int = 0
    # Importance scores of selected frames (for mean/max reporting).
    importance_scores: list[float] = field(default_factory=list)

    # Aggregated size of the saved images, in bytes.
    saved_bytes: int = 0

    _started_at: float | None = field(default=None, repr=False)
    _active_timer: str | None = field(default=None, repr=False)
    _timer_started_at: float = field(default=0.0, repr=False)

    def start(self) -> None:
        """Start the overall run timer."""
        self._started_at = time.perf_counter()

    def stop(self) -> float:
        """Stop the overall run timer and return the elapsed seconds."""
        self.finish_active_timer()
        if self._started_at is not None:
            self.total_time_seconds = time.perf_counter() - self._started_at
            self._started_at = None
        return self.total_time_seconds

    def start_timer(self, name: str) -> None:
        """Start a named sub-timer (e.g. ``"read"``, ``"analysis"``, ``"save"``)."""
        self.finish_active_timer()
        self._active_timer = name
        self._timer_started_at = time.perf_counter()

    def finish_active_timer(self) -> None:
        """Stop the active sub-timer, if any, and add it to its bucket."""
        if self._active_timer is None:
            return
        elapsed = time.perf_counter() - self._timer_started_at
        bucket = {
            "read": "read_time_seconds",
            "analysis": "analysis_time_seconds",
            "save": "save_time_seconds",
        }.get(self._active_timer)
        if bucket is not None:
            setattr(self, bucket, getattr(self, bucket) + elapsed)
        self._active_timer = None

    @property
    def analysis_fps(self) -> float:
        """Analyzed frames per second (0 when nothing was analyzed)."""
        if self.analysis_time_seconds <= 0:
            return 0.0
        return self.frames_analyzed / self.analysis_time_seconds

    @property
    def processing_speed(self) -> float:
        """Analyzed frames per second of total wall-clock time (0 when empty)."""
        if self.total_time_seconds <= 0:
            return 0.0
        return self.frames_analyzed / self.total_time_seconds

    def summary(self) -> dict[str, Any]:
        """Return the metrics as a plain dict (JSON-friendly)."""
        return {
            "total_time_seconds": round(self.total_time_seconds, 4),
            "read_time_seconds": round(self.read_time_seconds, 4),
            "analysis_time_seconds": round(self.analysis_time_seconds, 4),
            "save_time_seconds": round(self.save_time_seconds, 4),
            "frames_read": self.frames_read,
            "frames_analyzed": self.frames_analyzed,
            "scene_changes_detected": self.scene_changes_detected,
            "scene_changes_skipped_gap": self.scene_changes_skipped_gap,
            "frames_skipped_blank": self.frames_skipped_blank,
            "drift_frames_saved": self.drift_frames_saved,
            "frames_saved": self.frames_saved,
            "importance_candidates": self.importance_candidates,
            "importance_selected": self.importance_selected,
            "mean_importance": round(
                (
                    sum(self.importance_scores) / len(self.importance_scores)
                    if self.importance_scores
                    else 0.0
                ),
                3,
            ),
            "saved_bytes": self.saved_bytes,
            "analysis_fps": round(self.analysis_fps, 2),
            "processing_speed": round(self.processing_speed, 2),
        }
