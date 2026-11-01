from types import SimpleNamespace

import core.benchmark as benchmark


def _device_api(available=False, count=0, name=None, name_error=None):
    def get_device_name(index):
        if name_error is not None:
            raise name_error
        return name

    return SimpleNamespace(
        is_available=lambda: available,
        device_count=lambda: count,
        get_device_name=get_device_name,
    )


def _torch_module(
    *,
    cuda_available=False,
    cuda_count=0,
    cuda_name=None,
    cuda_version=None,
    hip_version=None,
    xpu_available=False,
    xpu_count=0,
    xpu_name=None,
):
    return SimpleNamespace(
        __version__="2.8.0",
        version=SimpleNamespace(cuda=cuda_version, hip=hip_version),
        cuda=_device_api(cuda_available, cuda_count, cuda_name),
        xpu=_device_api(xpu_available, xpu_count, xpu_name),
    )


def _patch_environment(monkeypatch, torch_module, cpu_name="Test CPU"):
    monkeypatch.setattr(benchmark, "import_module", lambda name: torch_module)
    monkeypatch.setattr(benchmark.platform, "processor", lambda: cpu_name)
    monkeypatch.setattr(benchmark.platform, "platform", lambda: "Test OS")
    monkeypatch.setattr(benchmark, "_ffmpeg_version", lambda: "FFmpeg test")


def test_collect_environment_reports_cpu_and_cuda_metadata(monkeypatch):
    torch_module = _torch_module(
        cuda_available=True,
        cuda_count=2,
        cuda_name="NVIDIA Test GPU",
        cuda_version="12.8",
    )
    _patch_environment(monkeypatch, torch_module, "Intel Test CPU")

    environment = benchmark.collect_environment(device=1)

    assert environment["cpu"] == "Intel Test CPU"
    assert environment["ffmpeg"] == "FFmpeg test"
    assert environment["pytorch"] == "2.8.0"
    assert environment["cuda"] == "12.8"
    assert environment["rocm"] is None
    assert environment["gpu_backend"] == "CUDA"
    assert environment["gpu"] == "NVIDIA Test GPU"
    assert environment["cuda_device"] == 1
    assert environment["selected_inference_backend"] == "CUDA"
    assert environment["xpu_available"] is False


def test_collect_environment_distinguishes_rocm_from_cuda_api(monkeypatch):
    torch_module = _torch_module(
        cuda_available=True,
        cuda_count=1,
        cuda_name="AMD Test GPU",
        hip_version="6.3",
    )
    _patch_environment(monkeypatch, torch_module)

    environment = benchmark.collect_environment(device=0)

    assert environment["cuda"] is None
    assert environment["rocm"] == "6.3"
    assert environment["gpu_backend"] == "ROCm"
    assert environment["gpu"] == "AMD Test GPU"
    assert environment["selected_inference_backend"] == "ROCm"


def test_collect_environment_keeps_cpu_selection_explicit(monkeypatch):
    torch_module = _torch_module(
        cuda_available=True,
        cuda_count=1,
        cuda_name="NVIDIA Test GPU",
        cuda_version="12.8",
        xpu_available=True,
        xpu_count=1,
        xpu_name="Intel Test XPU",
    )
    _patch_environment(monkeypatch, torch_module)

    environment = benchmark.collect_environment(device="cpu")

    assert environment["selected_inference_backend"] == "CPU"
    assert environment["gpu_backend"] == "CUDA"
    assert environment["gpu"] == "NVIDIA Test GPU"
    assert environment["cuda_device"] == 0
    assert environment["xpu_available"] is True
    assert environment["xpu_gpu"] == "Intel Test XPU"
    assert environment["xpu_device"] == 0


def test_collect_environment_reports_xpu_without_claiming_it_is_selected(monkeypatch):
    torch_module = _torch_module(
        xpu_available=True,
        xpu_count=1,
        xpu_name="Intel Test XPU",
    )
    _patch_environment(monkeypatch, torch_module)

    environment = benchmark.collect_environment(device=0)

    assert environment["xpu_available"] is True
    assert environment["xpu_gpu"] == "Intel Test XPU"
    assert environment["selected_inference_backend"] == "unavailable"
    assert environment["gpu"] is None


def test_collect_environment_does_not_fail_when_device_name_probe_errors(monkeypatch):
    torch_module = _torch_module(
        cuda_available=True,
        cuda_count=1,
        cuda_version="12.8",
    )
    def fail_device_name(_index):
        raise RuntimeError("driver query failed")

    torch_module.cuda.get_device_name = fail_device_name
    _patch_environment(monkeypatch, torch_module)

    environment = benchmark.collect_environment(device=0)

    assert environment["selected_inference_backend"] == "CUDA"
    assert environment["gpu"] is None
    assert environment["gpu_name_error"] == "RuntimeError: driver query failed"


def test_collect_environment_handles_missing_pytorch(monkeypatch):
    def fail_import(_name):
        raise ModuleNotFoundError("No module named 'torch'")

    monkeypatch.setattr(benchmark, "import_module", fail_import)
    monkeypatch.setattr(benchmark.platform, "processor", lambda: "Test CPU")
    monkeypatch.setattr(benchmark.platform, "platform", lambda: "Test OS")
    monkeypatch.setattr(benchmark, "_ffmpeg_version", lambda: "FFmpeg test")

    environment = benchmark.collect_environment(device=0)

    assert environment["cpu"] == "Test CPU"
    assert environment["pytorch"] is None
    assert environment["selected_inference_backend"] == "unavailable"
    assert environment["ffmpeg"] == "FFmpeg test"
    assert "ModuleNotFoundError" in environment["torch_import_error"]

    cpu_environment = benchmark.collect_environment(device="cpu")
    assert cpu_environment["selected_inference_backend"] == "unavailable"



def test_collect_environment_reports_explicit_cpu_only_runtime(monkeypatch):
    torch_module = _torch_module()
    _patch_environment(monkeypatch, torch_module)

    environment = benchmark.collect_environment(device="cpu")

    assert environment["selected_inference_backend"] == "CPU"
    assert environment["gpu_backend"] is None
    assert environment["gpu"] is None
    assert environment["xpu_available"] is False
