# ==========================
# BlurGPT
# ==========================
# Author: Adler Nicolau
# Date: 21/07/2026
#
# Main program
# This program gets the video in input folder, and pixelates plates and faces exporting videos to output folder.
# ==========================

import config
from config import *

import torch
from datetime import datetime, timezone
from tqdm import tqdm

from core.benchmark import collect_environment, write_benchmark
from core.detector import Detector
from core.jobmanager import JobManager
from core.pixelate import pixelate
from core.report import Stats, print_report
from core.video import VideoProcessor


# ==========================
# Environment
# ==========================

print(f"blurGPT............. {VERSION}")
print(f"PyTorch............. {torch.__version__}")

if torch.cuda.is_available():
    print(f"GPU................. {torch.cuda.get_device_name(0)}")
else:
    print("GPU................. CPU")
    raise RuntimeError(
        "CUDA is not available.\n"
        "Read README.md to install the CUDA version of PyTorch."
    )

print()


def process_job(manager, job, detector, current_job, total_jobs, run_id, environment):
    """
    Process a single job. Raises on failure so the caller can route
    the video to input_error/ and continue the batch.
    """

    print()
    print("=" * 60)
    print(f"[{current_job}/{total_jobs}] Processing: {job.filename}")
    print("=" * 60)
    print()

    stats = Stats()

    video = VideoProcessor(
        manager.get_processing_path(job),
        manager.get_temp_output_path(job),
        VIDEO_CODEC,
        VIDEO_ENCODER,
        VIDEO_NVENC_CQ,
        VIDEO_NVENC_PRESET
    )

    progress = tqdm(
        total=video.total_frames,
        desc="Processing",
        unit="frame"
    )

    # Reset per-video motion / frame state (model stays loaded)
    detector.reset()

    try:
        while True:

            ret, frame = video.read()

            if not ret:
                break

            detections = detector.detect(frame, stats)

            pixelate(
                frame=frame,
                detections=detections,
                pixel_size=PIXEL_SIZE,
                stats=stats,
                margin=BOX_MARGIN
            )

            video.write(frame, stats)

            stats.frame_processed()

            progress.update(1)

    finally:
        progress.close()
        video.release()

    manager.finish(job)

    print_report(
        stats,
        video
    )

    write_benchmark(
        job.filename,
        stats,
        video,
        config,
        run_id,
        environment
    )


def main():

    manager = JobManager()

    jobs = manager.find_jobs()

    if not jobs:
        print("No videos found.")
        return

    total_jobs = len(jobs)
    current_job = 0
    succeeded = 0
    failed = 0

    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    environment = collect_environment()

    # Load the model once for the whole batch
    detector = Detector(
        MODEL_PATH,
        DEVICE,
        DETECT_EVERY,
        IMGSZ
    )

    while True:

        jobs = manager.find_jobs()

        if not jobs:
            break

        job = jobs[0]

        manager.start(job)

        current_job += 1

        try:
            process_job(
                manager,
                job,
                detector,
                current_job,
                total_jobs,
                run_id,
                environment
            )
            succeeded += 1

        except Exception as error:
            failed += 1
            print()
            print(f"[ERROR] Job failed: {job.filename}")
            print(f"        {type(error).__name__}: {error}")
            print("        Moving to input_error/ and continuing batch...")
            print()

            try:
                manager.fail(job, error)
            except Exception as fail_error:
                print(f"[WARN] Could not fully clean up failed job: {fail_error}")

    print()
    print("Batch processing finished.")
    print(f"Succeeded...........: {succeeded}")
    print(f"Failed..............: {failed}")
    print(f"Benchmark log.......: logs/benchmarks.jsonl")
    print(f"Run id..............: {run_id}")


if __name__ == "__main__":
    main()
