# BlurGPT Architecture

This document describes the runtime architecture of the current BlurGPT implementation.

## Runtime pipeline

```text
Video file
    │
    ▼
JobManager
    │
    ▼
VideoProcessor ───────────────┐
    │                          │
    ▼                          │
Detector (YOLO)               │
    │                          │
    ▼                          │
MotionPredictor                │
    │                          │
    ▼                          │
Pixelation ◄───────────────────┘
    │
    ▼
VideoWriter
    │
    ▼
temp/ → output/
```

The original input is moved to `input_archive/` after successful completion.

## Module responsibilities

### `blurGPT.py`

Application entry point and orchestration layer. It:

1. Creates the `JobManager`.
2. Discovers pending jobs.
3. Starts each job.
4. Creates the video processor, detector and statistics collector.
5. Reads frames in a loop.
6. Runs detection or motion prediction.
7. Pixelates detected regions.
8. Writes processed frames.
9. Finalizes the job and prints the processing report.

### `config.py`

Central configuration for the runtime. It defines the model path, CUDA device, detection interval, inference size, pixelation parameters and video output settings.

The current configuration uses:

```python
MODEL_PATH = "models/blurGPT.pt"
DEVICE = 0
DETECT_EVERY = 5
IMGSZ = 640
```

### `core/jobmanager.py`

Controls the file-based job lifecycle.

Supported input extensions:

```text
.mp4 .mov .avi .mkv .m4v .wmv
```

Job discovery gives priority to `processing/`, followed by `input/`. This allows a video already moved into `processing/` to be picked up before newly submitted videos.

The normal successful lifecycle is:

```text
input/
  ↓
processing/
  ↓
temp/
  ↓
output/

processing/ ──→ input_archive/
```

### `core/video.py`

Encapsulates video input/output operations and frame metadata used by the processing loop.

### `core/detector.py`

Loads the Ultralytics YOLO model and performs inference at the configured interval. YOLO results are converted into BlurGPT's internal `Detection` representation.

When a detector call is skipped, the detector delegates frame advancement to `MotionPredictor` instead of running another YOLO inference.

### `core/detection.py`

Defines the internal detection object used by the rest of the application. This prevents downstream modules from depending directly on Ultralytics' result objects.

### `core/motion.py`

Implements the current motion-prediction strategy. It stores the previous and latest detector results, calculates motion between them, and predicts intermediate bounding boxes using linear interpolation.

Detection matching currently uses nearest center distance. There is no persistent object ID or full tracker in the current implementation.

### `core/pixelate.py`

Applies pixelation to the regions represented by `Detection` objects. Pixelation size and optional bounding-box margin are configurable through `config.py`.

### `core/report.py`

Collects and displays processing statistics, including timing information accumulated by the processing pipeline.

## Detection model

The current runtime uses a single YOLO model:

```text
models/blurGPT.pt
```

It detects both supported classes:

```text
0 → license plate
1 → face
```

This is important because the current architecture is a **single-detector pipeline**, not a two-model face/plate pipeline.

## Motion prediction sequence

With `DETECT_EVERY = 5`, the runtime behaves conceptually like this:

```text
Frame 0   → YOLO
Frame 1   → prediction
Frame 2   → prediction
Frame 3   → prediction
Frame 4   → prediction
Frame 5   → YOLO
```

The exact predicted bounding box depends on the detections available at the preceding detector calls. If the predictor cannot establish a valid motion estimate, it falls back to the latest detections.

## Design boundaries

BlurGPT deliberately separates:

- job/file management
- video I/O
- object detection
- internal detection data
- motion prediction
- anonymization
- reporting

This separation makes it possible to replace or improve individual components without coupling the entire processing pipeline to the YOLO API.

## Current limitations

The motion predictor assumes that the set of detections can be meaningfully matched between detector calls. Changes in object count, occlusion, appearance/disappearance, or ambiguous nearest-center matches can therefore produce imperfect predictions.

A dedicated object tracker is the natural next step when prediction quality becomes the limiting factor.
