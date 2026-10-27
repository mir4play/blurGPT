import json

import pytest

import core.preflight as preflight_module
import core.settings as settings_module


def test_validate_settings_normalizes_and_rejects_invalid_values():
    values = settings_module.DEFAULTS.copy()
    values.update({"device": "1", "detect_every": "8", "imgsz": "640", "gui_advanced_mode": 1})

    validated = settings_module.validate_settings(values)

    assert validated["device"] == 1
    assert validated["detect_every"] == 8
    assert validated["imgsz"] == 640
    assert validated["gui_advanced_mode"] is True

    invalid = values.copy()
    invalid["imgsz"] = 641
    try:
        settings_module.validate_settings(invalid)
    except ValueError as exc:
        assert "multiple of 32" in str(exc)
    else:
        raise AssertionError("invalid inference size should be rejected")


def test_save_and_load_settings_round_trip(tmp_path, monkeypatch):
    settings_path = tmp_path / "config" / "settings.json"
    monkeypatch.setattr(settings_module, "SETTINGS_PATH", settings_path)
    monkeypatch.setattr(settings_module, "SETTINGS_DIR", settings_path.parent)

    values = settings_module.profile_values("Performance")
    values["gui_advanced_mode"] = True
    settings_module.save_settings(values)

    payload = json.loads(settings_path.read_text(encoding="utf-8"))
    assert payload["version"] == settings_module.SETTINGS_VERSION
    assert payload["settings"]["video_nvenc_preset"] == "p3"

    loaded = settings_module.load_settings()
    assert loaded["detect_every"] == 8
    assert loaded["gui_advanced_mode"] is True


def test_preflight_reports_missing_model_without_gpu_dependency(tmp_path, monkeypatch):
    values = settings_module.DEFAULTS.copy()
    values.update({
        "model_path": str(tmp_path / "missing.pt"),
        "device": "cpu",
        "video_encoder": "opencv",
    })

    monkeypatch.setattr(preflight_module, "load_settings", lambda: values)

    errors = preflight_module.validate_processing_environment()

    assert len(errors) == 1
    assert "YOLO model was not found" in errors[0]
    assert "Place the model file at:" in errors[0]


def test_preflight_reports_unavailable_cuda_device(tmp_path, monkeypatch):
    pytest.importorskip("torch")
    import torch

    model = tmp_path / "model.pt"
    model.write_bytes(b"model")
    values = settings_module.DEFAULTS.copy()
    values.update({"model_path": str(model), "device": 2, "video_encoder": "opencv"})

    monkeypatch.setattr(preflight_module, "load_settings", lambda: values)
    monkeypatch.setattr(torch.cuda, "is_available", lambda: True)
    monkeypatch.setattr(torch.cuda, "device_count", lambda: 1)

    errors = preflight_module.validate_processing_environment()

    assert any("CUDA device 2 is not available" in error for error in errors)
