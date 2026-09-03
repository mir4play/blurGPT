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

        pairs = self.match_detections()

        # Build motion only for successfully matched pairs.
        # Unmatched objects keep motion = None for that slot so
        # predict_detections falls back to the last known box.
        self.motion = []

        for prev, curr in pairs:

            if prev is None:
                self.motion.append(None)
                continue

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

        # If nothing was matched at all, disable prediction for this interval.
        if all(m is None for m in self.motion):
            self.motion = None

    def predict_detections(self):
        """
        Predicts object positions between YOLO detections
        using linear motion estimation (center + size).
        """

        if self.motion is None:
            return self.last_detections

        predicted = []

        n = self.frames_since_detection

        for detection, motion in zip(
            self.last_detections,
            self.motion
        ):

            if motion is None:
                # No reliable match for this object — keep last box
                predicted.append(detection)
                continue

            dx, dy, dw, dh = motion

            # Predict center
            cx = detection.cx + dx * n
            cy = detection.cy + dy * n

            # Predict size (was previously ignored)
            w = max(1.0, detection.width + dw * n)
            h = max(1.0, detection.height + dh * n)

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
        Matches current detections with previous detections.

        Lightweight rules (no full tracker):
        - only same class (face↔face, plate↔plate)
        - nearest center within a distance threshold based on the
          previous box diagonal
        - greedy assignment
        """

        pairs = []

        unused_previous = list(self.previous_detections)

        for curr in self.last_detections:

            best = None
            best_distance = float("inf")

            for prev in unused_previous:

                # Same class only
                if prev.cls != curr.cls:
                    continue

                dx = prev.cx - curr.cx
                dy = prev.cy - curr.cy
                distance = (dx * dx + dy * dy) ** 0.5

                # Distance threshold: previous box diagonal * 1.5
                prev_diag = (prev.width ** 2 + prev.height ** 2) ** 0.5
                max_dist = max(prev_diag * 1.5, 30.0)

                if distance < best_distance and distance <= max_dist:
                    best_distance = distance
                    best = prev

            pairs.append((best, curr))

            if best is not None:
                unused_previous.remove(best)

        return pairs

    def reset(self):
        """
        Clears motion state so the predictor can be reused across videos.
        """

        self.previous_detections = []
        self.last_detections = []
        self.motion = None
        self.frames_since_detection = 0
