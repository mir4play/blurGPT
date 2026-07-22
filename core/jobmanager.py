# ==========================================================
# BlurGPT
# Job Manager
# ==========================================================

from dataclasses import dataclass
from pathlib import Path


# ==========================================================
# Job
# ==========================================================

@dataclass
class Job:
    """
    Represents a video waiting for processing.
    """

    filename: str
    source: str

    def __str__(self):
        return f"[{self.source}] {self.filename}"


# ==========================================================
# Job Manager
# ==========================================================

class JobManager:

    # Supported video extensions
    VIDEO_EXTENSIONS = (
        ".mp4",
        ".mov",
        ".avi",
        ".mkv",
        ".m4v",
        ".wmv"
    )

    def __init__(self):

        self.input_dir = Path("input")
        self.processing_dir = Path("processing")
        self.temp_dir = Path("temp")
        self.output_dir = Path("output")
        self.archive_dir = Path("input_archive")
        self.error_dir = Path("input_error")
        self.logs_dir = Path("logs")

    # ------------------------------------------------------

    def _list_videos(self, folder):
        """
        Returns every supported video found
        inside the given folder.
        """

        jobs = []

        if not folder.exists():
            return jobs

        for file in sorted(folder.iterdir()):

            if (
                file.is_file()
                and file.suffix.lower() in self.VIDEO_EXTENSIONS
            ):

                jobs.append(
                    Job(
                        filename=file.name,
                        source=folder.name
                    )
                )

        return jobs

    # ------------------------------------------------------

    def _path(self, folder, job):
        """
        Builds the full path for a job
        inside the given folder.
        """

        return folder / job.filename

    # ------------------------------------------------------

    def get_processing_path(self, job):
        """
        Returns the processing video path.
        """

        return self._path(self.processing_dir, job)

    # ------------------------------------------------------

    def get_temp_output_path(self, job):
        """
        Returns the temporary output path.
        """

        return self._path(self.temp_dir, job)

    # ------------------------------------------------------

    def get_output_path(self, job):
        """
        Returns the final output path.
        """

        return self._path(self.output_dir, job)

    # ------------------------------------------------------

    def get_archive_path(self, job):
        """
        Returns the archived input path.
        """

        return self._path(self.archive_dir, job)

    # ------------------------------------------------------

    def get_error_path(self, job):
        """
        Returns the failed input path.
        """

        return self._path(self.error_dir, job)

    # ------------------------------------------------------

    def find_jobs(self):
        """
        Searches for videos to process.

        Priority:

        1. processing/
        2. input/
        """

        jobs = []

        jobs.extend(
            self._list_videos(self.processing_dir)
        )

        jobs.extend(
            self._list_videos(self.input_dir)
        )

        return jobs

    # ------------------------------------------------------

    def start(self, job):
        """
        Moves a video from input/ to processing/.

        If the video is already in processing/,
        nothing is done.
        """

        if job.source == "processing":
            return

        source = self.input_dir / job.filename

        destination = self.get_processing_path(job)

        source.replace(destination)

        job.source = "processing"

        # ------------------------------------------------------

    def finish(self, job):
        """
        Finalizes a completed job.

        Moves the processed video to the output folder
        and archives the original input video.
        """

        temp_video = self.get_temp_output_path(job)
        output_video = self.get_output_path(job)

        processing_video = self.get_processing_path(job)
        archive_video = self.get_archive_path(job)

        temp_video.replace(output_video)
        processing_video.replace(archive_video)