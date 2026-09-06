"""BlurGPT settings dialog."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QSpinBox,
    QVBoxLayout,
)

from core.settings import load_settings, profile_values, save_settings


class SettingsDialog(QDialog):
    """User-facing settings without exposing Python configuration files."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("BlurGPT Settings")
        self.setMinimumWidth(520)

        settings = load_settings()

        root = QVBoxLayout(self)
        intro = QLabel(
            "Choose a processing profile or tune the individual parameters. "
            "Changes apply to the next processing run."
        )
        intro.setWordWrap(True)
        intro.setObjectName("secondary")
        root.addWidget(intro)

        form = QFormLayout()
        form.setSpacing(12)

        self.profile = QComboBox()
        self.profile.addItem("Recommended", "Recommended")
        self.profile.addItem("Performance", "Performance")
        self.profile.addItem("Quality", "Quality")
        self.profile.addItem("Custom", "Custom")
        self.profile.setCurrentIndex(3)
        self.profile.setToolTip(
            "Recommended balances detection and speed. Performance favors throughput; "
            "Quality increases detection frequency and inference resolution."
        )
        self.profile.currentIndexChanged.connect(self._profile_changed)
        form.addRow("Processing profile", self.profile)

        self.device = QComboBox()
        self.device.addItem("GPU 0 (recommended)", 0)
        self.device.addItem("CPU (not recommended)", "cpu")
        self.device.setCurrentIndex(0 if settings["device"] == 0 else 1)
        self.device.setToolTip("CUDA device used by YOLO inference.")
        form.addRow("Device", self.device)

        self.detect_every = QSpinBox()
        self.detect_every.setRange(1, 100)
        self.detect_every.setValue(int(settings["detect_every"]))
        self.detect_every.setToolTip(
            "Run YOLO every N frames. Lower values improve detection continuity "
            "but increase GPU workload."
        )
        form.addRow("Detection interval", self.detect_every)

        self.imgsz = QSpinBox()
        self.imgsz.setRange(320, 4096)
        self.imgsz.setSingleStep(32)
        self.imgsz.setValue(int(settings["imgsz"]))
        self.imgsz.setToolTip(
            "YOLO inference image size. Higher values can improve small-object "
            "detection but use more VRAM."
        )
        form.addRow("Inference size", self.imgsz)

        self.pixel_size = QSpinBox()
        self.pixel_size.setRange(1, 100)
        self.pixel_size.setValue(int(settings["pixel_size"]))
        self.pixel_size.setToolTip("Larger values produce stronger pixelation.")
        form.addRow("Pixelation size", self.pixel_size)

        self.box_margin = QSpinBox()
        self.box_margin.setRange(0, 200)
        self.box_margin.setValue(int(settings["box_margin"]))
        self.box_margin.setToolTip("Extra pixels added around each detection box.")
        form.addRow("Detection margin", self.box_margin)

        self.encoder = QComboBox()
        self.encoder.addItem("NVIDIA NVENC (recommended)", "h264_nvenc")
        self.encoder.addItem("OpenCV / mp4v (fallback)", "opencv")
        encoder_index = 0 if settings["video_encoder"] == "h264_nvenc" else 1
        self.encoder.setCurrentIndex(encoder_index)
        self.encoder.setToolTip(
            "NVENC uses the NVIDIA hardware encoder. OpenCV is the compatibility fallback."
        )
        form.addRow("Video encoder", self.encoder)

        self.cq = QSpinBox()
        self.cq.setRange(0, 51)
        self.cq.setValue(int(settings["video_nvenc_cq"]))
        self.cq.setToolTip(
            "NVENC constant-quality value. Lower values generally mean higher quality "
            "and larger files."
        )
        form.addRow("NVENC quality (CQ)", self.cq)

        self.preset = QComboBox()
        for value in ("p1", "p2", "p3", "p4", "p5", "p6", "p7"):
            self.preset.addItem(value.upper(), value)
        preset = str(settings["video_nvenc_preset"]).lower()
        index = self.preset.findData(preset)
        self.preset.setCurrentIndex(index if index >= 0 else 3)
        self.preset.setToolTip(
            "NVENC performance/quality preset. P4 is the recommended balance."
        )
        form.addRow("NVENC preset", self.preset)

        root.addLayout(form)
        self._apply_profile("Custom")
        self._set_profile_from_current()

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        reset_button = buttons.addButton(
            "Restore recommended", QDialogButtonBox.ResetRole
        )
        reset_button.clicked.connect(self._restore_defaults)
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

    def _profile_changed(self):
        name = self.profile.currentData()
        if name != "Custom":
            self._apply_profile(name)

    def _apply_profile(self, name: str):
        if name == "Custom":
            return
        values = profile_values(name)
        self.detect_every.setValue(int(values["detect_every"]))
        self.imgsz.setValue(int(values["imgsz"]))
        self.pixel_size.setValue(int(values["pixel_size"]))
        self.box_margin.setValue(int(values["box_margin"]))
        self.encoder.setCurrentIndex(0 if values["video_encoder"] == "h264_nvenc" else 1)
        self.cq.setValue(int(values["video_nvenc_cq"]))
        index = self.preset.findData(str(values["video_nvenc_preset"]).lower())
        self.preset.setCurrentIndex(index if index >= 0 else 3)

    def _set_profile_from_current(self):
        for index in range(self.profile.count() - 1):
            name = self.profile.itemData(index)
            values = profile_values(name)
            if all(
                getattr(self, field).value() == int(values[key])
                for field, key in (
                    ("detect_every", "detect_every"),
                    ("imgsz", "imgsz"),
                    ("pixel_size", "pixel_size"),
                    ("box_margin", "box_margin"),
                    ("cq", "video_nvenc_cq"),
                )
            ) and self.encoder.currentData() == values["video_encoder"] \
                    and self.preset.currentData() == values["video_nvenc_preset"]:
                self.profile.setCurrentIndex(index)
                return
        self.profile.setCurrentIndex(3)

    def _restore_defaults(self):
        """Restore recommended values in the dialog without saving yet."""
        values = profile_values("Recommended")
        self.device.setCurrentIndex(0 if values["device"] == 0 else 1)
        self.profile.setCurrentIndex(0)
        self._apply_profile("Recommended")

    def _save(self):
        current_settings = load_settings()
        save_settings({
            "model_path": current_settings["model_path"],
            "device": self.device.currentData(),
            "detect_every": self.detect_every.value(),
            "imgsz": self.imgsz.value(),
            "pixel_size": self.pixel_size.value(),
            "box_margin": self.box_margin.value(),
            "video_encoder": self.encoder.currentData(),
            "video_codec": "mp4v",
            "video_nvenc_cq": self.cq.value(),
            "video_nvenc_preset": self.preset.currentData(),
        })
        self.accept()
