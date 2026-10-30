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
- PyTorch/Ultralytics dependencies compatible with the selected inference device
- The Python dependencies listed in `requirements.txt`
- An NVIDIA GPU with a compatible CUDA-enabled PyTorch build for the **maintainer-validated reference path**
- **FFmpeg with `h264_nvenc` support** when using the recommended NVIDIA hardware encoder

The default inference device is CUDA device 0. If that selected GPU is unavailable, preflight reports an error; BlurGPT does **not** silently switch to CPU. The GUI exposes an explicit CPU option, the CPU path predates the current NVIDIA-optimized reference, but it has not been revalidated against the current packaged Windows build. It may be substantially slower.

For a CPU-only attempt, select **CPU** as the inference device and **OpenCV / mp4v** as the video encoder. The default NVENC encoder still requires a compatible NVIDIA driver and FFmpeg build. See [hardware backend status](docs/hardware-backends.md) before treating any alternative configuration as supported.

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

### 4. Install PyTorch for the selected device

For the maintainer-validated NVIDIA/CUDA reference environment, install the CUDA-enabled PyTorch build appropriate for your system. The environment currently documented by the project uses:

```bash
python -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cu132
```

For a CPU-only experiment, install a CPU-compatible PyTorch build using the official PyTorch installation selector. The CPU path is exposed in BlurGPT settings and existed in earlier project iterations, but it is not part of the current performance reference and has not been revalidated against the current packaged Windows build.

If you use another CUDA/PyTorch combination, follow the corresponding official PyTorch installation instructions and verify that `torch.cuda.is_available()` returns `True` when selecting a CUDA device.

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
| `DEVICE` | `0` | First CUDA GPU; CPU can be selected explicitly in the GUI |
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

## Hardware compatibility

The current reference configuration is NVIDIA CUDA inference with FFmpeg NVENC encoding. CPU can be selected explicitly, but it is not an automatic fallback and has not been revalidated against the current packaged Windows build. AMD/ROCm, Intel/XPU, and newer NVIDIA platforms require separate compatibility validation; no universal GPU support is claimed.

Inference hardware and video encoding are independent. A CPU-only system should select CPU inference and OpenCV `mp4v`; an NVIDIA GPU does not guarantee that its driver/FFmpeg combination can initialize NVENC.

See [`docs/hardware-backends.md`](docs/hardware-backends.md) for the source-level inventory and current validation status, and [`docs/compatibility.md`](docs/compatibility.md) for voluntary community testing instructions.

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
│   ├── compatibility.md
│   ├── hardware-backends.md
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
- [`docs/compatibility.md`](docs/compatibility.md) — volunteer hardware testing and compatibility reports
- [`docs/hardware-backends.md`](docs/hardware-backends.md) — source-level hardware backend inventory and validation status
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
- Backend portability and independent validation (see issue #61)

---

## Technologies

- **Python** — application language
- **PySide6 / Qt** — desktop GUI
- **OpenCV** — video input and frame processing
- **FFmpeg** — hardware video encoding
- **Ultralytics YOLO** — object detection
- **PyTorch** — deep-learning inference
- **CUDA / NVENC** — current reference GPU inference and video encoding path

## License

BlurGPT is released under the **MIT License**. You may use, copy, modify, merge, publish, distribute, sublicense, and sell copies of the software for **personal or commercial purposes**, provided that the copyright notice and license notice are retained in copies or substantial portions of the software.

Copyright © 2026 Adler Nicolau dos Santos.

See [`LICENSE`](LICENSE) for the complete license text.

### Third-party components

BlurGPT depends on third-party software such as Python, PySide6, OpenCV, PyTorch, Ultralytics YOLO, and FFmpeg. Those components remain subject to their own licenses. The BlurGPT MIT license does not replace or override third-party licensing terms.
