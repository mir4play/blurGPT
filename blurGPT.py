# ==========================
# BlurGPT
# ==========================
# Autor: Adler Nicolau
# Date: 21/07/2026
#
# Main program
# This program gets the video in input folder, and pixelate plates and faces exporting videos to output folder.
# ==========================


from config import *

import torch
from tqdm import tqdm

from core.detector import Detector
from core.jobmanager import JobManager
from core.pixelate import pixelate
from core.report import Stats, print_report
from core.video import VideoProcessor



# ==========================
# Ambiente
# ==========================

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

def main():

    manager = JobManager()

    jobs = manager.find_jobs()

    if not jobs:
        print("No videos found.")
        return

    total_jobs = len(jobs)
    current_job = 0

    while True:

        jobs = manager.find_jobs()

        if not jobs:
            break

        job = jobs[0]

        manager.start(job)

        current_job += 1

        print()
        print("=" * 60)
        print(f"[{current_job}/{total_jobs}] Processing: {job.filename}")
        print("=" * 60)
        print()

        # ==========================
        # Statistics
        # ==========================

        stats = Stats()

        # ==========================
        # Video
        # ==========================

        video = VideoProcessor(
            manager.get_processing_path(job),
            manager.get_temp_output_path(job),
            VIDEO_CODEC
        )

        # ==========================
        # Progress Bar
        # ==========================

        progress = tqdm(
            total=video.total_frames,
            desc="Processing",
            unit="frame"
        )

        # ==========================
        # Detectors
        # ==========================

        face_detector = Detector(
            FACE_MODEL,
            DEVICE,
            FACE_DETECT_EVERY,
            FACE_IMGSZ
        )

        plate_detector = Detector(
            PLATE_MODEL,
            DEVICE,
            PLATE_DETECT_EVERY,
            PLATE_IMGSZ
        )

        # ==========================
        # Frame loop
        # ==========================

        while True:

            ret, frame = video.read()

            if not ret:
                break

            face_boxes = face_detector.detect(frame, stats)
            plate_boxes = plate_detector.detect(frame, stats)

            pixelate(
                frame=frame,
                boxes=face_boxes,
                target_class=CLASSES["face"],
                pixel_size=PIXEL_SIZE,
                stats=stats,
                margin=BOX_MARGIN
            )

            pixelate(
                frame=frame,
                boxes=plate_boxes,
                target_class=CLASSES["plate"],
                pixel_size=PIXEL_SIZE,
                stats=stats,
                margin=BOX_MARGIN
            )

            video.write(frame, stats)

            stats.frame_processed()

            progress.update(1)

        progress.close()

        video.release()

        manager.finish(job)

        print_report(
            stats,
            video
        )

    print()
    print("Batch processing finished.")


if __name__ == "__main__":
    main()