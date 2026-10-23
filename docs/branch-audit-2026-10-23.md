# Branch audit — 2026-10-23

Inventory of remaining branches in mir4play/blurGPT after packaging readiness work landed on `main`.

## Current branches

- `main` — default branch (HEAD `7eb4775`). Contains full PySide6 GUI (via #46), shared resolve_ffmpeg, origin-aware Remove, packaging notes (`docs/packaging.md`) and starter PyInstaller spec (`blurGPT.spec` via #49/#50). Do not delete.
- `feature/pyside6-gui` — historical development branch (HEAD `8e284de`). GUI work has been merged to `main` via #46. Can be kept for reference or deleted if no longer needed; it is behind `main`.
- `automation/issue-packaging-docs-2026-10-23` — temporary branch for packaging how-to (merged via #50). Safe to delete; no unique unmerged work.

## Status of prior automation branches

The long list of date-suffixed `automation/*` branches from the 2026-10-22 audit has been cleaned up. Only the packaging-docs branch above remains.

## Recommendation

- Delete `automation/issue-packaging-docs-2026-10-23` (merged).
- Optionally delete or archive `feature/pyside6-gui` once confirmed no longer needed for ongoing work.
- Future agent work should continue to use short-lived branches off `main` (or a fresh feature branch) and delete them after merge.
- Consider enabling GitHub's automatic head-branch deletion on PR merge.

This file supersedes `docs/branch-audit-2026-10-22.md` and can itself be removed after the remaining cleanup.

Related: #43, #23, #14. Packaging readiness notes and starter spec are on `main`; local Windows frozen build is now possible via `pyinstaller blurGPT.spec` (see `docs/packaging.md`).
