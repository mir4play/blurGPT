# ==========================================================
# BlurGPT
# Job Manager
# ==========================================================

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import json
import shutil

from core.paths import (
    ARCHIVE_DIR,
    ERROR_DIR,
    INPUT_DIR,
    LOGS_DIR,
    OUTPUT_DIR,
    PROCESSING_DIR,
    REMOVED_DIR,
    TEMP_DIR,
    CONFIG_DIR,
)


@dataclass
class Job:
    """Represents a video waiting for processing."""

    filename: str
    source: str

    def __str__(self):
        return f"[{self.source}] {self.filename}"


class JobManager:

    VIDEO_EXTENSIONS = (
        ".mp4", ".mov", ".avi", ".mkv", ".m4v", ".wmv"
    )

    def __init__(self):
        self.input_dir = INPUT_DIR
        self.processing_dir = PROCESSING_DIR
        self.temp_dir = TEMP_DIR
        self.output_dir = OUTPUT_DIR
        self.archive_dir = ARCHIVE_DIR
        self.error_dir = ERROR_DIR
        self.removed_dir = REMOVED_DIR
        self.logs_dir = LOGS_DIR
        self.config_dir = CONFIG_DIR
        self.origins_path = self.config_dir / "queue_origins.json"

        for folder in (
            self.input_dir, self.processing_dir, self.temp_dir,
            self.output_dir, self.archive_dir, self.error_dir,
            self.removed_dir, self.logs_dir, self.config_dir,
        ):
            folder.mkdir(parents=True, exist_ok=True)

        self._origins = self._load_origins()

    def _load_origins(self) -> dict[str, str]:
        if not self.origins_path.is_file():
            return {}
        try:
            data = json.loads(self.origins_path.read_text(encoding="utf-8"))
            return {str(k): str(v) for k, v in data.items()} if isinstance(data, dict) else {}
        except (OSError, json.JSONDecodeError):
            return {}

    def _save_origins(self) -> None:
        try:
            self.origins_path.write_text(
                json.dumps(self._origins, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
        except OSError:
            pass

    def _record_origin(self, filename: str, origin: Path) -> None:
        self._origins[filename] = str(origin.resolve())
        self._save_origins()

    def _forget_origin(self, filename: str) -> None:
        if filename in self._origins:
            del self._origins[filename]
            self._save_origins()

    def _list_videos(self, folder):
        jobs = []
        if not folder.exists():
            return jobs
        for file in sorted(folder.iterdir()):
            if file.is_file() and file.suffix.lower() in self.VIDEO_EXTENSIONS:
                jobs.append(Job(filename=file.name, source=folder.name))
        return jobs

    def _path(self, folder, job):
        return folder / job.filename

    def _unique_path(self, folder, filename):
        """Return a non-existing path, preserving existing files."""
        candidate = folder / filename
        if not candidate.exists():
            return candidate

        original = Path(filename)
        counter = 1
        while True:
            candidate = folder / f"{original.stem}_{counter}{original.suffix}"
            if not candidate.exists():
                return candidate
            counter += 1

    def get_unique_input_path(self, filename):
        """Return a safe input path for a newly imported video.

        This is intentionally based on the destination filename, not the
        original source path. Two different folders may contain files with
        the same basename, so imports are renamed instead of being skipped or
        overwriting an existing queued job.
        """
        return self._unique_path(self.input_dir, filename)

    def import_from_external(self, source: Path) -> Path | None:
        """Copy an external video into input/ and remember its origin.

        Returns the destination path on success, or None if the source is
        already under input/ or the copy fails.
        """
        source = source.resolve()
        try:
            source.relative_to(self.input_dir.resolve())
            return None  # already inside input/
        except ValueError:
            pass

        if not source.is_file() or source.suffix.lower() not in self.VIDEO_EXTENSIONS:
            return None

        destination = self.get_unique_input_path(source.name)
        try:
            shutil.copy2(source, destination)
        except OSError:
            return None

        self._record_origin(destination.name, source)
        return destination

    def get_processing_path(self, job):
        return self._path(self.processing_dir, job)

    def get_temp_output_path(self, job):
        return self._path(self.temp_dir, job)

    def get_output_path(self, job):
        return self._path(self.output_dir, job)

    def get_archive_path(self, job):
        return self._path(self.archive_dir, job)

    def get_error_path(self, job):
        return self._path(self.error_dir, job)

    def find_jobs(self):
        jobs = []
        jobs.extend(self._list_videos(self.processing_dir))
        jobs.extend(self._list_videos(self.input_dir))
        return jobs

    def start(self, job):
        if job.source == "processing":
            return
        source = self.input_dir / job.filename
        destination = self.get_processing_path(job)
        source.replace(destination)
        job.source = "processing"

    def finish(self, job):
        temp_video = self.get_temp_output_path(job)
        processing_video = self.get_processing_path(job)
        output_video = self._unique_path(self.output_dir, job.filename)
        archive_video = self._unique_path(self.archive_dir, job.filename)

        temp_video.replace(output_video)
        processing_video.replace(archive_video)
        self._forget_origin(job.filename)

    def cancel(self, job):
        """Safely stop a user-cancelled job and leave it resumable."""
        processing_video = self.get_processing_path(job)
        input_video = self.input_dir / job.filename
        temp_video = self.get_temp_output_path(job)

        if temp_video.exists():
            try:
                temp_video.unlink()
            except OSError:
                pass

        if processing_video.exists() and not input_video.exists():
            processing_video.replace(input_video)
            job.source = "input"

    def fail(self, job, error):
        processing_video = self.get_processing_path(job)
        error_video = self._unique_path(self.error_dir, job.filename)
        temp_video = self.get_temp_output_path(job)

        if processing_video.exists():
            processing_video.replace(error_video)

        if temp_video.exists():
            try:
                temp_video.unlink()
            except OSError:
                pass

        log_file = self.logs_dir / "errors.log"
        timestamp = datetime.now(timezone.utc).isoformat()
        message = f"{timestamp} | {job.filename} | {type(error).__name__}: {error}\n"
        try:
            with log_file.open("a", encoding="utf-8") as f:
                f.write(message)
        except OSError:
            pass

        self._forget_origin(job.filename)

    def remove_from_queue(self, filename: str) -> bool:
        """Remove a queued input file.

        If an external origin was recorded and still exists, the working copy
        under input/ is deleted (origin remains the sole copy). Otherwise the
        file is moved to input_removed/ so a sole copy is never destroyed.
        """
        source = self.input_dir / filename
        if not source.is_file():
            return False

        origin_str = self._origins.get(filename)
        if origin_str:
            origin = Path(origin_str)
            if origin.is_file():
                try:
                    source.unlink()
                    self._forget_origin(filename)
                    return True
                except OSError:
                    pass  # fall through to move

        destination = self._unique_path(self.removed_dir, filename)
        try:
            source.replace(destination)
            self._forget_origin(filename)
            return True
        except OSError:
            return False
