# Portable Windows packaging readiness

Notes for a future packaged/portable Windows GUI build of BlurGPT (so end users do not need a full Python + CUDA environment to run the desktop app).

## Current support (already in tree)

`core/paths.py` already distinguishes development vs frozen execution:

- `application_root()` uses `Path(sys.executable).parent` when `sys.frozen` is true (PyInstaller-style).
- All runtime directories (`input/`, `output/`, `processing/`, `temp/`, `input_archive/`, `input_error/`, `input_removed/`, `logs/`, `config/`, `models/`, `ffmpeg/`) are resolved relative to that root.
- `resolve_ffmpeg()` prefers a bundled `ffmpeg/ffmpeg.exe` next to the executable, then falls back to PATH.

This keeps a portable layout predictable and avoids depending on the current working directory.

## How to produce a local frozen build

A starter PyInstaller spec is in the repository root: `blurGPT.spec` (added in #49).

On a Windows machine with the project dependencies installed (PySide6, torch+CUDA, ultralytics, opencv-python, etc.):

```bat
pyinstaller blurGPT.spec
```

This produces `dist/BlurGPT/` (onedir by default). Copy or place the following next to `BlurGPT.exe` before running:

- `models/blurGPT.pt` (required; not embedded by default because it is large)
- Optionally `ffmpeg/ffmpeg.exe` (preferred over PATH; CUDA/NVENC build recommended)

The app will create `config/`, `input/`, `output/`, etc. at runtime next to the executable. See the suggested layout below.

Switch the spec to onefile by adjusting the `EXE`/`COLLECT` sections if a single-file binary is preferred (startup may be slower).

## Suggested portable layout (for a future build)

```text
BlurGPT/
├── BlurGPT.exe          # frozen GUI entry (gui.py)
├── models/
│   └── blurGPT.pt
├── ffmpeg/
│   └── ffmpeg.exe       # optional; or rely on system PATH
├── config/              # created at runtime (settings.json)
├── input/
├── output/
├── processing/
├── temp/
├── input_archive/
├── input_error/
├── input_removed/
└── logs/
```

Place the YOLO model and (optionally) a CUDA-enabled FFmpeg with NVENC next to the exe. The app will create the other directories as needed.

## Checklist before a testable frozen build

- [x] Starter PyInstaller spec (`blurGPT.spec`) present.
- [ ] Confirm `sys.frozen` path resolution works under PyInstaller on Windows.
- [ ] Bundle or document the YOLO model (`models/blurGPT.pt`).
- [ ] Decide FFmpeg strategy: bundled `ffmpeg.exe` with `h264_nvenc`, or require it on PATH.
- [ ] Verify CUDA/PyTorch runtime dependencies are either bundled or clearly required (current app requires CUDA at startup).
- [ ] Smoke-test: start GUI, add external video, process short clip with NVENC, cancel mid-job, Remove (origin-aware), open result folders.
- [ ] Confirm settings persist in `config/settings.json` next to the exe.
- [ ] Document any antivirus/false-positive notes for the frozen binary.

## Status

**Ready for local Windows frozen-build smoke-test.**

The starter PyInstaller spec (`blurGPT.spec`) and these notes are on `main`. A user with the development environment can now run:

```bat
pyinstaller blurGPT.spec
```

then place `models/blurGPT.pt` (and optionally `ffmpeg/ffmpeg.exe`) next to `dist/BlurGPT/BlurGPT.exe` and launch the GUI.

No frozen binary is produced by CI yet. When a pre-built portable package is available it will be announced on #14 / #23. Do not bump version or tag until a real release milestone is validated on `main` (see #29).

Related: #14 (GUI backlog), #23 (handoff), #29 (release gates).
