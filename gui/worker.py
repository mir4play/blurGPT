"""Qt worker for running the BlurGPT engine outside the GUI thread."""

from PySide6.QtCore import QObject, Signal, Slot

from core.jobmanager import JobManager
from core.processor import BatchProcessor


class ProcessingWorker(QObject):
    """Run BatchProcessor in a QThread and expose safe UI signals."""

    progress = Signal(int)
    status = Signal(str)
    finished = Signal(dict)
    failed = Signal(str)

    def __init__(self):
        super().__init__()
        self.processor = None
        self._cancel_requested = False

    @Slot()
    def run(self):
        try:
            manager = JobManager()
            self.processor = BatchProcessor(
                manager,
                progress_callback=self.progress.emit,
                status_callback=self.status.emit,
            )
            if self._cancel_requested:
                self.processor.request_cancel()
            result = self.processor.run()
            self.finished.emit(result)
        except Exception as error:
            self.failed.emit(f"{type(error).__name__}: {error}")

    @Slot()
    def cancel(self):
        # Keep the request even if the user clicks Cancel while the worker is
        # still initializing the model. It will be applied immediately after
        # BatchProcessor is created.
        self._cancel_requested = True
        if self.processor is not None:
            self.processor.request_cancel()
