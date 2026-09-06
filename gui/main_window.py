"""Main BlurGPT application window.

The window never runs video processing in the Qt event-loop thread. Heavy work
is delegated to ProcessingWorker/QThread so the interface remains responsive.
"""

import shutil
from pathlib import Path

from PySide6.QtCore import QTimer, QThread
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QProgressBar,
    QVBoxLayout,
    QWidget,
)

from core.jobmanager import JobManager
from gui.worker import ProcessingWorker


class MainWindow(QMainWindow):
    """Primary BlurGPT window."""

    def __init__(self):
        super().__init__()

        self.manager = JobManager()
        self.thread = None
        self.worker = None
        self._closing_after_processing = False
        self._processing_started_at = None
        self._last_progress = 0

        self.setWindowTitle("BlurGPT")
        self.setMinimumSize(900, 620)
        self._build_ui()

        # A lightweight heartbeat is deliberately independent of worker
        # progress. This lets the UI show elapsed time even while one expensive
        # YOLO/FFmpeg operation is in progress and no frame callback arrives.
        self._heartbeat = QTimer(self)
        self._heartbeat.setInterval(1000)
        self._heartbeat.timeout.connect(self._update_heartbeat)

        self.refresh_jobs()

    def _build_ui(self):
        central = QWidget()
        root = QVBoxLayout(central)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(16)

        title = QLabel("BlurGPT")
        title.setObjectName("title")
        subtitle = QLabel("Video anonymization — faces and license plates")
        subtitle.setObjectName("subtitle")
        root.addWidget(title)
        root.addWidget(subtitle)

        content = QGridLayout()
        content.setHorizontalSpacing(16)
        content.setVerticalSpacing(12)

        input_card = self._card("Input queue")
        input_layout = input_card.layout()
        self.queue_list = QListWidget()
        self.queue_list.setMinimumHeight(260)
        input_layout.addWidget(self.queue_list)

        buttons = QHBoxLayout()
        self.add_button = QPushButton("Add videos…")
        self.add_button.clicked.connect(self.add_videos)
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.refresh_jobs)
        buttons.addWidget(self.add_button)
        buttons.addWidget(self.refresh_button)
        input_layout.addLayout(buttons)

        status_card = self._card("Processing status")
        status_layout = status_card.layout()
        self.status_label = QLabel("Ready")
        self.current_label = QLabel("No job running")
        self.current_label.setObjectName("secondary")
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(True)
        status_layout.addWidget(self.status_label)
        status_layout.addWidget(self.current_label)
        status_layout.addWidget(self.progress)

        self.heartbeat_label = QLabel("Idle")
        self.heartbeat_label.setObjectName("secondary")
        status_layout.addWidget(self.heartbeat_label)

        action_buttons = QHBoxLayout()
        self.start_button = QPushButton("Start processing")
        self.start_button.setObjectName("primaryButton")
        self.start_button.clicked.connect(self.start_processing)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setEnabled(False)
        self.cancel_button.clicked.connect(self.cancel_processing)
        action_buttons.addWidget(self.start_button)
        action_buttons.addWidget(self.cancel_button)
        status_layout.addLayout(action_buttons)

        content.addWidget(input_card, 0, 0)
        content.addWidget(status_card, 0, 1)
        content.setColumnStretch(0, 3)
        content.setColumnStretch(1, 2)
        root.addLayout(content)

        info = QLabel(
            "Processing runs in a background worker. The window stays responsive "
            "while YOLO and NVENC are working, and Cancel stops safely at the "
            "next processing point without treating the video as a failed job."
        )
        info.setWordWrap(True)
        info.setObjectName("info")
        root.addWidget(info)

        self.setCentralWidget(central)
        self.setStyleSheet(
            """
            QMainWindow { background: #202124; }
            QWidget { color: #e8eaed; font-size: 14px; }
            QLabel#title { font-size: 30px; font-weight: 700; }
            QLabel#subtitle { color: #9aa0a6; margin-bottom: 8px; }
            QLabel#secondary, QLabel#info { color: #9aa0a6; }
            QLabel#info { padding: 8px; }
            QFrame#card { background: #292a2d; border: 1px solid #3c4043; border-radius: 10px; }
            QListWidget { background: #202124; border: 1px solid #3c4043; border-radius: 6px; padding: 6px; }
            QPushButton { background: #3c4043; border: 1px solid #5f6368; border-radius: 6px; padding: 9px 14px; }
            QPushButton:hover { background: #4a4d51; }
            QPushButton:disabled { color: #777; }
            QPushButton#primaryButton { background: #8ab4f8; color: #202124; font-weight: 700; padding: 11px; }
            QProgressBar { background: #202124; border: 1px solid #3c4043; border-radius: 5px; text-align: center; min-height: 18px; }
            """
        )

    @staticmethod
    def _card(title: str) -> QFrame:
        card = QFrame()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        heading = QLabel(title)
        heading.setStyleSheet("font-size: 18px; font-weight: 600;")
        layout.addWidget(heading)
        return card

    def refresh_jobs(self):
        if self.thread is not None and self.thread.isRunning():
            return

        self.queue_list.clear()
        jobs = self.manager.find_jobs()
        for job in jobs:
            self.queue_list.addItem(f"[{job.source}]  {job.filename}")

        count = len(jobs)
        self.status_label.setText(
            f"{count} video{'s' if count != 1 else ''} waiting"
        )
        self.start_button.setEnabled(count > 0)

    def add_videos(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select videos",
            str(Path.cwd()),
            "Videos (*.mp4 *.mov *.avi *.mkv *.m4v *.wmv)",
        )
        if not files:
            return

        copied = 0
        for filename in files:
            source = Path(filename)
            destination = self.manager.input_dir / source.name
            if destination.exists():
                continue
            try:
                # Never read an entire video into RAM. TV/video files can be
                # tens of gigabytes, so copy2 streams through the filesystem.
                shutil.copy2(source, destination)
                copied += 1
            except OSError as error:
                QMessageBox.warning(
                    self, "Could not add video", f"{source.name}\n\n{error}"
                )

        self.refresh_jobs()
        if copied:
            self.status_label.setText(
                f"Added {copied} video{'s' if copied != 1 else ''}"
            )

    def start_processing(self):
        if self.thread is not None and self.thread.isRunning():
            return

        self.thread = QThread(self)
        self.worker = ProcessingWorker()
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.progress.connect(self._on_progress)
        self.worker.status.connect(self._on_status)
        self.worker.finished.connect(self._on_finished)
        self.worker.failed.connect(self._on_failed)
        self.worker.finished.connect(self.thread.quit)
        self.worker.failed.connect(self.thread.quit)
        self.thread.finished.connect(self._cleanup_worker)

        self._set_processing_state(True)
        self.progress.setValue(0)
        self._last_progress = 0
        self._processing_started_at = __import__("time").monotonic()
        self.heartbeat_label.setText("Worker starting…")
        self.status_label.setText("Starting…")
        self._heartbeat.start()
        self.thread.start()

    def cancel_processing(self):
        if self.worker is None:
            return
        self.cancel_button.setEnabled(False)
        self.status_label.setText("Cancellation requested…")
        self.worker.cancel()

    def _on_progress(self, value):
        self._last_progress = value
        self.progress.setValue(value)

    def _on_status(self, message):
        self.status_label.setText(message)
        if ": " in message:
            self.current_label.setText(message.split(": ", 1)[1])

    def _update_heartbeat(self):
        if self._processing_started_at is None:
            return
        import time

        elapsed = int(time.monotonic() - self._processing_started_at)
        minutes, seconds = divmod(elapsed, 60)
        self.heartbeat_label.setText(
            f"Worker active • elapsed {minutes:02d}:{seconds:02d} • "
            f"last frame progress {self._last_progress}%"
        )

    def _on_finished(self, result):
        self._heartbeat.stop()
        self._processing_started_at = None
        if result.get("cancelled"):
            self.status_label.setText("Cancelled safely")
        else:
            self.status_label.setText(
                f"Finished — {result['succeeded']} succeeded, "
                f"{result['failed']} failed"
            )
        self.heartbeat_label.setText("Idle")
        self._set_processing_state(False)
        self.refresh_jobs()
        if self._closing_after_processing:
            self.close()

    def _on_failed(self, message):
        self._heartbeat.stop()
        self._processing_started_at = None
        self.heartbeat_label.setText("Worker stopped")
        self._set_processing_state(False)
        QMessageBox.critical(self, "BlurGPT processing error", message)

    def _cleanup_worker(self):
        if self.worker is not None:
            self.worker.deleteLater()
        self.worker = None
        if self.thread is not None:
            self.thread.deleteLater()
        self.thread = None
        self.refresh_jobs()

    def _set_processing_state(self, running):
        self.add_button.setEnabled(not running)
        self.refresh_button.setEnabled(not running)
        self.start_button.setEnabled(not running and bool(self.manager.find_jobs()))
        self.cancel_button.setEnabled(running)

    def closeEvent(self, event):
        if self.thread is None or not self.thread.isRunning():
            event.accept()
            return

        answer = QMessageBox.question(
            self,
            "Processing is still running",
            "BlurGPT is processing a video. Cancel safely and close when it stops?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer == QMessageBox.Yes:
            self._closing_after_processing = True
            self.cancel_processing()
            event.ignore()
        else:
            event.ignore()


def run():
    """Start the Qt application."""
    app = QApplication.instance() or QApplication([])
    app.setApplicationName("BlurGPT")
    window = MainWindow()
    window.show()
    return app.exec()
