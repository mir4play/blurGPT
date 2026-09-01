import json
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import torch


LOG_PATH = Path("logs/benchmarks.jsonl")


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


def _environment():
    gpu = None
    if torch.cuda.is_available():
        gpu = torch.cuda.get_device_name(0)

    return {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "pytorch": torch.__version__,
        "cuda": torch.version.cuda,
        "gpu": gpu,
        "ffmpeg": _ffmpeg_version(),
    }


def write_benchmark(video_name, stats, video, config):
    """Append one structured processing record to the benchmark history."""
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    record = {
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
        "detect_every": config.DETECT_EVERY,
        "imgsz": config.IMGSZ,
        "model": config.MODEL_PATH,
        "video_codec": config.VIDEO_CODEC,
        "nvenc_cq": config.VIDEO_NVENC_CQ,
        "nvenc_preset": config.VIDEO_NVENC_PRESET,
        "environment": _environment(),
    }

    with LOG_PATH.open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(record, ensure_ascii=False) + "\n")
