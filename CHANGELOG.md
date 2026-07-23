# Changelog

All notable changes to this project will be documented in this file.

---

## [0.4.0] - In Progress

### Added
- Motion prediction system between YOLO detections.
- Internal motion vector calculation (dx, dy, dw, dh).
- Detector architecture prepared for predictive tracking.
- Folders of the architeture that was missing at github

### Changed
- Detector refactored to support motion estimation.
- Detection pipeline prepared for future tracking improvements.


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