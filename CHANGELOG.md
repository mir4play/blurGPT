# Changelog

All notable changes to this project will be documented in this file.

---

## [0.4.0] - In Progress

### Added
- Motion prediction system between YOLO detections.
- Internal motion vector calculation (dx, dy, dw, dh).
- Detector architecture prepared for predictive tracking.
- Internal `Detection` class to decouple BlurGPT from Ultralytics.
- MotionPredictor module for linear interpolation between YOLO detections.
- Configurable `detect_every` option to reduce inference frequency.
- Folders of the architeture that was missing at github

### Changed
- Detector refactored to support motion estimation.
- Detection pipeline prepared for future tracking improvements.
- Detector now returns internal Detection objects.
- Pixelation pipeline updated to use Detection objects.
- Motion prediction extracted into its own class.

### Performance
- Recommended detect_every value: 5.
- Approximately 2× processing speed compared to detect_every=1 while maintaining acceptable visual quality.

### Known Limitation

The current motion prediction assumes that object detections keep the same order between consecutive YOLO inference frames.

If the detector changes the order of detections, or if objects appear/disappear between inference frames, the predicted motion may be assigned to the wrong object, causing temporary bounding box jumps.

This limitation will be addressed in a future version by introducing object tracking (IoU matching or a dedicated tracker such as ByteTrack/BoT-SORT).


---

## [0.3.1] - 2026-07-22

### Added
- Batch processing.
- Automatic input folder scanning.
- JobManager module.
- Automatic input archive.
- Automatic failed input handling.
- Temporary output workflow.

### Changed
- Video processing now uses a job-based workflow.

---

## [0.3.0] - 2026-07-21

### Added
- Automated processing workflow.
- Project modularization.

---

## [0.2.0]

### Added
- Face detection.
- License plate detection.
- Pixelation.
- CUDA support.
- Statistics report.
- Progress bar.