import time
import cv2


def pixelate(
    frame,
    boxes,
    face_class,
    pixel_size,
    stats=None,
    margin=0
):
    """
    Pixeliza todas as faces encontradas.

    Parameters
    ----------
    frame : numpy.ndarray
        Frame do vídeo.

    boxes : ultralytics.engine.results.Boxes
        Caixas retornadas pela YOLO.

    face_class : int
        Classe correspondente ao rosto.

    pixel_size : int
        Intensidade da pixelização.

    stats : Stats | None
        Objeto para medir desempenho.

    margin : int
        Margem extra ao redor da caixa.
    """

    if boxes is None:
        return frame

    t0 = time.perf_counter()

    frame_h, frame_w = frame.shape[:2]

    for box in boxes:

        cls = int(box.cls.item())

        if cls != face_class:
            continue

        x1, y1, x2, y2 = map(int, box.xyxy[0])

        # Expande a caixa
        x1 -= margin
        y1 -= margin
        x2 += margin
        y2 += margin

        # Mantém dentro da imagem
        x1 = max(0, x1)
        y1 = max(0, y1)
        x2 = min(frame_w, x2)
        y2 = min(frame_h, y2)

        roi = frame[y1:y2, x1:x2]

        if roi.size == 0:
            continue

        h, w = roi.shape[:2]

        small = cv2.resize(
            roi,
            (
                max(1, w // pixel_size),
                max(1, h // pixel_size)
            ),
            interpolation=cv2.INTER_LINEAR
        )

        pixel = cv2.resize(
            small,
            (w, h),
            interpolation=cv2.INTER_NEAREST
        )

        frame[y1:y2, x1:x2] = pixel

    if stats is not None:
        stats.tempo_pixel += time.perf_counter() - t0

    return frame