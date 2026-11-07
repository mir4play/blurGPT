import json
from types import SimpleNamespace

import pytest

import core.preflight as preflight_module
import core.settings as settings_module
from core.backends import BackendCapabilities


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
    values["device"] = "cpu"
    values["gui_advanced_mode"] = True
    settings_module.save_settings(values)

    payload = json.loads(settings_path.read_text(encoding="utf-8"))
    assert payload["version"] == settings_module.SETTINGS_VERSION
    assert payload["settings"]["video_nvenc_preset"] == "p3"

    loaded = settings_module.load_settings()
    assert loaded["detect_every"] == 8
    assert loaded["device"] == "cpu"
    assert loaded["gui_advanced_mode"] is True


def test_preflight_reports_missing_model_without_gpu_dependency(tmp_path, monkeypatch):
    values = settings_module.DEFAULTS.copy()
    values.update({
        "model_path": str(tmp_path / "missing.pt"),
        "device": "cpu",
        "video_encoder": "opencv",
    })

    monkeypatch.setattr(preflight_module, "load_settings", lambda: values)
    monkeypatch.setattr(preflight_module, "import_module", lambda name: object())

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


def test_preflight_accepts_rocm_device_index(tmp_path, monkeypatch):
    model = tmp_path / "model.pt"
    model.write_bytes(b"model")
    values = settings_module.DEFAULTS.copy()
    values.update({"model_path": str(model), "device": 0, "video_encoder": "opencv"})
    capabilities = BackendCapabilities(
        pytorch_available=True,
        cpu_available=True,
        cuda_available=False,
        rocm_available=True,
        xpu_available=False,
        cuda_api_device_count=1,
        xpu_device_count=0,
        rocm_runtime_version="6.3",
    )

    monkeypatch.setattr(preflight_module, "load_settings", lambda: values)
    monkeypatch.setattr(
        preflight_module, "inspect_backend_capabilities", lambda: capabilities
    )

    assert preflight_module.validate_processing_environment() == []


def test_preflight_does_not_treat_xpu_as_a_selectable_cuda_device(tmp_path, monkeypatch):
    model = tmp_path / "model.pt"
    model.write_bytes(b"model")
    values = settings_module.DEFAULTS.copy()
    values.update({"model_path": str(model), "device": 0, "video_encoder": "opencv"})
    capabilities = BackendCapabilities(
        pytorch_available=True,
        cpu_available=True,
        cuda_available=False,
        rocm_available=False,
        xpu_available=True,
        cuda_api_device_count=0,
        xpu_device_count=1,
    )

    monkeypatch.setattr(preflight_module, "load_settings", lambda: values)
    monkeypatch.setattr(
        preflight_module, "inspect_backend_capabilities", lambda: capabilities
    )

    errors = preflight_module.validate_processing_environment()

    assert any("Intel XPU" in error and "does not yet expose" in error for error in errors)


def test_preflight_accepts_explicit_cpu_without_accelerator_probe(tmp_path, monkeypatch):
    model = tmp_path / "model.pt"
    model.write_bytes(b"model")
    values = settings_module.DEFAULTS.copy()
    values.update({
        "model_path": str(model),
        "device": "cpu",
        "video_encoder": "opencv",
    })

    torch_imports = []
    monkeypatch.setattr(preflight_module, "load_settings", lambda: values)
    monkeypatch.setattr(
        preflight_module,
        "import_module",
        lambda name: torch_imports.append(name),
    )
    monkeypatch.setattr(
        preflight_module,
        "inspect_backend_capabilities",
        lambda: pytest.fail("CPU preflight must not probe an accelerator"),
    )

    assert preflight_module.validate_processing_environment() == []
    assert torch_imports == ["torch"]


def test_preflight_reports_missing_pytorch_for_cpu_without_accelerator_probe(
    tmp_path, monkeypatch
):
    model = tmp_path / "model.pt"
    model.write_bytes(b"model")
    values = settings_module.DEFAULTS.copy()
    values.update({
        "model_path": str(model),
        "device": "cpu",
        "video_encoder": "opencv",
    })

    def fail_torch_import(name):
        assert name == "torch"
        raise ModuleNotFoundError("No module named 'torch'")

    monkeypatch.setattr(preflight_module, "load_settings", lambda: values)
    monkeypatch.setattr(preflight_module, "import_module", fail_torch_import)
    monkeypatch.setattr(
        preflight_module,
        "inspect_backend_capabilities",
        lambda: pytest.fail("CPU preflight must not probe an accelerator"),
    )

    errors = preflight_module.validate_processing_environment()

    assert len(errors) == 1
    assert "CPU inference requires PyTorch" in errors[0]
    assert "ModuleNotFoundError: No module named 'torch'" in errors[0]


def test_preflight_checks_encoder_independently_of_cpu_inference(
    tmp_path, monkeypatch
):
    model = tmp_path / "model.pt"
    model.write_bytes(b"model")
    values = settings_module.DEFAULTS.copy()
    values.update({
        "model_path": str(model),
        "device": "cpu",
        "video_encoder": "h264_nvenc",
    })
    encoder_checks = []

    monkeypatch.setattr(preflight_module, "load_settings", lambda: values)
    monkeypatch.setattr(preflight_module, "import_module", lambda name: object())
    monkeypatch.setattr(
        preflight_module,
        "_validate_nvenc",
        lambda errors: encoder_checks.append("h264_nvenc"),
    )
    monkeypatch.setattr(
        preflight_module,
        "inspect_backend_capabilities",
        lambda: pytest.fail("CPU inference must not probe a GPU"),
    )

    assert preflight_module.validate_processing_environment() == []
    assert encoder_checks == ["h264_nvenc"]


@pytest.mark.parametrize(
    ("platform", "expect_hidden_console"),
    [("win32", True), ("linux", False)],
)
def test_nvenc_preflight_hides_console_only_on_windows(
    tmp_path, monkeypatch, platform, expect_hidden_console
):
    ffmpeg = tmp_path / "ffmpeg.exe"
    calls = []
    no_window_flag = 0x08000000

    monkeypatch.setattr(preflight_module, "resolve_ffmpeg", lambda: ffmpeg)
    monkeypatch.setattr(preflight_module.sys, "platform", platform)
    monkeypatch.setattr(
        preflight_module.subprocess,
        "CREATE_NO_WINDOW",
        no_window_flag,
        raising=False,
    )

    def fake_run(command, **kwargs):
        calls.append((command, kwargs))
        return SimpleNamespace(stdout="h264_nvenc")

    monkeypatch.setattr(preflight_module.subprocess, "run", fake_run)

    errors = []
    preflight_module._validate_nvenc(errors)

    assert errors == []
    assert calls[0][0] == [str(ffmpeg), "-hide_banner", "-encoders"]
    assert calls[0][1]["capture_output"] is True
    assert calls[0][1]["text"] is True
    assert calls[0][1]["timeout"] == 5
    if expect_hidden_console:
        assert calls[0][1]["creationflags"] == no_window_flag
    else:
        assert "creationflags" not in calls[0][1]


