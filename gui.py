"""BlurGPT graphical application entry point."""

from PySide6.QtWidgets import QApplication

from gui.main_window import MainWindow


def run():
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(run())
