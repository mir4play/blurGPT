"""Main BlurGPT application window."""

import shutil
import time
from pathlib import Path

from PySide6.QtCore import QThread, QTimer
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
from core.paths import ROOT_DIR
from gui.settings_dialog import SettingsDialog
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
        self._advanced_mode = False

        self.setWindowTitle("BlurGPT")
        self.setMinimumSize(900, 620)
        self._build_ui()

        self._heartbeat = QTimer(self)
        self._heartbeat.setInterval(1000)
        self._heartbeat.timeout.connect(self._update_heartbeat)
        self.refresh_jobs()

    def _build_ui(self):
        central = QWidget()
        root = QVBoxLayout(central)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(16)

        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("BlurGPT")
        title.setObjectName("title")
        subtitle = QLabel("Video anonymization — faces and license plates")
        subtitle.setObjectName("subtitle")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header.addLayout(title_box)
        header.addStretch()
        self.mode_button = QPushButton("Advanced")
        self.mode_button.setCheckable(True)
        self.mode_button.setToolTip("Show detailed live processing metrics")
        self.mode_button.clicked.connect(self._toggle_advanced)
        header.addWidget(self.mode_button)
        root.addLayout(header)

        content = QGridLayout()
        content.setHorizontalSpacing(16)
        content.setVerticalSpacing(12)

        input_card = self._card("Input queue")
        input_layout = input_card.layout()
        self.queue_list = QListWidget()
        self.queue_list.setMinimumHeight(260)
        self.queue_list.setSelectionMode(QListWidget.ExtendedSelection)
        input_layout.addWidget(self.queue_list)

        buttons = QHBoxLayout()
        self.add_button = QPushButton("Add videos…")
        self.add_button.clicked.connect(self.add_videos)
        self.remove_button = QPushButton("Remove selected")
        self.remove_button.setToolTip(
            "Remove selected queued videos. Original source files are not deleted."
        )
        self.remove_button.clicked.connect(self.remove_selected_videos)
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.refresh_jobs)
        buttons.addWidget(self.add_button)
        buttons.addWidget(self.remove_button)
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
        self.progress.setTextVisible(False)
        status_layout.addWidget(self.status_label)
        status_layout.addWidget(self.current_label)
        status_layout.addWidget(self.progress)

        self.progress_metrics = QLabel("0%")
        self.progress_metrics.setObjectName("progressMetrics")
        status_layout.addWidget(self.progress_metrics)

        self.heartbeat_label = QLabel("Idle")
        self.heartbeat_label.setObjectName("secondary")
        status_layout.addWidget(self.heartbeat_label)

        self.metrics_card = self._card("Live metrics")
        metrics_layout = self.metrics_card.layout()
        self.metrics_label = QLabel("Advanced metrics are available while processing.")
        self.metrics_label.setObjectName("metrics")
        self.metrics_label.setWordWrap(True)
        metrics_layout.addWidget(self.metrics_label)
        self.metrics_card.setVisible(False)

        action_buttons = QHBoxLayout()
        self.start_button = QPushButton("Start processing")
        self.start_button.setObjectName("primaryButton")
        self.start_button.clicked.connect(self.start_processing)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setEnabled(False)
        self.cancel_button.clicked.connect(self.cancel_processing)
        self.settings_button = QPushButton("Settings…")
        self.settings_button.clicked.connect(self.open_settings)
        action_buttons.addWidget(self.start_button)
        action_buttons.addWidget(self.cancel_button)
        action_buttons.addWidget(self.settings_button)
        status_layout.addLayout(action_buttons)

        content.addWidget(input_card, 0, 0)
        content.addWidget(status_card, 0, 1)
        content.addWidget(self.metrics_card, 1, 1)
        content.setColumnStretch(0, 3)
        content.setColumnStretch(1, 2)
        content.setRowStretch(0, 1)
        root.addLayout(content)

        info = QLabel(
            "Processing runs in a background worker. The window stays responsive "
            "while YOLO and NVENC are working. Settings are saved separately "
            "from the Python source and apply to the next processing run."
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
            QLabel#progressMetrics { font-size: 16px; font-weight: 600; padding: 2px 0; }
            QLabel#metrics { line-height: 1.4; }
            QFrame#card { background: #292a2d; border: 1px solid #3c4043; border-radius: 10px; }
            QListWidget { background: #202124; border: 1px solid #3c4043; border-radius: 6px; padding: 6px; }
            QPushButton { background: #3c4043; border: 1px solid #5f6368; border-radius: 6px; padding: 9px 14px; }
            QPushButton:hover { background: #4a4d51; }
            QPushButton:disabled { color: #777; }
            QPushButton#primaryButton { background: #8ab4f8; color: #202124; font-weight: 700; padding: 11px; }
            QProgressBar { background: #202124; border: 1px solid #3c4043; border-radius: 5px; min-height: 18px; }
            QProgressBar::chunk { background: #5f6368; border-radius: 4px; }
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
        self.status_label.setText(f"{count} video{'s' if count != 1 else ''} waiting")
        self.start_button.setEnabled(count > 0)
        self.remove_button.setEnabled(count > 0)

    def add_videos(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select videos", str(ROOT_DIR),
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
                shutil.copy2(source, destination)
                copied += 1
            except OSError as error:
                QMessageBox.warning(self, "Could not add video", f"{source.name}\n\n{error}")
        self.refresh_jobs()
        if copied:
            self.status_label.setText(f"Added {copied} video{'s' if copied != 1 else ''}")

    def remove_selected_videos(self):
        selected = self.queue_list.selectedItems()
        if not selected:
            self.status_label.setText("Select one or more videos to remove")
            return
        filenames = [item.text().split("]  ", 1)[1] for item in selected if "]  " in item.text()]
        count = len(filenames)
        answer = QMessageBox.question(
            self, "Remove from queue",
            f"Remove {count} selected video{'s' if count != 1 else ''} from the BlurGPT queue?\n\n"
            "The original source files will not be deleted.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return
        removed = 0
        for filename in filenames:
            path = self.manager.input_dir / filename
            try:
                if path.is_file():
                    path.unlink()
                    removed += 1
            except OSError as error:
                QMessageBox.warning(self, "Could not remove video", f"{filename}\n\n{error}")
        self.refresh_jobs()
        self.status_label.setText(f"Removed {removed} video{'s' if removed != 1 else ''} from queue")

    def open_settings(self):
        if self.thread is not None and self.thread.isRunning():
            return
        dialog = SettingsDialog(self)
        if dialog.exec():
            self.status_label.setText("Settings saved — ready for the next run")

    def _toggle_advanced(self, checked):
        self._advanced_mode = bool(checked)
        self.mode_button.setText("Clean" if checked else "Advanced")
        self.metrics_card.setVisible(checked)
        self.adjustSize()

    def start_processing(self):
        if self.thread is not None and self.thread.isRunning():
            return
        self.thread = QThread(self)
        self.worker = ProcessingWorker()
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.progress.connect(self._on_progress)
        self.worker.status.connect(self._on_status)
        self.worker.metrics.connect(self._on_metrics)
        self.worker.finished.connect(self._on_finished)
        self.worker.failed.connect(self._on_failed)
        self.worker.finished.connect(self.thread.quit)
        self.worker.failed.connect(self.thread.quit)
        self.thread.finished.connect(self._cleanup_worker)
        self._set_processing_state(True)
        self.progress.setValue(0)
        self.progress_metrics.setText("0%")
        self._last_progress = 0
        self._processing_started_at = time.monotonic()
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
        self.progress_metrics.setText(f"{value}%")

    def _on_status(self, message):
        self.status_label.setText(message)
        if ": " in message:
            self.current_label.setText(message.split(": ", 1)[1])

    def _on_metrics(self, metrics):
        percent = metrics.get("percent", 0.0)
        frames = metrics.get("frames", 0)
        total = metrics.get("total_frames", 0)
        fps = metrics.get("fps", 0.0)
        source_fps = metrics.get("video_fps", 0.0)
        elapsed = metrics.get("elapsed", 0.0)
        yolo = metrics.get("yolo", 0.0)
        pixel = metrics.get("pixel", 0.0)
        write = metrics.get("write", 0.0)
        encoder = metrics.get("encoder") or "—"
        resolution = f"{metrics.get('width', 0)}×{metrics.get('height', 0)}"
        device = metrics.get("device")
        device_text = f"GPU {device}" if isinstance(device, int) else str(device or "—")

        if total:
            self.progress_metrics.setText(
                f"{frames:,} / {total:,} frames  ·  {percent:.1f}%  ·  "
                f"{fps:.1f} FPS"
            )
        else:
            self.progress_metrics.setText(f"{frames:,} frames  ·  {fps:.1f} FPS")

        minutes, seconds = divmod(int(elapsed), 60)
        self.metrics_label.setText(
            f"<b>Throughput</b>  {fps:.2f} FPS average<br>"
            f"<b>Source</b>  {source_fps:.2f} FPS  ·  {resolution}<br>"
            f"<b>Elapsed</b>  {minutes:02d}:{seconds:02d}<br>"
            f"<b>YOLO</b>  {yolo:.2f}s cumulative  ·  "
            f"<b>Pixelation</b>  {pixel:.2f}s  ·  <b>Encoding</b>  {write:.2f}s<br>"
            f"<b>Encoder</b>  {encoder}  ·  <b>Device</b>  {device_text}"
        )

    def _update_heartbeat(self):
        if self._processing_started_at is None:
            return
        elapsed = int(time.monotonic() - self._processing_started_at)
        minutes, seconds = divmod(elapsed, 60)
        self.heartbeat_label.setText(
            f"Worker active • elapsed {minutes:02d}:{seconds:02d} • last frame progress {self._last_progress}%"
        )

    def _on_finished(self, result):
        self._heartbeat.stop()
        self._processing_started_at = None
        if result.get("cancelled"):
            self.status_label.setText("Cancelled safely")
        else:
            self.status_label.setText(f"Finished — {result['succeeded']} succeeded, {result['failed']} failed")
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
        self.remove_button.setEnabled(not running)
        self.refresh_button.setEnabled(not running)
        self.settings_button.setEnabled(not running)
        self.start_button.setEnabled(not running and bool(self.manager.find_jobs()))
        self.cancel_button.setEnabled(running)

    def closeEvent(self, event):
        if self.thread is None or not self.thread.isRunning():
            event.accept()
            return
        answer = QMessageBox.question(
            self, "Processing is still running",
            "BlurGPT is processing a video. Cancel safely and close when it stops?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
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
