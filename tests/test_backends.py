from types import SimpleNamespace

import core.backends as backends


def _device_api(available, count=0):
    return SimpleNamespace(
        is_available=lambda: available,
        device_count=lambda: count,
    )


def _torch_module(*, cuda_available=False, cuda_count=0, cuda_version=None,
                  hip_version=None, xpu_available=False, xpu_count=0):
    return SimpleNamespace(
        __version__="2.8.0",
        version=SimpleNamespace(cuda=cuda_version, hip=hip_version),
        cuda=_device_api(cuda_available, cuda_count),
        xpu=_device_api(xpu_available, xpu_count),
    )


def test_inspect_backend_capabilities_reports_cpu_only_build():
    capabilities = backends.inspect_backend_capabilities(
        _torch_module(cuda_version=None)
    )

    assert capabilities.pytorch_available is True
    assert capabilities.cpu_available is True
    assert capabilities.cuda_available is False
    assert capabilities.rocm_available is False
    assert capabilities.xpu_available is False
    assert capabilities.cuda_api_available is False


def test_inspect_backend_capabilities_identifies_cuda_devices():
    capabilities = backends.inspect_backend_capabilities(
        _torch_module(cuda_available=True, cuda_count=2, cuda_version="12.8")
    )

    assert capabilities.cuda_available is True
    assert capabilities.rocm_available is False
    assert capabilities.cuda_api_available is True
    assert capabilities.cuda_api_backend_name == "CUDA"
    assert capabilities.cuda_api_device_count == 2
    assert capabilities.cuda_runtime_version == "12.8"


def test_inspect_backend_capabilities_distinguishes_rocm_from_cuda_api():
    capabilities = backends.inspect_backend_capabilities(
        _torch_module(cuda_available=True, cuda_count=1, hip_version="6.3")
    )

    assert capabilities.cuda_available is False
    assert capabilities.rocm_available is True
    assert capabilities.cuda_api_available is True
    assert capabilities.cuda_api_backend_name == "ROCm"
    assert capabilities.cuda_api_device_count == 1
    assert capabilities.rocm_runtime_version == "6.3"


def test_inspect_backend_capabilities_reports_xpu_without_selecting_it():
    capabilities = backends.inspect_backend_capabilities(
        _torch_module(xpu_available=True, xpu_count=1)
    )

    assert capabilities.xpu_available is True
    assert capabilities.xpu_device_count == 1
    assert capabilities.cuda_api_available is False


def test_inspect_backend_capabilities_preserves_probe_errors():
    def fail_probe():
        raise RuntimeError("driver mismatch")

    failing_api = SimpleNamespace(
        is_available=fail_probe,
        device_count=lambda: 1,
    )
    torch_module = SimpleNamespace(
        __version__="2.8.0",
        version=SimpleNamespace(cuda="12.8", hip=None),
        cuda=failing_api,
    )

    capabilities = backends.inspect_backend_capabilities(torch_module)

    assert capabilities.cuda_available is False
    assert capabilities.cuda_probe_error == "RuntimeError: driver mismatch"


def test_inspect_backend_capabilities_reports_torch_import_failure(monkeypatch):
    def fail_import(_name):
        raise ModuleNotFoundError("No module named 'torch'")

    monkeypatch.setattr(backends, "import_module", fail_import)

    capabilities = backends.inspect_backend_capabilities()

    assert capabilities.pytorch_available is False
    assert capabilities.cpu_available is False
    assert capabilities.cuda_api_available is False
    assert "ModuleNotFoundError" in capabilities.torch_import_error
