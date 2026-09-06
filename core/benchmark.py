import json
import platform
import subprocess
from datetime import datetime, timezone

import torch

from core.paths import LOGS_DIR


LOG_PATH = LOGS_DIR / "benchmarks.jsonl"


def _ffmpeg_version():
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        first_line = result.stdout.splitlines()
        return first_line[0] if first_line else "unknown"
    except (FileNotFoundError, subprocess.SubprocessError):
        return "not available"


def collect_environment(device=0):
    """Collect the runtime environment used by the processing session."""
    gpu = None
    cuda_device = None

    if torch.cuda.is_available():
        if isinstance(device, int) and 0 <= device < torch.cuda.device_count():
            cuda_device = device
        else:
            cuda_device = 0
        gpu = torch.cuda.get_device_name(cuda_device)

    return {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "pytorch": torch.__version__,
        "cuda": torch.version.cuda,
        "gpu": gpu,
        "cuda_device": cuda_device,
        "ffmpeg": _ffmpeg_version(),
    }


def write_benchmark(video_name, stats, video, settings, run_id, environment):
    """Append one structured processing record to the benchmark history."""
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    # The benchmark must describe the effective configuration, not merely the
    # environment captured before processing started.
    environment = dict(environment or {})
    environment.update(collect_environment(settings["device"]))

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
        "device": settings["device"],
        "detect_every": settings["detect_every"],
        "imgsz": settings["imgsz"],
        "model": settings["model_path"],
        "video_encoder": settings["video_encoder"],
        "video_codec": settings["video_codec"],
        "nvenc_cq": settings["video_nvenc_cq"],
        "nvenc_preset": settings["video_nvenc_preset"],
        "pixel_size": settings["pixel_size"],
        "box_margin": settings["box_margin"],
        "environment": environment,
    }

    try:
        with LOG_PATH.open("a", encoding="utf-8") as log_file:
            log_file.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError as exc:
        print(f"Warning: benchmark log could not be written: {exc}")


def _profile_name(settings):
    """Identify the built-in profile represented by the effective settings."""
    from core.settings import profile_name

    try:
        return profile_name(settings)
    except ValueError:
        return "Custom"
