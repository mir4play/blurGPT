# Performance Benchmarks

This document records the benchmark used to evaluate BlurGPT's motion-prediction interval.

## Test workload

- Resolution: **1920 × 1080**
- Frame rate: **60 FPS**
- Total frames: **3,597**

The benchmark compares different values of `DETECT_EVERY`.

> **Important:** FPS results are measurements from the original benchmark environment. They should not be treated as universal performance figures. GPU, CPU, driver, PyTorch, video codec and workload characteristics can materially change throughput.

## Results

| `DETECT_EVERY` | Processing FPS | Visual quality | Assessment |
|---:|---:|---|---|
| 1 | 31.8 | ★★★★★ | YOLO on every frame; highest detection frequency |
| 5 | 61.1 | ★★★★★ | **Recommended balance** |
| 10 | 70.1 | ★★★☆☆ | Minor prediction errors |
| 20 | 75.8 | ★☆☆☆☆ | Prediction errors become unacceptable |

The benchmark indicates that reducing YOLO frequency can substantially increase throughput. The gain is not linear because the remaining work—video decoding, pixelation, encoding and Python-side processing—still consumes time.

## Recommended configuration

The current default is:

```python
DETECT_EVERY = 5
IMGSZ = 640
```

`DETECT_EVERY = 5` was selected because the benchmark retained the same five-star visual-quality assessment while approximately doubling measured processing FPS relative to detection on every frame.

This is a project-level default, not a guarantee that five is optimal for every video or hardware configuration.

## What the benchmark does not measure

The benchmark is focused on the detector interval and motion-prediction behaviour. It does not establish a universal real-time capability, nor does it compare every possible YOLO model, resolution, GPU or codec.

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
- output codec

## Motion-prediction design notes

Several interpolation strategies were considered during development:

- corner interpolation
- center interpolation
- dynamic bounding-box scaling
- fixed bounding-box size

The current implementation uses linear motion prediction based primarily on changes between detector results. Bounding-box center movement and size changes are calculated and used to predict intermediate positions.

The benchmark suggested that the main quality limitation was perspective and object-motion behaviour rather than simply the interpolation formula.

## Why not a full tracker yet?

A tracker such as ByteTrack or BoT-SORT could provide persistent object identities and more robust matching between detector calls. However, introducing a tracker increases implementation and tuning complexity.

The current project therefore keeps motion prediction deliberately lightweight and postpones full object tracking until it provides a clear benefit for anonymization quality.

## Interpreting the results

The key trade-off is:

```text
More YOLO inference
        ↓
Higher detection cost
        ↓
Potentially better temporal accuracy

Less YOLO inference
        ↓
Higher throughput
        ↓
Greater dependence on prediction quality
```

`DETECT_EVERY = 5` is the current compromise between these two extremes.
