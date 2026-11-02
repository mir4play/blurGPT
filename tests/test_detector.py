import importlib
import sys
from types import ModuleType, SimpleNamespace

import pytest


@pytest.mark.parametrize("device", ["cpu", 0, 2])
def test_detector_forwards_selected_device_to_yolo_predict(
    tmp_path, monkeypatch, device
):
    model_path = tmp_path / "model.pt"
    model_path.write_bytes(b"model")
    calls = []
    model_paths = []

    class FakeYOLO:
        def __init__(self, path):
            model_paths.append(path)

        def predict(self, frame, **kwargs):
            calls.append((frame, kwargs))
            return [SimpleNamespace(boxes=None)]

    fake_ultralytics = ModuleType("ultralytics")
    fake_ultralytics.YOLO = FakeYOLO
    monkeypatch.setitem(sys.modules, "ultralytics", fake_ultralytics)

    detector_was_loaded = "core.detector" in sys.modules
    detector_module = importlib.import_module("core.detector")
    monkeypatch.setattr(detector_module, "YOLO", FakeYOLO)

    detector = detector_module.Detector(
        model_path,
        device=device,
        detect_every=1,
        imgsz=640,
    )
    frame = object()

    assert detector.detect(frame) == []
    assert model_paths == [str(model_path)]
    assert calls == [
        (
            frame,
            {"device": device, "imgsz": 640, "verbose": False},
        )
    ]

    if not detector_was_loaded:
        monkeypatch.delitem(sys.modules, "core.detector", raising=False)
