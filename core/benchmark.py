import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from importlib import import_module

from core.backends import inspect_backend_capabilities
from core.paths import LOGS_DIR, resolve_ffmpeg


LOG_PATH = LOGS_DIR / "benchmarks.jsonl"


def _ffmpeg_version():
    """Return the version of the same FFmpeg resolution used by VideoProcessor."""
    ffmpeg_path = resolve_ffmpeg()
    if not ffmpeg_path:
        return "not available"
    try:
        run_kwargs = {
            "capture_output": True,
            "text": True,
            "timeout": 5,
            "check": False,
        }
        if sys.platform == "win32":
            # Prevent a visible console window when the GUI is frozen (windowed).
            run_kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

        result = subprocess.run(
            [str(ffmpeg_path), "-version"],
            **run_kwargs,
        )
        first_line = result.stdout.splitlines()
        return first_line[0] if first_line else "unknown"
    except (OSError, subprocess.SubprocessError):
        return "not available"


def _cpu_name():
    """Return a best-effort CPU identifier without adding a system dependency."""
    try:
        processor = str(platform.processor() or "").strip()
    except (OSError, RuntimeError):
        processor = ""
    if processor:
        return processor

    try:
        processor = str(platform.uname().processor or "").strip()
    except (AttributeError, OSError, RuntimeError):
        processor = ""
    return processor or platform.machine() or "unknown"


def _device_name(api, index):
    """Return a device name and optional diagnostic without breaking a job."""
    get_device_name = getattr(api, "get_device_name", None)
    if not callable(get_device_name):
        return None, None
    try:
        name = get_device_name(index)
        return (str(name) if name else None), None
    except Exception as exc:
        return None, f"{type(exc).__name__}: {exc}"


def collect_environment(device=0):
    """Collect local runtime and backend metadata for the processing session.

    Device-name queries are best-effort: a diagnostic failure must not prevent
    video processing or invalidate an otherwise successful benchmark record.
    """
    try:
        torch_module = import_module("torch")
    except Exception as exc:
        return {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "ffmpeg": _ffmpeg_version(),
            "cpu": _cpu_name(),
            "pytorch": None,
            "cuda": None,
            "rocm": None,
            "gpu": None,
            "cuda_device": None,
            "gpu_backend": None,
            "selected_inference_backend": "unavailable",
            "xpu_available": False,
            "xpu_gpu": None,
            "xpu_device": None,
            "cuda_probe_error": None,
            "gpu_name_error": None,
            "xpu_probe_error": None,
            "xpu_name_error": None,
            "torch_import_error": f"{type(exc).__name__}: {exc}",
        }

    capabilities = inspect_backend_capabilities(torch_module)
    gpu = None
    cuda_device = None
    gpu_name_error = None

    if capabilities.cuda_api_available:
        device_count = capabilities.cuda_api_device_count
        if isinstance(device, int) and not isinstance(device, bool) and 0 <= device < device_count:
            cuda_device = device
        else:
            cuda_device = 0
        gpu, gpu_name_error = _device_name(
            getattr(torch_module, "cuda", None),
            cuda_device,
        )

    xpu_gpu = None
    xpu_device = None
    xpu_name_error = None
    if capabilities.xpu_available:
        xpu_device = 0
        xpu_gpu, xpu_name_error = _device_name(
            getattr(torch_module, "xpu", None),
            xpu_device,
        )

    if device == "cpu":
        selected_backend = "CPU"
    elif capabilities.cuda_api_available:
        selected_backend = capabilities.cuda_api_backend_name
    else:
        selected_backend = "unavailable"

    return {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "ffmpeg": _ffmpeg_version(),
        "cpu": _cpu_name(),
        "pytorch": capabilities.pytorch_version,
        "cuda": capabilities.cuda_runtime_version,
        "rocm": capabilities.rocm_runtime_version,
        "gpu_backend": (
            capabilities.cuda_api_backend_name
            if capabilities.cuda_api_available else None
        ),
        "gpu": gpu,
        "cuda_device": cuda_device,
        "selected_inference_backend": selected_backend,
        "xpu_available": capabilities.xpu_available,
        "xpu_gpu": xpu_gpu,
        "xpu_device": xpu_device,
        "cuda_probe_error": capabilities.cuda_probe_error,
        "gpu_name_error": gpu_name_error,
        "xpu_probe_error": capabilities.xpu_probe_error,
        "xpu_name_error": xpu_name_error,
    }


def _setting(settings, name):
    """Read a setting from either a dict or the legacy config module."""
    if isinstance(settings, dict):
        return settings[name]
    return getattr(settings, name)


def write_benchmark(video_name, stats, video, settings, run_id, environment):
    """Append one structured processing record to the benchmark history."""
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    device = _setting(settings, "device")
    environment = dict(environment or {})
    environment.update(collect_environment(device))

    record = {
        "run_id": run_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "video": video_name,
        "frames": stats.frames,
        "resolution": f"{video.width}x{video.height}",
        "video_fps": round(video.fps, 3),
        "processing_fps": round(stats.fps, 3),
        "total_time_s": round(stats.total_time, 3),
        "yolo_time_s": round(stats.tempo_yolo, 3),
        "pixelation_time_s": round(stats.tempo_pixel, 3),
        "write_time_s": round(stats.tempo_write, 3),
        "encoder": video.write_backend,
        "profile": _profile_name(settings),
        "device": device,
        "detect_every": _setting(settings, "detect_every"),
        "imgsz": _setting(settings, "imgsz"),
        "model": _setting(settings, "model_path"),
        "video_encoder": _setting(settings, "video_encoder"),
        "video_codec": _setting(settings, "video_codec"),
        "nvenc_cq": _setting(settings, "video_nvenc_cq"),
        "nvenc_preset": _setting(settings, "video_nvenc_preset"),
        "pixel_size": _setting(settings, "pixel_size"),
        "box_margin": _setting(settings, "box_margin"),
        "environment": environment,
    }

    try:
        with LOG_PATH.open("a", encoding="utf-8") as log_file:
            log_file.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError as exc:
        print(f"Warning: benchmark log could not be written: {exc}")


def _profile_name(settings):
    """Identify the built-in profile represented by effective settings."""
    from core.settings import profile_name

    try:
        if isinstance(settings, dict):
            effective = settings
        else:
            keys = (
                "model_path", "device", "detect_every", "imgsz", "pixel_size",
                "box_margin", "video_encoder", "video_codec",
                "video_nvenc_cq", "video_nvenc_preset",
            )
            effective = {key: getattr(settings, key) for key in keys}
        return profile_name(effective)
    except (AttributeError, ValueError, TypeError):
        return "Custom"
