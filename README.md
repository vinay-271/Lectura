# lectura-video-processing

OpenCV-based video processing pipeline for **frame extraction, scene detection, visual importance scoring and representative frame selection** — my contribution to [Lectura](https://github.com/vinay-271/Lectura), a Chrome extension that turns educational YouTube videos into structured, timestamped notes.

> This repository contains **only the Video Processing / OpenCV module** (Member 3 of the Lectura team project). The FastAPI backend, AI pipeline and Chrome extension are built by other team members in the main Lectura repository.

## Purpose

Lectura's notes include key screenshots taken at meaningful moments of a video. This module is the stage of the pipeline that decides **which moments matter** and turns them into optimized images:

```
video file ──► validate ──► sample frames ──► detect scene changes / drift ──►
reject blank frames ──► score visual importance ──► select one representative
per distinct useful visual ──► resize + compress + save ──► frames + metadata + metrics
```

Selection is **content-driven, not time-driven**: a 1-minute video with 4 diagram slides yields ~4 screenshots — regardless of duration. Talking-head footage with no useful visuals yields almost none.

## Architecture

The module is a plain Python package with no web-framework dependency, so it can be imported by any caller (the Lectura API layer maps its results into the `/generate-notes` response contract — each `ExtractedFrame` supplies the `image` path and `timestamp` of a note).

```
backend/services/video_processing/
├── __init__.py                 # Public API
├── video_processor.py          # VideoProcessor — pipeline entry point
├── scene_detector.py           # SceneDetector — scene change & blank-frame detection
├── importance.py               # FrameImportanceScorer — visual importance 0-1
├── important_frame_selector.py # ImportantFrameSelector — per-segment representative selection
├── frame_extractor.py          # FrameExtractor — resizing, compression, saving
├── metrics.py                  # ProcessingMetrics — timing & counters
├── models.py                   # ExtractedFrame, VideoInfo, VideoProcessingResult
└── exceptions.py               # VideoProcessingError hierarchy
```

### Components

| Component | Responsibility |
|---|---|
| `VideoProcessor` | Validates the file, opens it with OpenCV, samples candidate frames, runs detection → scoring → selection, saves representatives, collects metrics. |
| `SceneDetector` | Compares consecutive sampled frames using a weighted mix of grayscale pixel difference (60%) and Canny edge-structure difference (40%), normalized to 0-1. Also detects black/blank frames. Analysis runs on aspect-preserving 320×180 thumbnails. |
| `FrameImportanceScorer` | Scores 0-1 how much a frame looks like a *useful educational visual* (diagram, chart, slide, table) using three OpenCV-only signals: edge-structure density (Canny), straight-line density (HoughLinesP), and high-frequency detail (Laplacian). No ML models, no network calls. |
| `ImportantFrameSelector` | Treats the video as a sequence of visual segments. While a visual dwells on screen it tracks the best-scoring representative candidate and commits it only when the segment ends and the score clears an adaptive bar derived from the video's own score distribution. Includes duplicate prevention (one representative per segment), minimum-gap enforcement, and flicker guards. |
| `FrameExtractor` | Downscales frames preserving aspect ratio with `INTER_AREA`, encodes JPEG (quality 85, optimized) or PNG (compression 6), sanitizes filenames, and never overwrites existing files. |
| `ProcessingMetrics` | Wall-clock, read/analysis/save timings, frame counters, importance statistics — `summary()` returns a JSON-ready dict. |

## Processing pipeline

1. **Validation** — path exists, is a file, opens in OpenCV, has usable dimensions (≤ 10000 px) and a minimum duration (1 s). Failures raise `VideoNotFoundError` / `InvalidVideoError` (which also subclass `FileNotFoundError` / `ValueError` for drop-in compatibility).
2. **Metadata extraction** — width, height, fps (with a safe fallback for broken headers), frame count, duration (`VideoInfo`).
3. **Sampling** — frames are read sequentially; one every `sample_interval` seconds (default 0.5) becomes a candidate.
4. **Scene-change detection** — a candidate is produced on a scene change, or when slow drift is detected against the last saved visual (catches gradual changes that never cross the per-pair threshold).
5. **Blank-frame rejection** — near-black frames (intros, fades) are counted and skipped.
6. **Importance scoring** — each candidate is scored 0-1 for educational-visual content.
7. **Representative selection** — one representative per distinct useful visual is committed when its segment ends; near-duplicates are suppressed by the adaptive bar and a 2-second minimum gap. If a video contains no useful visuals at all, a single fallback anchor frame is still provided.
8. **Image optimization** — representatives are resized to ≤ 1280×720 and written as optimized JPEGs; per-run image bytes are tracked.
9. **Max-frame cap** — `max_frames` trims the *least important* saved frames (and deletes their files), so a limit reduces quantity without losing the best screenshots.

Memory stays constant for any video length: committed representatives are saved immediately, never accumulated in RAM.

## OpenCV usage

- `cv2.VideoCapture` for decode/metadata (released in `finally` on every path)
- `cv2.resize` with `INTER_AREA` for high-quality downscaling
- `cv2.cvtColor` (BGR→GRAY), `cv2.Canny` edges, `cv2.HoughLinesP` segments, `cv2.Laplacian` high-frequency energy
- `cv2.imencode` with `IMWRITE_JPEG_QUALITY` / `IMWRITE_JPEG_OPTIMIZE` / `IMWRITE_PNG_COMPRESSION`
- Handles both OpenCV 4 (`(N,1,4)` Hough output) and OpenCV 5 (`(N,4)`)

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r backend/requirements.txt
```

```python
from services.video_processing import VideoProcessor

processor = VideoProcessor(
    video_path="lecture.mp4",
    output_dir="temp/frames",
)
result = processor.process_with_result(sample_interval=0.5, max_frames=10)

for frame in result.frames:
    print(frame.timestamp, frame.image_path, frame.importance)

print(result.info.duration_seconds)
print(result.metrics.summary())
```

## Testing

The suite (66 tests) builds synthetic educational videos **with known content** — flowcharts, bar charts, tables, formula slides, talking heads, whiteboards — via OpenCV `VideoWriter`, and asserts content-driven behavior: diagrams outscore talking heads by 5×, a 30-second single slide produces one representative, blank intros are rejected, min-gap and cap rules hold, images decode to the advertised size, and metrics stay consistent.

```bash
cd backend
python -m pytest -v
```

## Benchmarking

```bash
cd backend
python benchmarks/benchmark_video_processing.py path/to/video.mp4 --runs 3
```

Reports per-run timings, frames read/analyzed/saved, scene counts, analysis FPS and the realtime factor (measured at ~2.5× playback speed on a 60 s 1080p 24 fps sample, cv2 5.0.0).

## How this fits into Lectura

Per the [Lectura architecture](https://github.com/vinay-271/Lectura), the Chrome extension sends a YouTube URL to the FastAPI backend (`POST /generate-notes`). The backend (Member 1) obtains the transcript and the video file, hands the file to this module, and merges the returned frames (`image_path` → `image`, `timestamp`) with the AI pipeline's structured notes. This module is deliberately independent from FastAPI and the extension, communicating only through plain dataclasses and exceptions.

## License

MIT — see [LICENSE](LICENSE). The Lectura project itself is MIT-licensed by its team.
