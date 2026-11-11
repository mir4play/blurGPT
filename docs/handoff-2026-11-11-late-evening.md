# Development handoff — 2026-11-11 (late evening)

## Current state

- `main` HEAD: `258cb20be2c2fab0d236324014f6384f8d59bba4` (docs: evening handoff after closing superseded PRs #95/#96).
- **v0.6.0** is released (PySide6 GUI, packaging notes + `blurGPT.spec`, Windows frozen smoke-test passed 2026-11-05).
- Config hygiene complete (unused flags, Detection aliases, and CLASSES dict removed).
- **PRs #95 (tooltips) and #96 (CLASSES removal) closed** as fully superseded by commits already on main (`5420fcf` and `6df4d52`). No unique work remained.
- 0 open PRs.
- Top open priority: **#61 Hardware portability** (NVIDIA/CUDA+NVENC remains the reference; explicit CPU + OpenCV path has source-runtime CI smoke evidence from 2026-11-09; frozen-build, real-footage, and alternative GPU backends still outstanding). Tooltips correctly describe independent device/encoder choices.

## Roadmap priorities (see `docs/roadmap.md`)

1. Hardware/backend portability (#61)
2. Model development
3. Model packaging (~44 MB `.pt` still a normal git blob)

## Branch hygiene

Many leftover `automation/*`, `docs/*`, `test/*`, and `feat/*` branches exist (changelog-*, handoff-*, config-hygiene-*, etc.). They contain no unique unmerged work that is not already on `main`. Safe to delete after a quick confirmation.

## Next safe slices

- Further docs reconciliation or small non-GPU tests under #61 (e.g. capability probe edge cases, docs clarity).
- User-driven frozen-build / real-footage validation of the CPU path if desired.
- Optional model packaging (Git LFS or download-on-first-run).
- Branch cleanup of obsolete automation/* branches.

Do not redesign architecture, add full trackers, or parallel multi-GPU jobs.

Related: #23, #14, #29, #61.
