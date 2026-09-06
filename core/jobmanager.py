# ==========================================================
# BlurGPT
# Job Manager
# ==========================================================

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


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
        self.input_dir = Path("input")
        self.processing_dir = Path("processing")
        self.temp_dir = Path("temp")
        self.output_dir = Path("output")
        self.archive_dir = Path("input_archive")
        self.error_dir = Path("input_error")
        self.logs_dir = Path("logs")

        for folder in (
            self.input_dir, self.processing_dir, self.temp_dir,
            self.output_dir, self.archive_dir, self.error_dir, self.logs_dir,
        ):
            folder.mkdir(parents=True, exist_ok=True)

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
