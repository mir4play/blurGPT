# BlurGPT

BlurGPT is a GPU-accelerated video anonymization tool for offline processing. It uses a YOLO object-detection model to detect faces and license plates, then pixelates the detected regions while preserving the rest of the video.

> **Project status:** active development. The current documented application version is **0.4.0**.

---

## Features

- 🚀 NVIDIA CUDA acceleration
- 😀 Face detection
- 🚗 License plate detection
- 🟪 Pixelation anonymization
- 📹 Batch processing of common video formats
- 📊 Processing statistics
- ⏳ Progress bar
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
YOLO detection
   │
   ▼
Motion prediction
   │
   ▼
Pixelation
   │
   ▼
temp/
   │
   ▼
output/
```

After a successful job, the original input is moved to `input_archive/`. A failed job can be moved to `input_error/` by the job-management workflow.

---

## Requirements

- Python **3.13**
- NVIDIA GPU with CUDA support
- PyTorch installed with CUDA support
- The Python dependencies listed in `requirements.txt`

BlurGPT currently requires CUDA at startup. If CUDA is unavailable, the application stops instead of falling back to CPU processing.

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

Place one or more supported videos in `input/` and run:

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

BlurGPT will process jobs one at a time. Videos found in `processing/` have priority over new videos in `input/`, allowing interrupted jobs to be resumed on the next execution.

---

## Configuration

Runtime settings are centralized in `config.py`. Important options include:

| Setting | Current value | Purpose |
|---|---:|---|
| `MODEL_PATH` | `models/blurGPT.pt` | YOLO model used for detection |
| `DEVICE` | `0` | First CUDA GPU |
| `DETECT_EVERY` | `5` | Run YOLO once every N frames |
| `IMGSZ` | `640` | YOLO inference image size |
| `PIXEL_SIZE` | `10` | Pixelation block size |
| `BOX_MARGIN` | `0` | Extra margin around detections |
| `VIDEO_CODEC` | `mp4v` | OpenCV output codec |
| `SHOW_VIDEO` | `False` | Display frames during processing |
| `SAVE_VIDEO` | `True` | Enable video output |
| `SHOW_REPORT` | `True` | Show processing statistics |

`DETECT_EVERY = 5` means YOLO is not executed on every frame. Between detector calls, `MotionPredictor` estimates the object position from the previous detections.

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

`MotionPredictor` estimates object movement between YOLO inference frames. It uses the center displacement and bounding-box size changes between detections and applies linear prediction to intermediate frames.

The current implementation matches detections between inference frames using nearest center distance. It intentionally does not yet implement a full multi-object tracker such as ByteTrack or BoT-SORT.

The benchmarked default is:

```python
DETECT_EVERY = 5
```

See [`docs/performance.md`](docs/performance.md) for the benchmark and its limitations.

---

## Project structure

```text
BlurGPT/
│
├── core/
│   ├── detector.py       # YOLO inference and Detection conversion
│   ├── detection.py      # Internal detection representation
│   ├── jobmanager.py     # Job discovery and file movement
│   ├── motion.py         # Motion prediction
│   ├── pixelate.py       # Anonymization
│   ├── report.py         # Processing statistics
│   └── video.py          # Video I/O
│
├── docs/
│   ├── architecture.md
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
│
├── blurGPT.py
├── config.py
├── requirements.txt
├── CHANGELOG.md
└── README.md
```

---

## Documentation

- [`docs/architecture.md`](docs/architecture.md) — runtime architecture and responsibilities of each module
- [`docs/performance.md`](docs/performance.md) — motion-prediction benchmarks and interpretation
- [`docs/roadmap.md`](docs/roadmap.md) — current development priorities and future work
- [`CHANGELOG.md`](CHANGELOG.md) — version history

---

## Current status

### Implemented

- Face anonymization
- License plate anonymization
- CUDA acceleration
- Batch video processing
- Job-based file workflow
- Temporary output workflow
- Progress reporting
- Processing statistics
- Motion prediction
- Modular architecture
- Internal `Detection` abstraction

### In development / planned

- More robust exception handling and recovery
- Further batch-processing improvements
- Improved object tracking between detector calls
- Additional anonymization methods
- GUI

---

## Technologies

- **Python** — application language
- **OpenCV** — video input/output and frame processing
- **Ultralytics YOLO** — object detection
- **PyTorch** — deep-learning inference
- **CUDA** — GPU acceleration

## License

No open-source license is currently declared in the repository. Unless a license is added, the default copyright rules apply to the project source code.
