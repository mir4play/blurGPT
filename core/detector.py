import time

from ultralytics import YOLO


class Detector:

    def __init__(self, model_path, device=0, detect_every=1, imgsz=640):

        self.model = YOLO(model_path)
        self.device = device
        self.detect_every = detect_every
        self.imgsz = imgsz
        self.last_boxes = None
        self.frame_count = 0

    def detect(self, frame, stats=None):
        """
        Executa a detecção usando o modelo carregado.

        Se detect_every > 1, reutiliza as detecções
        dos frames anteriores para ganhar desempenho.
        """

        if self.frame_count % self.detect_every == 0:

            t0 = time.perf_counter()

            results = self.model.predict(
                frame,
                device=self.device,
                imgsz=self.imgsz,
                verbose=False
            )

            self.last_boxes = results[0].boxes

            if stats is not None:
                stats.tempo_yolo += time.perf_counter() - t0

        self.frame_count += 1

        return self.last_boxes