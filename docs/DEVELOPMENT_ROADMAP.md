# BlurGPT Development Roadmap

> **Archived / historical handoff** (updated 2026-11-06).
>
> The PySide6 GUI milestone described below shipped in **0.6.0** and is now on `main` (Windows frozen smoke test passed 2026-11-05).
>
> **Current priorities** live in [`docs/roadmap.md`](roadmap.md). Hardware/backend portability is tracked in issue **#61**.

---

## Historical context (pre-0.6.0)

The PySide6 GUI and processing architecture were substantially refactored on `feature/pyside6-gui`. The GUI uses a worker thread for processing, while the reusable `BatchProcessor` is shared by GUI and CLI. Persistent processing settings, live metrics, Clean/Advanced modes, application-root paths, bundled FFmpeg support, environment preflight, collision-safe queue imports, cancellation handling, benchmark metadata, and unified English processing messages are in place.

The latest known performance reference around that time was approximately **76.9 processing FPS on 1920x1080/59.94 video**, with NVENC enabled. In that run, YOLO inference was the dominant cost; pixelation was negligible.

## Completed in the 0.6.0 milestone

- Persistent GUI processing settings in `config/settings.json`.
- Recommended / Performance / Quality / Custom processing profiles.
- Settings validation before processing.
- Active processing profile recorded in benchmark logs.
- Application-root path abstraction for portable deployments.
- Bundled FFmpeg path support (`ffmpeg/ffmpeg.exe`) with PATH fallback.
- Safe/idempotent video release and FFmpeg error reporting.
- GUI Clean / Advanced modes and live processing metrics.
- Queue collision handling: duplicate basenames are renamed safely instead of silently skipped or overwritten.
- Queue removal is origin-aware (does not leave a full-size duplicate when an external origin exists).
- Environment preflight before model initialization.
- Independent validation of inference CUDA device and NVENC availability.
- CLI converted to a thin `BatchProcessor` entry point.
- CLI Ctrl+C cancellation returns the current processing job to `input/` when cleanup succeeds.
- Benchmark logging aligned with effective settings/device and bundled FFmpeg.
- Processing reports and video errors standardized to English.
- MIT license and attribution documentation added.
- Finish/cancel summary dialog and folder shortcuts.
- Version in window title.
- Frozen console suppression (`CREATE_NO_WINDOW`).
- Models directory initialization.
- Successful Windows frozen-build smoke test.

## Scope boundaries (still apply)

Avoid premature complexity unless measurements demonstrate a need:

- No parallel GPU processing of multiple videos yet.
- No full multi-object tracker yet.
- No plugin system yet.
- No major visual redesign/theme framework yet.

The priority remains a reliable single-GPU batch pipeline with a clean GUI, predictable file lifecycle, reproducible settings, useful benchmarks, and safe cancellation.

## Development principle

Prefer small, independently reviewable commits. The user performs local runtime testing and reports results; development can continue proactively between tests when changes can be reasoned about safely from the codebase.

For the latest priorities after 0.6.0, see [`docs/roadmap.md`](roadmap.md) and issues #61 / #23 / #14.
