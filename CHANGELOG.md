# Changelog

All notable changes to this project will be documented in this file.

---

## [0.4.0] - 2026-08-05

### Added
- Motion prediction between YOLO detections.
- Internal motion vector calculation (dx, dy, dw, dh).
- Internal `Detection` class to decouple BlurGPT from Ultralytics.
- `MotionPredictor` module for linear interpolation between detections.
- Configurable `detect_every` option to reduce inference frequency.
- Project architecture documentation.
- Performance documentation.
- Development roadmap.

### Changed
- Detection pipeline refactored to use internal `Detection` objects.
- Pixelation pipeline updated to use the new detection abstraction.
- Motion prediction extracted into its own module.
- Default detection model updated to the new BlurGPT model.
- Detection pipeline optimized for reduced inference frequency.

### Performance
- Recommended configuration:
  - `detect_every = 5`
  - `imgsz = 640`
- Significantly reduced YOLO inference time.
- Improved overall processing speed while maintaining acceptable visual quality.

### Known Limitations
- Motion prediction assumes that object detections preserve their order between consecutive YOLO inference frames.
- If detections change order, or objects appear/disappear between inference frames, temporary bounding-box jumps may occur.
- This limitation is planned to be solved in a future release using object tracking (IoU matching or a tracker such as ByteTrack or BoT-SORT).

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