# BlurGPT Desktop GUI

This document describes the PySide6 GUI: how to run it, how it relates to the processing engine, and the development principles that keep it simple.

Trackable work lives in GitHub Issues (see the parent issue **GUI development backlog**). This file is orientation, not a second backlog.

---

## Run

```bash
python gui.py
```

CLI remains available:

```bash
python blurGPT.py
```

Both share the same Qt-free engine (`core/processor.py` / `BatchProcessor`). The GUI never runs YOLO or encoding on the Qt UI thread.

Portable / frozen Windows builds use `core/paths.py` (`application_root()` detects `sys.frozen` and places data next to the executable).

---

## Architecture (short)

```text
gui.py
  └── gui/main_window.py     # window, queue, status, signals
        ├── gui/settings_dialog.py
        └── gui/worker.py    # QObject in QThread
              └── core/processor.py   # Qt-free batch engine
                    ├── JobManager
                    ├── Detector / MotionPredictor
                    ├── VideoProcessor
                    └── settings / benchmarks / preflight
```

**Rules:**

1. **Qt-free engine** — `core/processor.py` has no PySide imports.
2. **Worker thread** — long work only inside `ProcessingWorker` / `BatchProcessor`.
3. **Settings outside source** — runtime prefs in `config/settings.json` (gitignored); `config.py` holds defaults only.
4. **Cooperative cancel** — never kill the process mid-encode; use `request_cancel` and `JobManager.cancel`. NVENC/FFmpeg shutdown is hardened so cancellation is not turned into a failure.
5. **Simple by default** — Clean mode first; Advanced metrics optional (preference can be persisted).

---

## User-facing behavior

| Action | Behavior |
|---|---|
| Add videos | Copy into `input/` (skip if already under `input/`; do not move the user's original) |
| Remove from queue | Move BlurGPT's copy from `input/` to `input_removed/` (non-destructive). Originals outside the project are untouched. |
| Start | Preflight (model, CUDA/NVENC, settings) then process `processing/` first, then `input/`, one job at a time |
| Cancel | Stop after the current cooperative check; return the current file to a resumable state when possible. NVENC pipe errors do not mask cancellation. |
| Fail | Move job to `input_error/`, log to `logs/errors.log`, continue batch |
| Success | Output in `output/`, original in `input_archive/` |
| Finish / Cancel summary | (pending polish) dialog with counts + shortcuts to `output/`, `input_error/` (if failures), `logs/` |

Settings changed in the dialog apply to the **next** processing run, not a job already in flight.

Drag-and-drop import, version in window title, and persist Clean/Advanced are implemented on open PRs and awaiting merge after local smoke-test.

---

## Profiles

| Profile | Detection | Inference | NVENC |
|---|---:|---:|---|
| Recommended | every 5 | 640 | CQ 23 / P4 |
| Performance | every 8 | 640 | CQ 25 / P3 |
| Quality | every 2 | 1280 | CQ 20 / P5 |
| Custom | user-defined | user-defined | user-defined |

---

## Development principles

Keep the GUI **simple and functional**:

- Prefer fixing queue/error clarity over new panels.
- Prefer one shared `BatchProcessor` over duplicating CLI logic.
- Prefer clear dialogs (missing model, missing FFmpeg, invalid settings) over silent fallback.
- Avoid full trackers, parallel GPU jobs, and heavy UI frameworks unless measured need appears.

Current polish status (see open PRs against `feature/pyside6-gui`):

- #34 — finish/cancel summary + folder shortcuts (#17)
- #33 — drag-and-drop import (#18)
- #28 — version in window title (#18)
- #36 — persist Clean/Advanced mode (#18)

All are mergeable; local Windows GUI smoke-test recommended before merging.

---

## Related docs

- [`architecture.md`](architecture.md) — core pipeline
- [`performance.md`](performance.md) — benchmarks and NVENC
- [`roadmap.md`](roadmap.md) — project-level priorities
