# Result Preview
[![Example of result (YOUTUBE)](https://img.youtube.com/vi/kYm4COCCH0U/0.jpg)](https://www.youtube.com/watch?v=n8U5uIlkz40)

# BlurGPT

BlurGPT is a GPU-accelerated video anonymization tool for offline processing. It uses a YOLO object-detection model to detect faces and license plates, then pixelates the detected regions while preserving the rest of the video.

> **Project status:** active development. The current documented application version is **0.5.0**.

---

## Features

- 🚀 NVIDIA CUDA acceleration
- 🎞️ NVIDIA NVENC hardware video encoding (OpenCV fallback available)
- 😀 Face detection
- 🚗 License plate detection
- 🟪 Pixelation anonymization
- 📹 Batch processing of common video formats
- 🛡️ Failed jobs routed to `input_error/` without stopping the batch
- ♻️ YOLO model loaded once and reused across the batch
- 📊 Processing statistics and `logs/benchmarks.jsonl`
- ⏳ Progress bar
- 🖥️ PySide6 desktop GUI with queue management
- ⚙️ Persistent GUI settings and processing profiles
- 🧩 Modular architecture
- 🔄 Automatic recovery of jobs left in `processing/`

## How it works

BlurGPT processes videos through a job-based pipeline:

```text
input/
   │
   ▼
processing/
   │
   ▼
YOLO detection (every N frames)
   │
   ▼
Motion prediction (center + size, class-aware match)
   │
   ▼
Pixelation
   │
   ▼
temp/
   │
   ▼
Hardware/software encoding
   │
   ▼
output/
```

After a successful job, the original input is moved to `input_archive/`.
On failure, the input is moved to `input_error/` and a line is appended to `logs/errors.log`; the batch continues.

---

## Requirements

- Python **3.13**
- NVIDIA GPU with CUDA support
- PyTorch installed with CUDA support
- The Python dependencies listed in `requirements.txt`
- **FFmpeg with `h264_nvenc` support** when using the recommended hardware encoder

BlurGPT currently requires CUDA at startup. If CUDA is unavailable, the application stops instead of falling back to CPU processing.

### FFmpeg / NVENC

The recommended output path is NVIDIA H.264 hardware encoding through FFmpeg. Verify the encoder is available with:

```bash
ffmpeg -hide_banner -encoders | findstr nvenc
```

You should see `h264_nvenc` in the encoder list. If FFmpeg or NVENC is unavailable, the GUI can use the OpenCV `mp4v` fallback.

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/mir4play/blurGPT.git
cd blurGPT
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

### 3. Activate it

**Windows:**

```bash
.venv\Scripts\activate
```

### 4. Install PyTorch with CUDA

Install the CUDA-enabled PyTorch build appropriate for your system. For the environment currently documented by the project:

```bash
python -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cu132
```

If you use another CUDA/PyTorch combination, follow the corresponding official PyTorch installation instructions and verify that `torch.cuda.is_available()` returns `True`.

### 5. Install BlurGPT dependencies

```bash
pip install -r requirements.txt
```

---

## First run

The repository contains the working directories used by the application:

```text
input/
processing/
temp/
output/
input_archive/
input_error/
logs/
```

Place one or more supported videos in `input/` and run either the desktop GUI:

```bash
python gui.py
```

or the processing entry point:

```bash
python blurGPT.py
```

Supported video extensions are:

```text
.mp4  .mov  .avi  .mkv  .m4v  .wmv
```

### Example

```text
input/
├── video1.mp4
├── video2.mov
└── video3.mp4
```

BlurGPT processes jobs one at a time. Videos found in `processing/` have priority over new videos in `input/`, allowing an interrupted job to be picked up on the next execution.

---

## Desktop GUI

The PySide6 GUI is designed to keep heavy video processing outside the Qt event loop. Processing runs in a worker thread so the interface remains responsive during YOLO inference and video encoding.

See [`docs/gui.md`](docs/gui.md) for architecture rules, profiles, and development principles. Trackable GUI work is in the [GUI development backlog](https://github.com/mir4play/blurGPT/issues/14).

The GUI currently provides:

- Video queue with multi-selection
- Add videos without loading the complete file into RAM
- Safe removal of queued inputs without deleting the original source file
- Start and cooperative cancellation
- Progress and current-job status
- Elapsed-time heartbeat independent of frame progress
- Persistent settings
- Processing profiles: **Recommended**, **Performance**, **Quality**, and **Custom**

### Settings profiles

| Profile | Intended use | Detection | Inference | NVENC |
|---|---|---:|---:|---|
| Recommended | Balanced default | every 5 frames | 640 | CQ 23 / P4 |
| Performance | Higher throughput | every 8 frames | 640 | CQ 25 / P3 |
| Quality | More frequent/smaller-object detection | every 2 frames | 1280 | CQ 20 / P5 |
| Custom | Manual tuning | user-defined | user-defined | user-defined |

Settings changed through the GUI are stored in `config/settings.json` and do not modify `config.py`. The local settings file is intentionally ignored by Git.

The GUI settings layer is being developed toward a packaged Windows application so end users will not need to edit Python source files.

---

## Configuration

Source-level defaults remain in `config.py` for compatibility. The GUI uses the persistent runtime settings in `config/settings.json`, which are initialized from those defaults when no settings file exists.

Important settings include:

| Setting | Default | Purpose |
|---|---:|---|
| `MODEL_PATH` | `models/blurGPT.pt` | YOLO model used for detection |
| `DEVICE` | `0` | First CUDA GPU |
| `DETECT_EVERY` | `5` | Run YOLO once every N frames |
| `IMGSZ` | `640` | YOLO inference image size |
| `PIXEL_SIZE` | `10` | Pixelation block size |
| `BOX_MARGIN` | `0` | Extra margin around detections |
| `VIDEO_ENCODER` | `h264_nvenc` | Recommended FFmpeg/NVIDIA encoder |
| `VIDEO_CODEC` | `mp4v` | OpenCV fallback codec |
| `VIDEO_NVENC_CQ` | `23` | NVENC constant-quality target |
| `VIDEO_NVENC_PRESET` | `p4` | NVENC performance/quality preset |

`DETECT_EVERY = 5` means YOLO is not executed on every frame. Between detector calls, `MotionPredictor` estimates object position and size from the previous detections.

---

## AI model

The current application uses **one YOLO model** for both supported classes:

```text
models/blurGPT.pt
```

The current class mapping in `config.py` is:

| Class ID | Class |
|---:|---|
| `0` | license plate |
| `1` | face |

The model is therefore responsible for detecting both faces and license plates in the same inference pipeline.

Model training is an active area of development; training datasets and model-generation experiments are not part of the runtime installation described here.

---

## Motion prediction

`MotionPredictor` estimates object movement between YOLO inference frames using linear prediction of **center and size** (`dx`, `dy`, `dw`, `dh`).

Matching between detector calls is **lightweight** (not a full tracker):

- same class only (face↔face, plate↔plate)
- nearest center within a distance threshold based on the previous box diagonal
- unmatched objects keep their last known box for the interval

Full trackers (ByteTrack / BoT-SORT / Kalman) were evaluated and are intentionally out of scope for now: high complexity, no measured end-to-end FPS gain on this workload.

The benchmarked default is:

```python
DETECT_EVERY = 5
```

See [`docs/performance.md`](docs/performance.md) for the benchmark and its limitations.

---

## Performance strategy

The most important performance finding from the project's testing was that reducing YOLO frequency alone does not remove the remaining end-to-end bottleneck. In a 1920×1080/59.94 FPS test, the previously measured end-to-end throughput was about **32.5 FPS**, with approximately **39.3 s spent in YOLO**, **0.3 s in pixelation**, and **49.3 s in video recording** for 3,597 frames.

This means a high-value optimization target is the video-output path rather than adding increasingly complex tracking algorithms.

Version **0.5.0** adds an FFmpeg pipe using `h264_nvenc`, moving H.264 encoding to the NVIDIA GPU. The legacy OpenCV `mp4v` path remains available for compatibility.

Throughput varies with video content and system workload. Compare `logs/benchmarks.jsonl` entries with their recorded environment and run context rather than treating a single FPS number as universal.

---

## Project structure

```text
BlurGPT/
│
├── core/
│   ├── benchmark.py      # Environment capture and benchmarks.jsonl writer
│   ├── detector.py       # YOLO inference and Detection conversion
│   ├── detection.py      # Internal detection representation
│   ├── jobmanager.py     # Job discovery, finish, and fail handling
│   ├── motion.py         # Motion prediction
│   ├── pixelate.py       # Anonymization
│   ├── processor.py      # Qt-free batch engine (CLI + GUI)
│   ├── report.py         # Processing statistics
│   ├── settings.py       # Persistent runtime settings and profiles
│   └── video.py          # Video I/O and encoding
│
├── gui/
│   ├── main_window.py    # PySide6 desktop interface
│   ├── settings_dialog.py# Settings and processing profiles
│   └── worker.py         # Background processing worker
│
├── docs/
│   ├── architecture.md
│   ├── gui.md
│   ├── performance.md
│   └── roadmap.md
│
├── models/
│   └── blurGPT.pt
│
├── input/
├── processing/
├── temp/
├── output/
├── input_archive/
├── input_error/
├── logs/
├── config.py
├── gui.py
├── blurGPT.py
├── requirements.txt
├── CHANGELOG.md
├── LICENSE
└── README.md
```

---

## Documentation

- [`docs/architecture.md`](docs/architecture.md) — runtime architecture and responsibilities of each module
- [`docs/gui.md`](docs/gui.md) — desktop GUI guide and development principles
- [`docs/performance.md`](docs/performance.md) — performance benchmarks and optimization decisions
- [`docs/roadmap.md`](docs/roadmap.md) — current development priorities and future work
- [`CHANGELOG.md`](CHANGELOG.md) — version history

---

## Current status

### Implemented

- Face anonymization
- License plate anonymization
- CUDA acceleration
- NVIDIA NVENC video encoding (OpenCV fallback)
- Batch video processing with per-job failure isolation
- Job-based file workflow (`input_archive/` / `input_error/`)
- Temporary output workflow
- Progress reporting and benchmark logging
- Motion prediction with size interpolation and class-aware matching
- Detector reuse across the batch
- Model-file validation before detector initialization
- Modular architecture
- Internal `Detection` abstraction
- PySide6 desktop GUI
- Persistent GUI settings
- Processing profiles

### In development / planned

- GUI queue hardening and pre-flight checks (see issue #14)
- Model packaging improvements (Git LFS / release assets)
- First-run diagnostics and packaged Windows distribution
- Additional anonymization methods

---

## Technologies

- **Python** — application language
- **PySide6 / Qt** — desktop GUI
- **OpenCV** — video input and frame processing
- **FFmpeg** — hardware video encoding
- **Ultralytics YOLO** — object detection
- **PyTorch** — deep-learning inference
- **CUDA / NVENC** — GPU acceleration and video encoding

## License

BlurGPT is released under the **MIT License**. You may use, copy, modify, merge, publish, distribute, sublicense, and sell copies of the software for **personal or commercial purposes**, provided that the copyright notice and license notice are retained in copies or substantial portions of the software.

Copyright © 2026 Adler Nicolau dos Santos.

See [`LICENSE`](LICENSE) for the complete license text.

### Third-party components

BlurGPT depends on third-party software such as Python, PySide6, OpenCV, PyTorch, Ultralytics YOLO, and FFmpeg. Those components remain subject to their own licenses. The BlurGPT MIT license does not replace or override third-party licensing terms.
