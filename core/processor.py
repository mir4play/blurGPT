"""Reusable BlurGPT video processing engine.

The engine is deliberately Qt-free. CLI and GUI entry points can both use it.
"""

from datetime import datetime, timezone

import config

from core.benchmark import collect_environment, write_benchmark
from core.detector import Detector
from core.pixelate import pixelate
from core.report import Stats, print_report
from core.settings import load_settings
from core.video import VideoProcessor


class ProcessingCancelled(Exception):
    """Raised when the user requests a graceful cancellation."""


class BatchProcessor:
    """Process BlurGPT jobs without depending on a user interface."""

    def __init__(self, manager, progress_callback=None, status_callback=None,
                 metrics_callback=None, cancel_callback=None):
        self.manager = manager
        self.progress_callback = progress_callback
        self.status_callback = status_callback
        self.metrics_callback = metrics_callback
        self.cancel_callback = cancel_callback
        self._cancel_requested = False
        self._current_job = None
        self.settings = load_settings()

        self.run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        self.environment = collect_environment()

        self.detector = Detector(
            self.settings["model_path"],
            self.settings["device"],
            self.settings["detect_every"],
            self.settings["imgsz"],
        )

    def request_cancel(self):
        self._cancel_requested = True

    def _is_cancelled(self):
        if self._cancel_requested:
            return True
        if self.cancel_callback is not None:
            return bool(self.cancel_callback())
        return False

    def _emit_status(self, message):
        if self.status_callback is not None:
            self.status_callback(message)

    def _emit_progress(self, value):
        if self.progress_callback is not None:
            self.progress_callback(value)

    def _emit_metrics(self, stats, video):
        if self.metrics_callback is not None:
            self.metrics_callback(stats.snapshot(
                total_frames=video.total_frames,
                video_fps=video.fps,
                width=video.width,
                height=video.height,
                encoder=video.write_backend,
                device=self.settings["device"],
            ))

    def process_job(self, job, current_job, total_jobs):
        if self._is_cancelled():
            raise ProcessingCancelled

        self._current_job = job
        self._emit_status(f"Processing {current_job}/{total_jobs}: {job.filename}")
        self.manager.start(job)
        stats = Stats()

        video = VideoProcessor(
            self.manager.get_processing_path(job),
            self.manager.get_temp_output_path(job),
            self.settings["video_codec"],
            self.settings["video_encoder"],
            self.settings["video_nvenc_cq"],
            self.settings["video_nvenc_preset"],
        )

        self.detector.reset()
        self._emit_metrics(stats, video)

        try:
            while True:
                if self._is_cancelled():
                    raise ProcessingCancelled

                ret, frame = video.read()
                if not ret:
                    break

                detections = self.detector.detect(frame, stats)
                pixelate(
                    frame=frame,
                    detections=detections,
                    pixel_size=self.settings["pixel_size"],
                    stats=stats,
                    margin=self.settings["box_margin"],
                )
                video.write(frame, stats)
                stats.frame_processed()

                if video.total_frames:
                    self._emit_progress(
                        int(stats.frames / video.total_frames * 100)
                    )

                # Ten-ish UI updates per second are enough for live metrics and
                # avoid turning Qt signal delivery into part of the hot path.
                if stats.frames == 1 or stats.frames % 10 == 0:
                    self._emit_metrics(stats, video)
        finally:
            video.release()

        self.manager.finish(job)
        print_report(stats, video)
        write_benchmark(
            job.filename,
            stats,
            video,
            config,
            self.run_id,
            self.environment,
        )
        self._emit_progress(100)
        self._emit_metrics(stats, video)
        self._current_job = None

    def run(self):
        """Process the current batch and return a summary dictionary."""
        total_jobs = len(self.manager.find_jobs())
        succeeded = 0
        failed = 0

        if total_jobs == 0:
            self._emit_status("No videos found")
            return {"succeeded": 0, "failed": 0, "cancelled": False}

        for index in range(total_jobs):
            if self._is_cancelled():
                break

            jobs = self.manager.find_jobs()
            if not jobs:
                break

            job = jobs[0]

            try:
                self.process_job(job, index + 1, total_jobs)
                succeeded += 1
            except ProcessingCancelled:
                self.manager.cancel(job)
                self._emit_status("Cancellation requested — stopping safely")
                break
            except Exception as error:
                failed += 1
                self._emit_status(f"Failed: {job.filename}")
                try:
                    self.manager.fail(job, error)
                except Exception:
                    pass

        cancelled = self._is_cancelled()
        if cancelled:
            self._emit_status("Processing cancelled")
        else:
            self._emit_status(
                f"Finished — {succeeded} succeeded, {failed} failed"
            )

        return {
            "succeeded": succeeded,
            "failed": failed,
            "cancelled": cancelled,
        }
