# Changelog

All notable changes to this project will be documented in this file.

---

## [Unreleased]

### Fixed

- MotionPredictor now applies `dw`/`dh` when interpolating bounding-box size between YOLO calls (previously only translation was applied).
- Motion matching is class-aware and uses a distance threshold based on the previous box diagonal, reducing face↔plate swaps and long-range false matches.
- Failed jobs are moved to `input_error/`, partial temp outputs are cleaned, and a line is appended to `logs/errors.log` instead of aborting the whole batch.
- Video I/O validates resolution and FPS before processing starts (NVENC path preserved).

### Changed

- `Detector` is instantiated once per batch and reused across videos via `reset()` (avoids reloading the YOLO weights for every file).
- `Detection` dataclass no longer declares duplicated `cx`/`cy`/`w`/`h` properties.

### Documentation

- Audited the README against the current runtime implementation.
- Corrected the model documentation: the current runtime uses one YOLO model for both face and license-plate classes.
- Documented the actual job-processing lifecycle and supported video extensions.
- Documented the current configuration defaults.
- Expanded the architecture documentation to describe module responsibilities and data flow.
- Clarified the scope and limitations of the performance benchmark.
- Updated the roadmap so completed work is no longer presented as future work.
- Added a note that no open-source license is currently declared in the repository.

> Built on top of `feature/performance-audit` (NVENC + benchmark logging). Application version is still **0.4.0** until a release is cut.

---

## [0.4.0] - 2026-08-05

### Added

- Motion prediction between YOLO detections.
- Internal motion vector calculation (`dx`, `dy`, `dw`, `dh`).
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

- Motion prediction depends on matching detections between consecutive YOLO inference frames.
- If detections change order, objects appear/disappear, or matching becomes ambiguous, temporary bounding-box jumps may occur.
- Future tracking improvements are planned to make temporal association more robust.

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
