# BlurGPT

BlurGPT is a GPU-accelerated video anonymization tool that automatically detects and pixelates faces and license plates using YOLO models.

---

# Features

- 🚀 GPU acceleration (CUDA)
- 😀 Face detection
- 🚗 License plate detection
- 🟪 Pixelation anonymization
- 📹 Full HD video processing
- 📊 Processing statistics
- ⏳ Progress bar
- 🧩 Modular architecture

---

# Installation

## 1. Create a virtual environment

```bash
python -m venv .venv
```

## 2. Activate it

### Windows

```bash
.venv\Scripts\activate
```

## 3. Install PyTorch with CUDA

For NVIDIA GPUs:

```bash
python -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cu132
```

> If you don't have an NVIDIA GPU, install the CPU version of PyTorch from https://pytorch.org.

## 4. Install the remaining dependencies

```bash
pip install -r requirements.txt
```

---

## First Run

After cloning the repository, the required working folders are already included:

- input/
- processing/
- temp/
- output/
- input_archive/
- input_error/
- logs/

Simply place your videos inside the `input` folder and run:

```bash
python blurGPT.py
```

# Usage

Place one or more videos inside the `input` folder.

```text
input/
    video1.mp4
    video2.mp4
    video3.mp4
```bash
python blurGPT.py
```

BlurGPT will automatically:

Scan the `input` folder.
Move videos to processing.
Process them one by one.
Save the anonymized videos into `output`.
Archive the original videos into `input_archive`.

Interrupted jobs are automatically resumed from the `processing` folder on the next execution.

---

# Project Structure

```text
BlurGPT/

├── core/
│   ├── detector.py
│   ├── jobmanager.py
│   ├── pixelate.py
│   ├── report.py
│   └── video.py
│
├── input/
├── processing/
├── temp/
├── output/
├── input_archive/
├── input_error/
├── logs/
│
├── models/
│
├── blurGPT.py
├── config.py
├── requirements.txt
└── README.md
```

# Processing Workflow

```text
input
    │
    ▼
processing
    │
    ▼
temp
    │
    ▼
output

Original video
        │
        ▼
input_archive
```
---

# AI Models

BlurGPT currently uses two YOLO models.

## Face Detection

**yolo26s.pt**

- Custom-trained by the project author using Ultralytics Cloud.
- Training resolution: **640 × 640**
- Training epochs: **20**
- Dataset: **~19,000 face images**
- Purpose: **Face detection**

## License Plate Detection

**platesYOLOv8.pt**

- Pre-trained YOLOv8 model.
- Source:
  https://huggingface.co/Koushim/yolov8-license-plate-detection
- Purpose: **License plate detection**

> **Inference Resolution**
>
> The face detector runs at **640 px**, while the license plate detector runs at **1280 px** to improve the detection of small license plates in Full HD videos.

---

# Requirements

- Python 3.13
- CUDA-compatible NVIDIA GPU (recommended)
- PyTorch with CUDA support

---

# Current Status

Current version: **0.4.0**

Implemented:

- ✅ Face anonymization
- ✅ License plate anonymization
- ✅ CUDA acceleration
- ✅ Batch video processing
- ✅ Automatic input folder scanning
- ✅ Automatic workflow
- ✅ Safe temporary output
- ✅ Progress bar
- ✅ Performance report
- ✅ Modular architecture
- ✅ Motion Prediction

Upcoming:

- ⏳ Automatic error recovery
- ⏳ Processing logs
- ⏳ Detector performance optimizations
- ⏳ Additional anonymization methods
- ⏳ GUI

# Technologies

- Python
- OpenCV - Video processing and frame manipulation
- Ultralytics YOLO - Object detection
- PyTorch - Deep learning inference
- CUDA - GPU acceleration