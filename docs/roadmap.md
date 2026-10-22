# BlurGPT Roadmap

This roadmap describes the next technical priorities for BlurGPT. It is intentionally kept separate from the changelog: the roadmap describes future work, while the changelog records work that has already been released.

Actionable GUI tasks live in **GitHub Issues**. Orientation for the desktop app is in [`docs/gui.md`](gui.md).

## Current priorities

### 1. Desktop GUI (active)

PySide6 GUI on `feature/pyside6-gui`: queue, worker thread, settings profiles, live metrics.

Principles and run instructions: [`docs/gui.md`](gui.md).
Trackable items: parent issue **GUI development backlog** (and linked child issues).

Focus remains simple and functional — queue correctness, clear errors, shared processing engine — not feature sprawl.

### 2. Model development

Continue improving training data and model versions for combined face and license-plate detection. Keep training experiments separate from the runtime so the README always describes the model shipped with the application.

### 3. Configuration hygiene

Optional cleanup after 0.5.0:

- remove or wire the legacy `SHOW_VIDEO`, `SAVE_VIDEO`, and `SHOW_REPORT` flags
- remove `CLASSES` if class filtering is not intended to be configurable

These are maintenance items, not blockers for the current runtime.

### 4. Model packaging

The runtime weight is still a normal git blob (~44 MB). Consider Git LFS or a release asset + download-on-first-run if the model is iterated often or cloned on multiple machines.

## Under evaluation

- Additional anonymization methods
- Further motion quality work only if measured leaks remain after the 0.5.0 matching/size fixes (full ByteTrack/BoT-SORT still out of scope unless quality or FPS gains are demonstrated)
- Packaged Windows distribution / first-run diagnostics

## Completed in 0.5.0

- Combined face and license-plate detection through a single runtime model
- Motion prediction between YOLO detections (including size `dw`/`dh`)
- Lightweight class-aware matching with distance threshold
- Modular detector/detection architecture
- Batch job workflow with `input_archive/` and `input_error/`
- Per-job exception handling so one bad file does not stop the batch
- Detector loaded once and reused across the batch
- NVIDIA NVENC encoding path with OpenCV fallback
- Structured benchmark logging (`logs/benchmarks.jsonl`)
- Early validation that the configured YOLO model file exists before detector initialization

These should not be re-added to the planned-work list unless a new implementation is being proposed.
