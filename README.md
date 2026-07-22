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

# Usage

Place your input video inside the `input` folder.

Run:

```bash
python blurGPT.py
```

The processed video will be saved into the `output` folder.

---

# Project Structure

```text
BlurGPT/

├── core/
│   ├── detector.py
│   ├── pixelate.py
│   ├── report.py
│   └── video.py
│
├── input/
├── output/
├── models/
│
├── blurGPT.py
├── config.py
├── requirements.txt
└── README.md
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

Current version: **0.3.1**

Implemented:

- ✅ Face anonymization
- ✅ License plate anonymization
- ✅ CUDA acceleration
- ✅ Modular architecture
- ✅ Performance report
- ✅ Progress bar

Upcoming:

- ⏳ Batch processing
- ⏳ Automatic input folder scanning
- ⏳ Additional anonymization methods
- ⏳ Multi-threaded inference

# Technologies

- Python
- OpenCV - Video processing and frame manipulation
- Ultralytics YOLO - Object detection
- PyTorch - Deep learning inference
- CUDA - GPU acceleration