# BlurGPT Development Roadmap

> Working handoff document for continuing development on `feature/pyside6-gui`.
>
> Updated: 2026-09-07

## Current state

The PySide6 GUI and processing architecture have been substantially refactored. The GUI uses a worker thread for processing, while the reusable `BatchProcessor` is shared by GUI and CLI. Persistent processing settings, live metrics, Clean/Advanced modes, application-root paths, bundled FFmpeg support, environment preflight, collision-safe queue imports, cancellation handling, benchmark metadata, and unified English processing messages are now in place.

The latest known performance reference is approximately **76.9 processing FPS on 1920x1080/59.94 video**, with NVENC enabled. In that run, YOLO inference was the dominant cost; pixelation was negligible.

## Completed recently

- Persistent GUI processing settings in `config/settings.json`.
- Recommended / Performance / Quality / Custom processing profiles.
- Settings validation before processing.
- Active processing profile recorded in benchmark logs.
- Application-root path abstraction for portable deployments.
- Bundled FFmpeg path support (`ffmpeg/ffmpeg.exe`) with PATH fallback.
- Safe/idempotent video release and FFmpeg error reporting.
- GUI Clean / Advanced modes and live processing metrics.
- Queue collision handling: duplicate basenames are renamed safely instead of silently skipped or overwritten.
- Queue removal now refuses to unlink a job that is currently in `processing/`.
- Environment preflight before model initialization.
- Independent validation of inference CUDA device and NVENC availability.
- CLI converted to a thin `BatchProcessor` entry point.
- CLI Ctrl+C cancellation returns the current processing job to `input/` when cleanup succeeds.
- Benchmark logging aligned with effective settings/device and bundled FFmpeg.
- Processing reports and video errors standardized to English.
- MIT license and attribution documentation added.

## Next work — recommended order

### 1. GUI completion / UX (#17)

Improve completion, failure, and cancellation feedback and add convenient folder shortcuts.

Planned:

- Make the completion dialog summarize succeeded / failed / cancelled jobs clearly.
- Make cancellation explicitly state that the current job was returned to `input/` when applicable.
- Make failures point to `input_error/` and the benchmark/log location.
- Add buttons/shortcuts to open `output/`, `input/`, `input_error/`, and `logs/` in the system file manager.

### 2. GUI polish (#18)

Planned:

- Drag-and-drop video files into the queue.
- Persist the Clean/Advanced UI preference separately from processing settings.
- Add a centralized application version and expose it in the window title/about information.

The UI preference should preferably live in a GUI-specific preferences file rather than being mixed into processing profiles.

### 3. Robustness audit

These are not necessarily user-visible features, but should be addressed before calling the architecture stable:

- Snapshot video metadata (resolution/FPS/backend) before releasing `VideoProcessor`, then use the snapshot for reports and benchmark records instead of relying on post-release object state.
- Review `JobManager` move operations as transactions. In particular, examine failure recovery when output finalization succeeds but archiving the source fails.
- Make cancellation cleanup robust against Windows file-lock timing.
- Consider whether `BatchProcessor` should receive/reuse the GUI's `JobManager` instance instead of constructing another stateless manager in the worker.
- Consider making the processor's initial environment snapshot use the effective configured inference device, not the default device 0.
- Expand preflight to check writable directories and other deployment-level prerequisites where useful.
- Keep NVENC preflight layered: FFmpeg encoder availability is checked now; an actual encoder initialization smoke test can be considered later if real-world failures justify it.

## Testing / quality work

Once the feature is stable enough, add automated tests for the parts that can be tested without a GPU/video workload:

- settings load/save/reset and profile detection
- settings validation and normalization
- application-root/path resolution
- JobManager name collisions
- start / finish / cancel / fail state transitions
- benchmark serialization and legacy settings compatibility
- preflight validation with mocked environments

A real GPU/FFmpeg processing test should remain a separate integration/manual test because it depends on the local NVIDIA driver, CUDA/PyTorch installation, FFmpeg build, model weights, and sample videos.

## Documentation / release work

Before a public release:

- Review `README.md` and GUI/architecture documentation against the current code.
- Document the portable folder layout, bundled FFmpeg expectations, persistent settings, and processing profiles.
- Document installation/runtime requirements (Python, PyTorch/CUDA, NVIDIA driver, model weights, FFmpeg when not bundled).
- Decide on packaging strategy, likely PyInstaller for the first Windows distribution.
- Test the frozen application from a clean machine/folder, including first-run behavior and writable directories.
- Audit the licenses of the YOLO model weights, training datasets, bundled FFmpeg build, and other third-party components separately from BlurGPT's MIT license. BlurGPT's MIT license does not automatically relicense third-party assets.

## Scope boundaries

Avoid premature complexity unless measurements demonstrate a need:

- No parallel GPU processing of multiple videos yet.
- No full multi-object tracker yet.
- No plugin system yet.
- No major visual redesign/theme framework yet.

The priority is a reliable single-GPU batch pipeline with a clean GUI, predictable file lifecycle, reproducible settings, useful benchmarks, and safe cancellation.

## Development principle for the next session

Continue from the branch tip rather than restarting the architecture. Prefer small, independently reviewable commits. The user will perform local runtime testing and report results; development can continue proactively between tests when changes can be reasoned about safely from the codebase.
