from config import *
from tqdm import tqdm
from core.video import VideoProcessor
from core.detector import Detector
from core.pixelate import pixelate
from core.report import Stats, print_report


def main():

    # ==========================
    # Estatísticas
    # ==========================

    stats = Stats()

    # ==========================
    # Vídeo
    # ==========================

    video = VideoProcessor(
        INPUT_VIDEO,
        OUTPUT_VIDEO,
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

    detector = Detector(
        MODEL,
        DEVICE,
        DETECT_EVERY
    )

    # ==========================
    # Loop principal
    # ==========================

    while True:

        ret, frame = video.read()

        if not ret:
            break

        # Detecta
        boxes = detector.detect(frame, stats)

        # Pixeliza
        pixelate(
            frame=frame,
            boxes=boxes,
            face_class=CLASSES["face"],
            pixel_size=PIXEL_SIZE,
            stats=stats,
            margin=BOX_MARGIN
        )

        # Grava
        video.write(frame, stats)

        # Estatísticas
        stats.frame_processed()
        progress.update(1)

    # ==========================
    # Finalização
    # ==========================
    progress.close()
    video.release()

    print_report(
        stats,
        video
    )


if __name__ == "__main__":
    main()