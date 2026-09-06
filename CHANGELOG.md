# Changelog

All notable changes to this project will be documented in this file.

---

## [Unreleased]

### Documentation

- (none yet)

---

## [0.5.0] - 2026-09-06

### Added

- NVIDIA `h264_nvenc` hardware encoding path via FFmpeg (default when available).
- OpenCV `mp4v` kept as explicit fallback through `VIDEO_ENCODER = "opencv"`.
- NVENC quality (`VIDEO_NVENC_CQ`) and preset (`VIDEO_NVENC_PRESET`) in `config.py`.
- Structured per-job benchmark records in `logs/benchmarks.jsonl`.
- `JobManager.fail()`: failed jobs move to `input_error/`, partial temp outputs are removed, and a line is appended to `logs/errors.log`.
- Batch continues after a failed job instead of aborting.
- `Detector.reset()` so the YOLO model is loaded once per batch and reused across videos.

### Fixed

- MotionPredictor now applies `dw`/`dh` when interpolating bounding-box size between YOLO calls (previously only translation was applied).
- Motion matching is class-aware (same class only) and uses a distance threshold based on the previous box diagonal.
- Video I/O validates resolution and FPS before processing; writer/open failures raise clear errors.
- `Detection` dataclass no longer declares duplicated `cx`/`cy`/`w`/`h` properties.

### Changed

- Processing statistics use `time.perf_counter()` and report the active encoder.
- Failed-job handling and detector reuse harden daily batch processing (~hours of Full HD video).

### Performance

- Encoding is the main remaining end-to-end cost after `DETECT_EVERY = 5`; NVENC targets that path.
- Benchmarks should be read with context (OBS/live sharing the same GPU lowers throughput).

### Documentation

- README, architecture, performance and roadmap updated for NVENC, resilience and motion matching.
- Audit backlog issues #5–#8 addressed in this release branch.

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
