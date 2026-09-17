"""Benchmark the video-processing pipeline on a real video file.

Usage (from ``backend/``):

    python benchmarks/benchmark_video_processing.py path/to/video.mp4
    python benchmarks/benchmark_video_processing.py test.mp4 --runs 3
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.video_processing import VideoProcessor  # noqa: E402


def run_benchmark(video_path: str, runs: int, sample_interval: float) -> None:
    total_times: list[float] = []

    for run in range(1, runs + 1):
        output_dir = Path("temp/benchmark") / f"run_{run}"
        processor = VideoProcessor(
            video_path=video_path,
            output_dir=str(output_dir),
        )

        result = processor.process_with_result(sample_interval=sample_interval)
        metrics = result.metrics
        total_times.append(metrics.total_time_seconds)

        duration = result.info.duration_seconds
        speedup = duration / metrics.total_time_seconds if metrics.total_time_seconds > 0 else 0.0

        print(f"--- Run {run}/{runs} ---")
        print(f"  Video:          {duration:.1f}s, "
              f"{result.info.width}x{result.info.height} @ {result.info.fps:.1f} fps")
        print(f"  Frames read:    {metrics.frames_read}")
        print(f"  Frames analyzed:{metrics.frames_analyzed}")
        print(f"  Scenes found:   {metrics.scene_changes_detected}")
        print(f"  Frames saved:   {metrics.frames_saved}")
        print(f"  Read time:      {metrics.read_time_seconds:.3f}s")
        print(f"  Analysis time:  {metrics.analysis_time_seconds:.3f}s")
        print(f"  Save time:      {metrics.save_time_seconds:.3f}s")
        print(f"  Total time:     {metrics.total_time_seconds:.3f}s")
        print(f"  Analysis FPS:   {metrics.analysis_fps:.1f} frames/s")
        print(f"  Realtime factor:{speedup:.1f}x faster than playback")
        print()

    if len(total_times) > 1:
        mean_time = sum(total_times) / len(total_times)
        best = min(total_times)
        worst = max(total_times)
        print("=== Summary ===")
        print(f"  Runs:       {runs}")
        print(f"  Mean time:  {mean_time:.3f}s")
        print(f"  Best time:  {best:.3f}s")
        print(f"  Worst time: {worst:.3f}s")
        print(f"  Variance:   {worst - best:.3f}s")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Benchmark the Lectura video-processing pipeline.",
    )
    parser.add_argument("video", help="Path to the video file")
    parser.add_argument(
        "--runs",
        type=int,
        default=1,
        help="Number of runs (default: 1)",
    )
    parser.add_argument(
        "--sample-interval",
        type=float,
        default=0.5,
        help="Seconds between sampled frames (default: 0.5)",
    )
    args = parser.parse_args()

    run_benchmark(args.video, args.runs, args.sample_interval)


if __name__ == "__main__":
    main()
