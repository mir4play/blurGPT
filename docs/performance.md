# Performance Benchmarks

This document records the benchmark used to evaluate BlurGPT's motion-prediction interval and the subsequent end-to-end performance audit.

## Test workload

- Resolution: **1920 × 1080**
- Frame rate: **59.94 FPS / approximately 60 FPS**
- Total frames: **3,597**

The benchmark compares different values of `DETECT_EVERY`.

> **Important:** FPS results are measurements from the original benchmark environment. They should not be treated as universal performance figures. GPU, CPU, driver, PyTorch, video codec and workload characteristics can materially change throughput.

## Motion-prediction results

| `DETECT_EVERY` | Processing FPS | Visual quality | Assessment |
|---:|---:|---|---|
| 1 | 31.8 | ★★★★★ | YOLO on every frame; highest detection frequency |
| 5 | 61.1 | ★★★★★ | **Recommended balance** |
| 10 | 70.1 | ★★★☆☆ | Minor prediction errors |
| 20 | 75.8 | ★☆☆☆☆ | Prediction errors become unacceptable |

The benchmark indicates that reducing YOLO frequency can substantially increase throughput. The gain is not linear because the remaining work—video decoding, pixelation, encoding and Python-side processing—still consumes time.

## End-to-end audit

A separate end-to-end test using the feature branch measured approximately **32.5 FPS** for the complete processing pipeline:

- YOLO: **39.29 s**
- Pixelation: **0.29 s**
- Video recording: **49.30 s**
- Total: **110.66 s**
- Frames: **3,597**

The result is important because the detector-only benchmark can make the optimization target appear to be YOLO. In the actual pipeline, video recording was the larger individual timed component.

Therefore, after `DETECT_EVERY = 5`, the highest-value optimization target is video encoding rather than a more sophisticated tracker.

## Current optimization

The performance-audit branch adds an optional FFmpeg pipe using NVIDIA's `h264_nvenc` encoder. This moves H.264 encoding from the CPU/OpenCV `mp4v` path to the NVIDIA hardware encoder.

Default configuration:

```python
VIDEO_ENCODER = "h264_nvenc"
VIDEO_NVENC_CQ = 23
VIDEO_NVENC_PRESET = "p4"
```

The legacy path remains available:

```python
VIDEO_ENCODER = "opencv"
VIDEO_CODEC = "mp4v"
```

This change must be benchmarked on the user's actual machine before claiming a specific FPS improvement. The objective is to reduce the recording component observed in the end-to-end profile; it is not assumed in advance that encoding is the only remaining bottleneck.

## Recommended detection configuration

The current default remains:

```python
DETECT_EVERY = 5
IMGSZ = 640
```

`DETECT_EVERY = 5` was selected because the benchmark retained the same five-star visual-quality assessment while approximately doubling measured processing FPS relative to detection on every frame.

This is a project-level default, not a guarantee that five is optimal for every video or hardware configuration.

## What the benchmark does not measure

The original benchmark does not establish a universal real-time capability, nor does it compare every possible YOLO model, resolution, GPU or codec.

For reproducible future comparisons, record at least:

- GPU model
- CPU model
- Python version
- PyTorch version
- Ultralytics version
- input resolution and FPS
- number of frames
- `DETECT_EVERY`
- `IMGSZ`
- output encoder and codec

## Motion-prediction design notes

Several interpolation strategies were considered during development:

- corner interpolation
- center interpolation
- dynamic bounding-box scaling
- fixed bounding-box size

The current implementation uses lightweight linear center-motion prediction between detector results. It intentionally does not add a full multi-object tracker in this performance step.

The benchmark suggested that the main quality limitation was perspective and object-motion behaviour rather than simply the interpolation formula.

## Why not a full tracker yet?

A tracker such as ByteTrack or BoT-SORT could provide persistent object identities and more robust matching between detector calls. However, introducing a tracker increases implementation and tuning complexity.

The current project keeps motion prediction deliberately lightweight because `DETECT_EVERY = 5` already delivered the measured quality/performance balance. A more complex tracker should only be introduced when a benchmark demonstrates a meaningful anonymization-quality or end-to-end performance gain.

## Interpreting the results

```text
Reduce YOLO frequency
        ↓
Less detector work
        ↓
Higher throughput

Then profile the whole pipeline
        ↓
Find the next dominant component
        ↓
Optimize that component
```

For the current benchmark, this led to the following sequence:

```text
DETECT_EVERY = 5
        ↓
Good quality / major YOLO reduction
        ↓
No demonstrated benefit from heavier tracking
        ↓
Video recording becomes a major bottleneck
        ↓
Use NVENC hardware encoding
```
