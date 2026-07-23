from core.detection import Detection


class MotionPredictor:

    def __init__(self, detect_every):

        self.detect_every = detect_every

        self.previous_detections = []
        self.last_detections = []

        self.motion = None

        self.frames_since_detection = 0

    def calculate_motion(self):
        """
        Calculates the average motion between the last two detections.
        """

        if not self.previous_detections:
            self.motion = None
            return

        if not self.last_detections:
            self.motion = None
            return

        if len(self.previous_detections) != len(self.last_detections):
            self.motion = None
            return

        self.motion = []

        for prev, curr in zip(self.previous_detections, self.last_detections):

            pcx = (prev.x1 + prev.x2) / 2
            pcy = (prev.y1 + prev.y2) / 2

            ccx = (curr.x1 + curr.x2) / 2
            ccy = (curr.y1 + curr.y2) / 2

            pw = prev.x2 - prev.x1
            ph = prev.y2 - prev.y1

            cw = curr.x2 - curr.x1
            ch = curr.y2 - curr.y1

            dx = (ccx - pcx) / self.detect_every
            dy = (ccy - pcy) / self.detect_every

            dw = (cw - pw) / self.detect_every
            dh = (ch - ph) / self.detect_every

            self.motion.append((dx, dy, dw, dh))


    def predict_detections(self):
        """
        Predicts object positions between YOLO detections
        using linear motion estimation.
        """
        if self.motion is None:
            return self.last_detections

        predicted = []

        n = self.frames_since_detection

        for detection, (dx, dy, dw, dh) in zip(
            self.last_detections,
            self.motion
        ):

            x1 = detection.x1 + dx * n
            y1 = detection.y1 + dy * n

            x2 = detection.x2 + dx * n
            y2 = detection.y2 + dy * n

            x2 += dw * n
            y2 += dh * n

            predicted.append(

                Detection(

                    cls=detection.cls,

                    x1=x1,
                    y1=y1,
                    x2=x2,
                    y2=y2

                )

            )

        return predicted

    def update(self, detections):

        self.previous_detections = self.last_detections
        self.last_detections = detections

        self.calculate_motion()

        self.frames_since_detection = 0

    def next_frame(self):

        self.frames_since_detection += 1

    def get_detections(self):

        if self.frames_since_detection == 0:
            return self.last_detections

        return self.predict_detections()