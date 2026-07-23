import time

from ultralytics import YOLO


class Detector:

    def __init__(self, model_path, device=0, detect_every=1, imgsz=640):

        self.model = YOLO(model_path)
        self.device = device
        self.detect_every = detect_every
        self.imgsz = imgsz

        self.last_boxes = None
        self.previous_boxes = None
        self.motion = None

        self.frame_count = 0
        self.frames_since_detection = 0

    def update_motion(self): # method to do the maths, to predict where the box would be

        if self.previous_boxes is None:
            self.motion = None
            return

        if self.last_boxes is None:
            self.motion = None
            return

        prev = self.previous_boxes.xyxy.cpu().numpy()
        curr = self.last_boxes.xyxy.cpu().numpy()

        if len(prev) != len(curr):
            self.motion = None
            return

        motion = []

        for p, c in zip(prev, curr):

            px1, py1, px2, py2 = p
            cx1, cy1, cx2, cy2 = c

            pcx = (px1 + px2) / 2
            pcy = (py1 + py2) / 2

            ccx = (cx1 + cx2) / 2
            ccy = (cy1 + cy2) / 2

            pw = px2 - px1
            ph = py2 - py1

            cw = cx2 - cx1
            ch = cy2 - cy1

            dx = (ccx - pcx) / self.detect_every
            dy = (ccy - pcy) / self.detect_every

            dw = (cw - pw) / self.detect_every
            dh = (ch - ph) / self.detect_every

            motion.append((dx, dy, dw, dh))

        self.motion = motion

    def detect(self, frame, stats=None):
        """
        Executes object detection using the loaded model.

        If detect_every > 1, detections are reused between frames
        to improve performance.
        """

        if self.frame_count % self.detect_every == 0:

            t0 = time.perf_counter()

            results = self.model.predict(
                frame,
                device=self.device,
                imgsz=self.imgsz,
                verbose=False
            )

            self.previous_boxes = self.last_boxes
            self.last_boxes = results[0].boxes

            self.update_motion()
            self.frames_since_detection = 0

            if stats is not None:
                stats.tempo_yolo += time.perf_counter() - t0

        else:
            self.frames_since_detection += 1

        self.frame_count += 1

        return self.predict_boxes() # changed from return self.last_boxes

    def predict_boxes(self):

        if self.motion is None:
            return self.last_boxes

        boxes = []

        coords = self.last_boxes.xyxy.cpu().numpy()
        classes = self.last_boxes.cls.cpu().numpy()

        for i, (dx, dy, dw, dh) in enumerate(self.motion):

            x1, y1, x2, y2 = coords[i]

            x1 += dx
            y1 += dy
            x2 += dx + dw
            y2 += dy + dh

            boxes.append({
                "cls": int(classes[i]),
                "xyxy": (
                    int(x1),
                    int(y1),
                    int(x2),
                    int(y2)
                )
            })

        return boxes