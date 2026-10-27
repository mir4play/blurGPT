"""BlurGPT graphical application entry point."""

from PySide6.QtWidgets import QApplication

from core.runtime import ensure_runtime_directories
from gui.main_window import MainWindow


def run():
    app = QApplication.instance() or QApplication([])
    ensure_runtime_directories()
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(run())
