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

        pairs = self.match_detections()

        for prev, curr in pairs:

            pcx = prev.cx
            pcy = prev.cy

            ccx = curr.cx
            ccy = curr.cy

            pw = prev.width
            ph = prev.height

            cw = curr.width
            ch = curr.height

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

            # Predict center
            cx = detection.cx + dx * n
            cy = detection.cy + dy * n

            # Predict size
            w = detection.width
            h = detection.height

            # Avoid invalid sizes
            w = max(1.0, w)
            h = max(1.0, h)

            # Rebuild bounding box
            x1 = cx - w / 2
            y1 = cy - h / 2

            x2 = cx + w / 2
            y2 = cy + h / 2

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

    def match_detections(self):
        """
        Matches current detections with previous detections
        using the nearest center distance.
        """

        pairs = []

        unused_previous = self.previous_detections.copy()

        for curr in self.last_detections:

            if not unused_previous:
                break

            best = None
            best_distance = float("inf")

            for prev in unused_previous:

                dx = prev.cx - curr.cx
                dy = prev.cy - curr.cy

                distance = dx * dx + dy * dy

                if distance < best_distance:
                    best_distance = distance
                    best = prev

            pairs.append((best, curr))
            unused_previous.remove(best)

        return pairs