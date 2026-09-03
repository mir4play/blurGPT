import time

from ultralytics import YOLO
from core.detection import Detection
from core.motion import MotionPredictor


class Detector:

    def __init__(self, model_path, device=0, detect_every=1, imgsz=640):

        self.model = YOLO(model_path)
        self.device = device
        self.detect_every = detect_every
        self.imgsz = imgsz

        self.predictor = MotionPredictor(detect_every)

        self.frame_count = 0

    def reset(self):
        """
        Resets per-video state so the same Detector instance
        can process multiple jobs without reloading the model.
        """

        self.predictor.reset()
        self.frame_count = 0

    def detect(self, frame, stats=None):

        if self.frame_count % self.detect_every == 0:

            t0 = time.perf_counter()

            results = self.model.predict(
                frame,
                device=self.device,
                imgsz=self.imgsz,
                verbose=False
            )

            detections = self.create_detections(results[0].boxes)

            self.predictor.update(detections)

            if stats is not None:
                stats.tempo_yolo += time.perf_counter() - t0

        else:

            self.predictor.next_frame()

        self.frame_count += 1

        return self.predictor.get_detections()

    def create_detections(self, boxes):
        """
        Creates internal Detection objects from YOLO output.
        """

        if boxes is None:
            return []

        detections = []

        coords = boxes.xyxy.cpu().numpy()
        classes = boxes.cls.cpu().numpy()

        for cls, (x1, y1, x2, y2) in zip(classes, coords):

            detections.append(
                Detection(
                    cls=int(cls),
                    x1=float(x1),
                    y1=float(y1),
                    x2=float(x2),
                    y2=float(y2)
                )
            )

        return detections
