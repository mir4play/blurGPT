# ==========================
# BlurGPT
# ==========================
# Autor: Adler Nicolau
# Data: 21/07/2026
# Versão: 0.1.0
# ==========================


from config import *
from tqdm import tqdm
from core.video import VideoProcessor
from core.detector import Detector
from core.pixelate import pixelate
from core.report import Stats, print_report
import torch

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
        FACE_IMGSZ
    )

    # ==========================
    # Loop principal
    # ==========================

    while True:

        ret, frame = video.read()

        if not ret:
            break

        # Detecta
        face_boxes = face_detector.detect(frame, stats)
        plate_boxes = plate_detector.detect(frame, stats)

        # Pixeliza
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