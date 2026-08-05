# Motion Predictor Benchmarks

Test video

- 1920x1080
- 60 FPS
- 3597 frames

---

## detect_every = 1

FPS: 31.8

Visual quality:
★★★★★

---

## detect_every = 5

FPS: 61.1

Visual quality:
★★★★★

Recommended value.

---

## detect_every = 10

FPS: 70.1

Visual quality:
★★★☆☆

Minor prediction errors.

---

## detect_every = 20

FPS: 75.8

Visual quality:
★☆☆☆☆

Prediction errors become unacceptable.

# Design Notes

During the development of the MotionPredictor, several interpolation strategies were evaluated:

- Corner interpolation
- Center interpolation
- Dynamic bounding box scaling
- Fixed bounding box size

All approaches produced similar behaviour when objects moved toward or away from the camera. The primary limitation was identified as perspective distortion rather than the interpolation method itself.

After benchmarking, the project adopted:

- Linear motion prediction
- Recommended `detect_every = 5`

This configuration provided the best balance between:

- processing speed
- GPU usage
- visual quality
- implementation simplicity

More complex tracking algorithms (Kalman Filter, optical flow, etc.) were intentionally postponed because they introduce significantly higher implementation complexity while providing limited benefit for the current goals of the project.