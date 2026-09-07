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

Both should eventually share the same engine (`core/processor.py`). The GUI must never run YOLO or encoding on the Qt UI thread.

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
                    └── settings / benchmarks
```

**Rules:**

1. **Qt-free engine** — `core/processor.py` has no PySide imports.
2. **Worker thread** — long work only inside `ProcessingWorker` / `BatchProcessor`.
3. **Settings outside source** — runtime prefs in `config/settings.json` (gitignored); `config.py` holds defaults only.
4. **Cooperative cancel** — never kill the process mid-encode; use `request_cancel` and `JobManager.cancel`.
5. **Simple by default** — Clean mode first; Advanced metrics optional.

---

## User-facing behavior

| Action | Behavior |
|---|---|
| Add videos | Copy into `input/` (do not move the user's original) |
| Remove from queue | Remove BlurGPT's copy under `input/` only when safe; originals outside the project are untouched |
| Start | Process `processing/` first, then `input/`, one job at a time |
| Cancel | Stop after the current cooperative check; return the current file to a resumable state when possible |
| Fail | Move job to `input_error/`, log to `logs/errors.log`, continue batch |
| Success | Output in `output/`, original in `input_archive/` |

Settings changed in the dialog apply to the **next** processing run, not a job already in flight.

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

Suggested order of work (details in Issues):

1. Queue correctness (processing items, name collisions)
2. Pre-flight checks before Start
3. Clear finish / fail / cancel messaging and folder shortcuts
4. Small UX polish (drag-and-drop, persist Advanced, version in title)
5. CLI → `BatchProcessor` unification if still divergent

---

## Related docs

- [`architecture.md`](architecture.md) — core pipeline
- [`performance.md`](performance.md) — benchmarks and NVENC
- [`roadmap.md`](roadmap.md) — project-level priorities
