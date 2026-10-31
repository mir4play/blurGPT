"""Pre-flight validation for a BlurGPT processing run."""

from pathlib import Path
import subprocess

from core.backends import inspect_backend_capabilities
from core.paths import DEFAULT_MODEL_PATH, ROOT_DIR, resolve_ffmpeg
from core.settings import load_settings, validate_settings


def _resolve_model_path(model_path):
    path = Path(model_path)
    return path if path.is_absolute() else ROOT_DIR / path


def _validate_nvenc(errors):
    ffmpeg = resolve_ffmpeg()
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
        errors.append(
            f"YOLO model was not found:\n{model_path}\n\n"
            f"Place the model file at:\n{DEFAULT_MODEL_PATH}"
        )

    if effective["video_encoder"] == "h264_nvenc":
        _validate_nvenc(errors)

    device = effective["device"]
    if device == "cpu":
        return errors

    capabilities = inspect_backend_capabilities()
    if not capabilities.pytorch_available:
        detail = (
            f"\nPyTorch import details: {capabilities.torch_import_error}"
            if capabilities.torch_import_error else ""
        )
        errors.append(
            "PyTorch could not be loaded, but the selected processing device is GPU.\n"
            "Choose CPU in Settings or install a compatible PyTorch build."
            f"{detail}"
        )
        return errors

    if not capabilities.cuda_api_available:
        if capabilities.xpu_available:
            errors.append(
                "Intel XPU is available in PyTorch, but BlurGPT does not yet expose "
                "XPU device selection.\n"
                "Choose CPU or use a supported CUDA/ROCm environment."
            )
        else:
            detail = (
                f"\nBackend probe details: {capabilities.cuda_probe_error}"
                if capabilities.cuda_probe_error else ""
            )
            errors.append(
                "CUDA/ROCm is not available, but the selected processing device is GPU.\n"
                "Choose CPU in Settings or install a compatible CUDA/ROCm PyTorch environment."
                f"{detail}"
            )
        return errors

    if device >= capabilities.cuda_api_device_count:
        backend_name = capabilities.cuda_api_backend_name
        errors.append(
            f"{backend_name} device {device} is not available. "
            f"This system exposes {capabilities.cuda_api_device_count} GPU device(s)."
        )

    return errors
