# Branch audit — 2026-10-22

Inventory of all branches in mir4play/blurGPT at the time of this audit. All work from the listed automation branches has been merged into `feature/pyside6-gui` (HEAD `8de8cd3c`). No open PRs exist.

## Keep

- `main` — default branch, v0.5.0 release. Do not delete.
- `feature/pyside6-gui` — primary active development branch. Do not delete.

## Delete (obsolete, work merged)

All `automation/*` branches below are date-suffixed temporary agent branches whose commits were merged via closed PRs. No unique unmerged work remains.

| Branch | Associated issue / PR | Status |
|---|---|---|
| automation/ci-unit-tests-2026-10-17 | CI baseline | merged |
| automation/issue-17-gui-result-actions-2026-10-15 | #17 | superseded |
| automation/issue-17-messaging-clean-2026-10-18 | #17 / #34 | superseded |
| automation/issue-17-messaging-current-2026-10-20 | #17 / #40 | merged |
| automation/issue-17-messaging-resolved-2026-10-19 | #17 / #38 | superseded |
| automation/issue-18-drag-drop-2026-10-16 | #18 | superseded |
| automation/issue-18-drag-drop-rebased-2026-10-17 | #18 / #33 | merged |
| automation/issue-18-persist-advanced-2026-10-18 | #18 / #36 | merged |
| automation/issue-18-version-title-2026-10-17 | #18 / #28 | merged |
| automation/issue-20-nvenc-cancel-2026-10-14 | #20 | merged |
| automation/issue-22-docs-catchup-2026-10-20 | #22 | superseded |
| automation/issue-22-docs-current-2026-10-21 | #22 / #45 | merged |
| automation/issue-22-docs-refresh-2026-10-19 | #22 / #37 | merged |
| automation/issue-22-resolve-ffmpeg-2026-10-19 | #22 | superseded |
| automation/issue-22-resolve-ffmpeg-2026-10-21 | #22 | superseded |
| automation/issue-22-resolve-ffmpeg-current-2026-10-21 | #22 / #44 | merged |
| automation/issue-39-no-duplicate-remove-2026-10-20 | #39 | superseded |
| automation/issue-39-origin-remove-2026-10-21 | #39 / #41 | merged |
| automation/issue-39-origin-remove-current-2026-10-20 | #39 | superseded |
| automation/queue-safety-2026-10-14 | queue safety | merged |

## Recommendation

Delete all listed `automation/*` branches after this documentation is merged. Future agent work should prefer short-lived branches and delete or close them promptly after merge. Consider enabling GitHub's automatic head-branch deletion on PR merge.

This file can be removed after cleanup is complete.
