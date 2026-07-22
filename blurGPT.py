# ==========================
# BlurGPT
# ==========================
# Autor: Adler Nicolau
# Data: 21/07/2026
# Versão: 0.3.0
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
        "CUDA não está disponível.\n"
        "Consulte o README.md para instalar a versão CUDA do PyTorch."
    )

print()

def main():

    # ==========================
    # Job Manager
    # ==========================

    manager = JobManager()

    jobs = manager.find_jobs()

    if not jobs:
        print("No videos found.")
        return

    job = jobs[0]

    manager.start(job)

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
    desc="Processando",
    unit="frame"
)
    # ==========================
    # Detector
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
    # Main loop
    # ==========================

    while True:

        ret, frame = video.read()

        if not ret:
            break

        # Detection
        face_boxes = face_detector.detect(frame, stats)
        plate_boxes = plate_detector.detect(frame, stats)

        # Pixelation
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

        # Write frame
        video.write(frame, stats)

        # Statistics
        stats.frame_processed()
        progress.update(1)

    # ==========================
    # Shutdown
    # ==========================
    progress.close()
    video.release()
    manager.finish(job)

    print_report(
        stats,
        video
    )


if __name__ == "__main__":
    main()