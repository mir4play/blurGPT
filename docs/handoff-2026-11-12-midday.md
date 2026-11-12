# Development handoff — 2026-11-12 (midday)

## Current state

- `main` HEAD: `60b7097` (morning handoff #102 that recorded prior HEAD 258cb20).
- **v0.6.0** is released (PySide6 GUI, packaging notes + `blurGPT.spec`, Windows frozen smoke-test passed 2026-11-05).
- Config hygiene complete (unused flags, Detection aliases, and CLASSES dict removed).
- **PRs #95 and #96 closed** as fully superseded; no unique work remained.
- 0 open PRs.
- Top open priority: **#61 Hardware portability** (NVIDIA/CUDA+NVENC remains the reference; explicit CPU + OpenCV path has source-runtime CI smoke evidence from 2026-11-09; frozen-build, real-footage, and alternative GPU backends still outstanding). Tooltips correctly describe independent device/encoder choices.

## Roadmap priorities (see `docs/roadmap.md`)

1. Hardware/backend portability (#61)
2. Model development
3. Model packaging (~44 MB `.pt` still a normal git blob)

## Branch hygiene

Many leftover `automation/*`, `docs/*`, `test/*`, `feat/*`, and `fix/*` branches exist (changelog-*, handoff-*, config-hygiene-*, etc.). They contain no unique unmerged work that is not already on `main`. Safe to delete after a quick confirmation.

## Next safe slices

- Further docs reconciliation or small non-GPU tests under #61 (e.g. capability probe edge cases, docs clarity).
- User-driven frozen-build / real-footage validation of the CPU path if desired.
- Optional model packaging (Git LFS or download-on-first-run).
- Branch cleanup of obsolete automation/* branches.

Do not redesign architecture, add full trackers, or parallel multi-GPU jobs.

Related: #23, #14, #29, #61.
