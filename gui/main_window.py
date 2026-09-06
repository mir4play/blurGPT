"""Main BlurGPT application window.

The GUI is intentionally independent from the existing processing entry point.
Processing integration will be added through a worker layer so the Qt event loop
never blocks while YOLO/video processing is running.
"""

from pathlib import Path

from PySide6.QtCore import Qt
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


class MainWindow(QMainWindow):
    """Primary BlurGPT window."""

    def __init__(self):
        super().__init__()

        self.manager = JobManager()
        self.setWindowTitle("BlurGPT")
        self.setMinimumSize(900, 620)

        self._build_ui()
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
        add_button = QPushButton("Add videos…")
        add_button.clicked.connect(self.add_videos)
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.refresh_jobs)
        buttons.addWidget(add_button)
        buttons.addWidget(refresh_button)
        input_layout.addLayout(buttons)

        status_card = self._card("Status")
        status_layout = status_card.layout()
        self.status_label = QLabel("Ready")
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(True)
        status_layout.addWidget(self.status_label)
        status_layout.addWidget(self.progress)

        start_button = QPushButton("Start processing")
        start_button.setObjectName("primaryButton")
        start_button.setEnabled(False)
        status_layout.addWidget(start_button)
        self.start_button = start_button

        content.addWidget(input_card, 0, 0)
        content.addWidget(status_card, 0, 1)
        content.setColumnStretch(0, 3)
        content.setColumnStretch(1, 2)
        root.addLayout(content)

        info = QLabel(
            "The processing engine remains unchanged. This first GUI layer "
            "only manages the interface and job queue."
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
            QLabel#info { color: #9aa0a6; padding: 8px; }
            QFrame#card {
                background: #292a2d;
                border: 1px solid #3c4043;
                border-radius: 10px;
            }
            QListWidget {
                background: #202124;
                border: 1px solid #3c4043;
                border-radius: 6px;
                padding: 6px;
            }
            QPushButton {
                background: #3c4043;
                border: 1px solid #5f6368;
                border-radius: 6px;
                padding: 9px 14px;
            }
            QPushButton:hover { background: #4a4d51; }
            QPushButton#primaryButton {
                background: #8ab4f8;
                color: #202124;
                font-weight: 700;
                padding: 11px;
            }
            QProgressBar {
                background: #202124;
                border: 1px solid #3c4043;
                border-radius: 5px;
                text-align: center;
                min-height: 18px;
            }
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
        self.queue_list.clear()
        jobs = self.manager.find_jobs()

        for job in jobs:
            self.queue_list.addItem(f"[{job.source}]  {job.filename}")

        count = len(jobs)
        self.status_label.setText(
            f"{count} video{'s' if count != 1 else ''} waiting"
        )

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
                destination.write_bytes(source.read_bytes())
                copied += 1
            except OSError as error:
                QMessageBox.warning(
                    self,
                    "Could not add video",
                    f"{source.name}\n\n{error}",
                )

        self.refresh_jobs()
        if copied:
            self.status_label.setText(f"Added {copied} video{'s' if copied != 1 else ''}")


def run():
    """Start the Qt application."""
    app = QApplication.instance() or QApplication([])
    app.setApplicationName("BlurGPT")
    window = MainWindow()
    window.show()
    return app.exec()
