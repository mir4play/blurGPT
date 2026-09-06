"""Persistent user settings and built-in processing profiles."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import config

SETTINGS_VERSION = 1
SETTINGS_DIR = Path("config")
SETTINGS_PATH = SETTINGS_DIR / "settings.json"

DEFAULTS: dict[str, Any] = {
    "model_path": config.MODEL_PATH,
    "device": config.DEVICE,
    "detect_every": config.DETECT_EVERY,
    "imgsz": config.IMGSZ,
    "pixel_size": config.PIXEL_SIZE,
    "box_margin": config.BOX_MARGIN,
    "video_encoder": config.VIDEO_ENCODER,
    "video_codec": config.VIDEO_CODEC,
    "video_nvenc_cq": config.VIDEO_NVENC_CQ,
    "video_nvenc_preset": config.VIDEO_NVENC_PRESET,
}

# Presets describe the intended trade-off; they are copied into the editable
# controls by the GUI and are never written into config.py.
PROFILES: dict[str, dict[str, Any]] = {
    "Recommended": {
        "detect_every": 5,
        "imgsz": 640,
        "pixel_size": 10,
        "box_margin": 0,
        "video_encoder": "h264_nvenc",
        "video_codec": "mp4v",
        "video_nvenc_cq": 23,
        "video_nvenc_preset": "p4",
    },
    "Performance": {
        "detect_every": 8,
        "imgsz": 640,
        "pixel_size": 10,
        "box_margin": 0,
        "video_encoder": "h264_nvenc",
        "video_codec": "mp4v",
        "video_nvenc_cq": 25,
        "video_nvenc_preset": "p3",
    },
    "Quality": {
        "detect_every": 2,
        "imgsz": 1280,
        "pixel_size": 10,
        "box_margin": 0,
        "video_encoder": "h264_nvenc",
        "video_codec": "mp4v",
        "video_nvenc_cq": 20,
        "video_nvenc_preset": "p5",
    },
}


def profile_values(name: str) -> dict[str, Any]:
    """Return a complete settings dictionary for a built-in profile."""
    if name not in PROFILES:
        raise ValueError(f"Unknown settings profile: {name}")
    values = DEFAULTS.copy()
    values.update(PROFILES[name])
    return values


def _normalise(values: dict[str, Any]) -> dict[str, Any]:
    """Keep persisted settings limited to known keys and valid primitive types."""
    merged = DEFAULTS.copy()
    for key, value in values.items():
        if key in merged:
            merged[key] = value
    return merged


def validate_settings(values: dict[str, Any]) -> dict[str, Any]:
    """Return a normalized, safe settings dictionary for the processing engine."""
    settings = _normalise(values)

    settings["model_path"] = str(settings["model_path"])
    if not settings["model_path"].strip():
        raise ValueError("Model path cannot be empty")

    device = settings["device"]
    if device != "cpu":
        try:
            device = int(device)
        except (TypeError, ValueError) as exc:
            raise ValueError("Device must be 'cpu' or a CUDA device index") from exc
        if device < 0:
            raise ValueError("CUDA device index cannot be negative")
    settings["device"] = device

    integer_ranges = {
        "detect_every": (1, 100),
        "imgsz": (320, 4096),
        "pixel_size": (1, 100),
        "box_margin": (0, 200),
        "video_nvenc_cq": (0, 51),
    }
    for key, (minimum, maximum) in integer_ranges.items():
        try:
            value = int(settings[key])
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Invalid value for {key}") from exc
        if not minimum <= value <= maximum:
            raise ValueError(f"{key} must be between {minimum} and {maximum}")
        settings[key] = value

    if settings["imgsz"] % 32 != 0:
        raise ValueError("Inference size must be a multiple of 32")

    if settings["video_encoder"] not in {"h264_nvenc", "opencv"}:
        raise ValueError("Unsupported video encoder")
    if settings["video_codec"] != "mp4v":
        raise ValueError("Unsupported OpenCV video codec")

    preset = str(settings["video_nvenc_preset"]).lower()
    if preset not in {f"p{i}" for i in range(1, 8)}:
        raise ValueError("NVENC preset must be between p1 and p7")
    settings["video_nvenc_preset"] = preset

    return settings


def load_settings() -> dict[str, Any]:
    """Load GUI settings, creating a defaults file when none exists."""
    if not SETTINGS_PATH.exists():
        save_settings(DEFAULTS)
        return DEFAULTS.copy()

    try:
        payload = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("settings.json must contain a JSON object")
        return _normalise(payload.get("settings", payload))
    except (OSError, ValueError, json.JSONDecodeError):
        # A damaged settings file should never prevent BlurGPT from starting.
        return DEFAULTS.copy()


def save_settings(values: dict[str, Any]) -> None:
    """Persist validated GUI settings without modifying Python source files."""
    validated = validate_settings(values)
    SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": SETTINGS_VERSION,
        "settings": validated,
    }
    temporary = SETTINGS_PATH.with_suffix(".json.tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    temporary.replace(SETTINGS_PATH)


def reset_settings() -> dict[str, Any]:
    """Restore the recommended profile and persist it."""
    values = profile_values("Recommended")
    save_settings(values)
    return values
