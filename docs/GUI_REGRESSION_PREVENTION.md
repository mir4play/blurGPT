# GUI Regression Prevention

## Why this exists

A previous GUI fix restored `gui/main_window.py` from an older/incomplete implementation. Although the targeted issue was fixed, the replacement unintentionally removed existing behavior: drag-and-drop, persistence of the Advanced-mode preference, and the processing-completion summary with folder shortcuts. These regressions were restored in commit `1f7c9774`.

## Mandatory rules for future changes

1. **Do not overwrite a working GUI module with an older version as a shortcut.** Compare the target-branch implementation with the proposed change before editing.
2. **Keep fixes scoped.** Preserve unrelated behavior and features unless their removal is explicitly intended, justified, and documented.
3. **Review the complete diff before merging.** Look for deleted methods, imports, signal connections, settings persistence, keyboard/mouse/drag interactions, and completion/error handling—not just the lines related to the issue.
4. **Protect existing GUI contracts.** At minimum, consider:
   - Dragging supported local video files into the main window.
   - Importing videos through the file picker, including origin-aware import behavior.
   - Queue removal that preserves the original file when required.
   - Saving and restoring the Clean/Advanced mode preference.
   - Showing the completion summary and shortcuts to output, error, and log folders.
   - Correct handling of processing errors and cancellation.
5. **Add regression tests where practical.** A test should fail if a focused fix silently removes an existing behavior.
6. **Do not claim GUI validation that has not been performed.** Run automated tests available in the environment and clearly identify any Windows-only behavior that still needs a Windows smoke test.

## GUI smoke-test checklist

Before merging changes affecting `gui/main_window.py`, video import, or queue management, verify:

- [ ] The GUI launches successfully.
- [ ] Drag-and-drop imports a supported video.
- [ ] File-picker import still works.
- [ ] Removing an imported working copy follows the origin-aware safety rules.
- [ ] Clean/Advanced selection persists after restarting the GUI.
- [ ] Completion summary appears and its folder shortcuts work.
- [ ] Processing error/cancellation behavior remains usable.
- [ ] Automated tests pass, and the full diff contains no unexplained deletions.

If a full-file restoration is genuinely necessary, manually reconcile it with the current implementation and check every removed method/feature before committing.
