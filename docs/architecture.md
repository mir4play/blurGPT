# BlurGPT Architecture

This document describes the runtime architecture of the current BlurGPT implementation on `feature/pyside6-gui` (GUI branch; main remains 0.5.0).

## Runtime pipeline

```text
Video file
    │
    ▼
JobManager (origin-aware import/remove)
    │
    ▼
VideoProcessor (OpenCV decode + NVENC or OpenCV encode)
    │
    ▼
Detector (YOLO, loaded once per batch)
    │
    ▼
MotionPredictor (center + size; class-aware match)
    │
    ▼
Pixelation
    │
    ▼
temp/ → output/   (success)
processing/ → input_error/   (failure)
```

On success the original input is moved to `input_archive/`. On failure, `JobManager.fail()` moves the input to `input_error/`, deletes partial temp output, and appends `logs/errors.log`.

Queue Remove is origin-aware: working copy under `input/` is deleted when a known external origin still exists; otherwise it is moved to `input_removed/` (sole-copy safety).

## Module responsibilities

### `core/paths.py`

Application root resolution (`application_root()` supports `sys.frozen` for portable Windows builds). Defines all data directories. Provides the single `resolve_ffmpeg()` helper used by preflight, VideoProcessor, and benchmarks (bundled `ffmpeg/` preferred, then PATH).

### `blurGPT.py` / GUI entry

CLI and GUI share the same Qt-free `BatchProcessor`. Both call preflight before processing.

### `config.py`

Central defaults for the runtime: model path, CUDA device, detection interval, inference size, pixelation parameters, and video encoder settings (`VIDEO_ENCODER`, NVENC CQ/preset, OpenCV codec fallback). Runtime overrides live in `config/settings.json`.

### `core/jobmanager.py`

Controls the file-based job lifecycle and tracks import origins (`config/queue_origins.json`).

Supported input extensions:

```text
.mp4 .mov .avi .mkv .m4v .wmv
```

Job discovery priority: `processing/`, then `input/`.

Successful lifecycle:

```text
input/ → processing/ → temp/ → output/
processing/ → input_archive/
```

Failed lifecycle:

```text
processing/ → input_error/
temp partial → deleted
logs/errors.log ← one line
```

### `core/video.py`

Video input/output. Uses `resolve_ffmpeg()` for the encoder path. Encoding is either:

- FFmpeg pipe with `h264_nvenc`, or
- OpenCV `VideoWriter` with the configured codec.

Exposes `write_backend` for reports and benchmarks.

### `core/detector.py`

Loads Ultralytics YOLO once. Runs inference every `detect_every` frames; otherwise advances `MotionPredictor`. `reset()` clears per-video motion/frame state without reloading weights.

### `core/detection.py`

Internal detection object (`cls`, box corners, derived center/size). Isolates the rest of the app from Ultralytics types.

### `core/motion.py`

Linear motion prediction between YOLO calls:

- computes `(dx, dy, dw, dh)` per matched pair
- applies **translation and size** on intermediate frames
- matches only the **same class**, within a distance threshold based on the previous box diagonal
- unmatched detections keep the last box for that interval

No persistent track IDs and no full multi-object tracker.

### `core/pixelate.py`

Applies pixelation to `Detection` regions (`PIXEL_SIZE`, optional `BOX_MARGIN`).

### `core/report.py` / `core/benchmark.py`

In-run statistics (`perf_counter`) and append-only `logs/benchmarks.jsonl` records (FPS, component times, encoder, environment). Benchmarks also use `resolve_ffmpeg()`.

### `core/preflight.py`

Shared preflight checks (model, FFmpeg/NVENC via `resolve_ffmpeg()`, settings) used by both CLI and GUI.

## Detection model

Single YOLO model:

```text
models/blurGPT.pt
0 → license plate
1 → face
```

## Motion prediction sequence

With `DETECT_EVERY = 5`:

```text
Frame 0   → YOLO
Frame 1–4 → prediction (center + size)
Frame 5   → YOLO
```

If no valid motion estimate exists, the predictor falls back to the latest detections.

## Design boundaries

BlurGPT separates job/file management, video I/O, detection, internal detection data, motion prediction, anonymization, and reporting so each piece can evolve independently. Path and FFmpeg resolution are centralized in `core/paths.py`.

## Current limitations

- Matching is still greedy and lightweight; heavy occlusion or large jumps can produce imperfect boxes.
- Full trackers remain out of product scope unless a measured quality or FPS gain is shown.
- Concurrent GPU use (e.g. OBS) reduces processing throughput; use benchmark logs for apples-to-apples comparison.
- Portable Windows packaging is prepared via `sys.frozen` paths but not yet released as a frozen binary.
