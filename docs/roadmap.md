# BlurGPT Roadmap

This roadmap describes the next technical priorities for BlurGPT. It is intentionally kept separate from the changelog: the roadmap describes future work, while the changelog records work that has already been released.

Actionable GUI tasks live in **GitHub Issues**. Orientation for the desktop app is in [`docs/gui.md`](gui.md).

## Current priorities

### 1. Desktop GUI (active)

The PySide6 GUI is now integrated on `main`: queue, worker thread, settings profiles, live metrics, finish/cancel messaging, and folder shortcuts.

Principles and run instructions: [`docs/gui.md`](gui.md).
Trackable items: parent issue **GUI development backlog** (and linked child issues).

Focus remains simple and functional — queue correctness, clear errors, shared processing engine — not feature sprawl.

### 2. Hardware/backend portability

Expand runtime compatibility beyond the current NVIDIA/CUDA-first path without destabilizing the working Windows executable. Track this work in **#61 — Hardware portability: CUDA, other GPU backends, and CPU fallback**.

The compatibility strategy is deliberately incremental:

- preserve the current NVIDIA/CUDA + NVENC path as the performance reference implementation
- document the existing explicit CPU device route accurately; do not describe it as an automatic fallback or validated support until its runtime behavior is independently checked
- keep CPU inference and video encoding separate; CPU-only attempts need an available software encoder such as the existing OpenCV `mp4v` path
- evaluate AMD GPU acceleration (initially ROCm on supported platforms) in an isolated environment
- evaluate Intel GPU acceleration (the appropriate PyTorch XPU/oneAPI path) separately
- verify newer NVIDIA platforms, including NVIDIA DGX Spark, through the supported PyTorch/CUDA stack rather than adding a separate special case
- keep backend-specific dependencies isolated so the existing Windows build does not inherit unnecessary packages
- use separate build/package targets when a single universal executable would introduce unsafe or excessive dependencies
- use the structured volunteer report form and short benchmark guidance in [`docs/compatibility.md`](compatibility.md), without adding telemetry or requiring the maintainer to test every alternative configuration

A non-mutating capability probe now distinguishes CPU availability, NVIDIA CUDA, ROCm/HIP, and Intel XPU when exposed by the installed PyTorch build. It reports availability only: the current CUDA device-index selector, encoder selection, and NVIDIA defaults remain unchanged. XPU is not selectable yet, and no alternative backend is runtime-certified.

The current source-level device/encoder inventory and validation status are in [`docs/hardware-backends.md`](hardware-backends.md). No claim of universal GPU support should be made without backend-specific runtime validation and documented benchmark conditions.

### 3. Model development

Continue improving training data and model versions for combined face and license-plate detection. Keep training experiments separate from the runtime so the README always describes the model shipped with the application.

### 4. Configuration hygiene

Optional cleanup after 0.5.0:

- remove or wire the legacy `SHOW_VIDEO`, `SAVE_VIDEO`, and `SHOW_REPORT` flags
- remove `CLASSES` if class filtering is not intended to be configurable

These are maintenance items, not blockers for the current runtime.

### 5. Model packaging

The runtime weight is still a normal git blob (~44 MB). Consider Git LFS or a release asset + download-on-first-run if the model is iterated often or cloned on multiple machines.

## Under evaluation

- Additional anonymization methods
- Further motion quality work only if measured leaks remain after the 0.5.0 matching/size fixes (full ByteTrack/BoT-SORT still out of scope unless quality or FPS gains are demonstrated)
- Packaged Windows distribution / first-run diagnostics
- Hardware-specific packaging/build targets for CUDA, CPU, AMD and Intel backends as compatibility work matures

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
