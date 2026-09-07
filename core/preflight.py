"""Pre-flight validation for a BlurGPT processing run."""

from pathlib import Path
import shutil
import subprocess

import torch

from core.paths import BUNDLED_FFMPEG_PATH, ROOT_DIR
from core.settings import load_settings, validate_settings


def _resolve_model_path(model_path):
    path = Path(model_path)
    return path if path.is_absolute() else ROOT_DIR / path


def _resolve_ffmpeg():
    bundled = Path(BUNDLED_FFMPEG_PATH)
    if bundled.is_file():
        return bundled
    system = shutil.which("ffmpeg")
    return Path(system) if system else None


def _validate_nvenc(errors):
    ffmpeg = _resolve_ffmpeg()
    if ffmpeg is None:
        errors.append(
            "NVENC encoding requires FFmpeg, but no FFmpeg executable was found.\n"
            "Bundle ffmpeg/ffmpeg.exe with BlurGPT or install FFmpeg and add it to PATH."
        )
        return

    try:
        result = subprocess.run(
            [str(ffmpeg), "-hide_banner", "-encoders"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if "h264_nvenc" not in result.stdout:
            errors.append(
                "The selected FFmpeg does not provide the h264_nvenc encoder.\n"
                "Use an FFmpeg build with NVIDIA NVENC support or select OpenCV encoding."
            )
    except (OSError, subprocess.SubprocessError) as exc:
        errors.append(f"Could not validate FFmpeg/NVENC support: {exc}")


def validate_processing_environment(settings=None):
    """Return a list of actionable errors preventing a processing run."""
    errors = []

    try:
        effective = validate_settings(settings if settings is not None else load_settings())
    except ValueError as exc:
        return [f"Settings are invalid: {exc}"]

    model_path = _resolve_model_path(effective["model_path"])
    if not model_path.is_file():
        errors.append(f"YOLO model was not found:\n{model_path}")

    if effective["video_encoder"] == "h264_nvenc":
        _validate_nvenc(errors)

    device = effective["device"]
    if device == "cpu":
        return errors

    if not torch.cuda.is_available():
        errors.append(
            "CUDA is not available, but the selected processing device is GPU.\n"
            "Choose CPU in Settings or install a CUDA-enabled PyTorch environment."
        )
        return errors

    if device >= torch.cuda.device_count():
        errors.append(
            f"CUDA device {device} is not available. "
            f"This system exposes {torch.cuda.device_count()} GPU device(s)."
        )

    return errors
