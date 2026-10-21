"""Application path resolution for source and packaged Windows builds."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path


def application_root() -> Path:
    """Return the BlurGPT application root.

    During development this is the repository root. When frozen (for example
    by PyInstaller), it is the directory containing the executable. This keeps
    the portable layout predictable and prevents the current working directory
    from changing where BlurGPT stores its files.
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


ROOT_DIR = application_root()

INPUT_DIR = ROOT_DIR / "input"
PROCESSING_DIR = ROOT_DIR / "processing"
TEMP_DIR = ROOT_DIR / "temp"
OUTPUT_DIR = ROOT_DIR / "output"
ARCHIVE_DIR = ROOT_DIR / "input_archive"
ERROR_DIR = ROOT_DIR / "input_error"
REMOVED_DIR = ROOT_DIR / "input_removed"
LOGS_DIR = ROOT_DIR / "logs"
CONFIG_DIR = ROOT_DIR / "config"
SETTINGS_PATH = CONFIG_DIR / "settings.json"
MODEL_DIR = ROOT_DIR / "models"
DEFAULT_MODEL_PATH = MODEL_DIR / "blurGPT.pt"
FFMPEG_DIR = ROOT_DIR / "ffmpeg"
BUNDLED_FFMPEG_PATH = FFMPEG_DIR / ("ffmpeg.exe" if sys.platform == "win32" else "ffmpeg")


def resolve_ffmpeg() -> Path | None:
    """Return the preferred FFmpeg executable, or None if none is available.

    Prefers the portable bundled copy next to the application root, then falls
    back to an FFmpeg found on PATH. This is the single source of truth used by
    preflight, VideoProcessor, and benchmark collection.
    """
    bundled = Path(BUNDLED_FFMPEG_PATH)
    if bundled.is_file():
        return bundled

    system = shutil.which("ffmpeg")
    return Path(system) if system else None
