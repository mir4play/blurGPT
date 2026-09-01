# Performance Benchmarks

This document records BlurGPT performance measurements and the decisions made from them.

## Benchmark conditions

Performance results depend on hardware, driver, software versions, input video and concurrent GPU workloads. Results are therefore reported with their test conditions rather than treated as universal figures.

## Motion-prediction benchmark

Original benchmark workload:

- Resolution: **1920 × 1080**
- Frame rate: **59.94 FPS / approximately 60 FPS**
- Total frames: **3,597**

| `DETECT_EVERY` | Processing FPS | Visual quality | Assessment |
|---:|---:|---|---|
| 1 | 31.8 | ★★★★★ | YOLO on every frame; highest detection frequency |
| 5 | 61.1 | ★★★★★ | **Recommended balance** |
| 10 | 70.1 | ★★★☆☆ | Minor prediction errors |
| 20 | 75.8 | ★☆☆☆☆ | Prediction errors become unacceptable |

`DETECT_EVERY = 5` remains the project default because it delivered the measured quality/performance balance without requiring a more complex tracker.

## Previous end-to-end baseline

A previous feature-branch run measured approximately **32.5 FPS** for 3,597 frames:

- YOLO: **39.29 s**
- Pixelation: **0.29 s**
- Video recording: **49.30 s**
- Total: **110.66 s**

That 16-video benchmark was performed while **OBS Studio was running concurrently and consuming substantial GPU resources**. It is therefore retained as historical data, but it is not a clean baseline for attributing changes to BlurGPT itself.

## Clean NVENC validation

A clean batch test was subsequently performed with OBS Studio and other significant workloads disabled. The same RTX 4060 Laptop GPU was used with FFmpeg `h264_nvenc`.

| Video | Frames | Processing time | Processing FPS |
|---|---:|---:|---:|
| GX010305.MP4 | 140,944 | 3276.24 s | 43.02 |
| GX010306.MP4 | 180,480 | 3497.77 s | 51.60 |
| GX010307.MP4 | 180,480 | 3503.44 s | 51.52 |
| GX020306.MP4 | 39,337 | 834.45 s | 47.14 |
| GX020307.MP4 | 5,785 | 111.66 s | 51.81 |
| **Total** | **547,026** | **11,223.56 s** | **48.74** |

Measured stage times for the same batch:

- YOLO: **3,575.28 s**
- Pixelation: **10.01 s**
- Video recording: **1,753.48 s**

The clean test demonstrates that the NVENC path is functioning and substantially reduces the measured recording-stage cost compared with the earlier feature-branch observation. It does **not** establish that NVENC alone caused the entire increase from ~32.5 FPS to ~48.7 FPS, because the earlier benchmark had concurrent OBS GPU load and was not an A/B comparison under identical conditions.

The current result shifts the optimization focus toward YOLO inference rather than pixelation or introducing a more complex tracker.

## Current encoding configuration

The recommended output path is:

```python
VIDEO_ENCODER = "h264_nvenc"
VIDEO_NVENC_CQ = 23
VIDEO_NVENC_PRESET = "p4"
```

The legacy compatibility path remains available:

```python
VIDEO_ENCODER = "opencv"
VIDEO_CODEC = "mp4v"
```

NVENC requires a compatible NVIDIA driver and FFmpeg build with `h264_nvenc` support.

## Benchmark logging

Each processing run can append structured records to:

```text
logs/benchmarks.jsonl
```

Records include the processing metrics, configuration and execution environment. A `run_id` groups all videos processed during the same application run. Logging failures are treated as warnings and must not invalidate an otherwise completed video-processing job.

The benchmark history is intended to make future performance comparisons reproducible. Official conclusions should still be documented here rather than relying only on raw runtime logs.

## What the benchmark does not measure

The current benchmark does not establish universal real-time capability and does not compare every YOLO model, resolution, GPU, codec or driver configuration.

For reproducible comparisons, record at least:

- GPU model and driver
- CPU model
- Python, PyTorch and Ultralytics versions
- FFmpeg version
- input resolution and FPS
- number of frames
- `DETECT_EVERY`
- `IMGSZ`
- output encoder and codec
- relevant concurrent GPU workloads

## Motion-prediction design notes

The current implementation uses lightweight linear center-motion prediction between detector results. It intentionally does not add a full multi-object tracker in this performance step.

Several interpolation strategies were considered during development, including corner interpolation, center interpolation, dynamic bounding-box scaling and fixed bounding-box size. The measured benefit did not justify the complexity of introducing a full tracker after `DETECT_EVERY = 5` had already delivered a strong quality/performance balance.

## Optimization strategy

```text
Reduce detector workload
        ↓
Benchmark the complete pipeline
        ↓
Identify the dominant remaining stage
        ↓
Optimize that stage
        ↓
Benchmark again
```

For the current audit:

```text
DETECT_EVERY = 5
        ↓
Strong quality/performance balance
        ↓
No demonstrated need for heavier tracking
        ↓
Video recording identified as a major cost
        ↓
NVENC implemented and validated
        ↓
YOLO becomes the next optimization target
```
