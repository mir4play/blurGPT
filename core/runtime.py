"""Runtime filesystem initialization for the desktop application."""

from core.paths import MODEL_DIR


def ensure_runtime_directories() -> None:
    """Create runtime directories that should be visible in portable builds.

    The JobManager creates the processing directories when it starts. The model
    directory is initialized explicitly here so a fresh frozen build exposes
    ``models/`` immediately, even before the first processing job is queued.
    The model file itself is intentionally not bundled by this helper.
    """
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
