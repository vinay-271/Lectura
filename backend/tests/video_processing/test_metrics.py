"""Unit tests for ``ProcessingMetrics``."""

import pytest

from services.video_processing import ProcessingMetrics


class TestTimers:
    def test_stop_records_elapsed_time(self):
        metrics = ProcessingMetrics()
        metrics.start()
        metrics.stop()

        assert metrics.total_time_seconds > 0

    def test_stop_without_start_is_safe(self):
        metrics = ProcessingMetrics()
        metrics.stop()

        assert metrics.total_time_seconds == 0.0

    def test_named_timers_accumulate_into_buckets(self):
        metrics = ProcessingMetrics()
        metrics.start()

        metrics.start_timer("read")
        metrics.finish_active_timer()
        metrics.start_timer("analysis")
        metrics.finish_active_timer()

        metrics.stop()

        assert metrics.read_time_seconds > 0
        assert metrics.analysis_time_seconds > 0
        assert metrics.save_time_seconds == 0.0

    def test_finish_without_active_timer_is_safe(self):
        metrics = ProcessingMetrics()
        metrics.finish_active_timer()

        assert metrics.total_time_seconds == 0.0

    def test_unknown_timer_name_is_ignored(self):
        metrics = ProcessingMetrics()
        metrics.start_timer("does_not_exist")
        metrics.finish_active_timer()

        assert metrics.total_time_seconds == 0.0


class TestRatesAndSummary:
    def test_rates_are_zero_when_nothing_happened(self):
        metrics = ProcessingMetrics()

        assert metrics.analysis_fps == 0.0
        assert metrics.processing_speed == 0.0

    def test_rates_are_computed(self):
        metrics = ProcessingMetrics(
            frames_analyzed=100,
            analysis_time_seconds=10.0,
            total_time_seconds=20.0,
        )

        assert metrics.analysis_fps == pytest.approx(10.0)
        assert metrics.processing_speed == pytest.approx(5.0)

    def test_summary_shape(self):
        metrics = ProcessingMetrics()
        metrics.start()
        metrics.stop()

        summary = metrics.summary()

        assert "total_time_seconds" in summary
        assert "analysis_fps" in summary
        assert "frames_saved" in summary
        # summary() must be JSON-serializable without extra work.
        assert all(
            isinstance(value, (int, float)) for value in summary.values()
        )
