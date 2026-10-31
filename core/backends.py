"""Non-mutating capability detection for PyTorch inference backends.

This module reports what the installed PyTorch build exposes. It does not
select a device, install backend dependencies, or choose a video encoder.
"""

from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from typing import Any


@dataclass(frozen=True)
class BackendCapabilities:
    """Snapshot of inference capabilities exposed by the current PyTorch build."""

    pytorch_available: bool
    cpu_available: bool
    cuda_available: bool
    rocm_available: bool
    xpu_available: bool
    cuda_api_device_count: int
    xpu_device_count: int
    pytorch_version: str | None = None
    cuda_runtime_version: str | None = None
    rocm_runtime_version: str | None = None
    torch_import_error: str | None = None
    cuda_probe_error: str | None = None
    xpu_probe_error: str | None = None

    @property
    def cuda_api_available(self) -> bool:
        """Whether the PyTorch CUDA-compatible device API exposes a GPU."""
        return self.cuda_available or self.rocm_available

    @property
    def cuda_api_backend_name(self) -> str:
        """Name the backend behind the PyTorch CUDA-compatible API."""
        return "ROCm" if self.rocm_available else "CUDA"


def _version_string(value: Any) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None


def _probe_device_api(torch_module: Any, api_name: str) -> tuple[bool, int, str | None]:
    """Probe one PyTorch device API without allowing probe errors to escape."""
    api = getattr(torch_module, api_name, None)
    if api is None:
        return False, 0, None

    is_available = getattr(api, "is_available", None)
    device_count = getattr(api, "device_count", None)
    if not callable(is_available) or not callable(device_count):
        return False, 0, None

    try:
        if not is_available():
            return False, 0, None
        count = max(0, int(device_count()))
        return count > 0, count, None
    except Exception as exc:
        return False, 0, f"{type(exc).__name__}: {exc}"


def inspect_backend_capabilities(torch_module: Any | None = None) -> BackendCapabilities:
    """Inspect CPU, CUDA, ROCm/HIP and XPU availability without selecting a device.

    The torch.cuda API is also exposed by PyTorch ROCm builds. The HIP runtime
    version distinguishes ROCm from NVIDIA CUDA. XPU is reported separately
    because BlurGPT does not yet expose XPU device selection.

    The optional module argument allows capability decisions to be tested
    without installing PyTorch or requiring accelerator hardware.
    """
    if torch_module is None:
        try:
            torch_module = import_module("torch")
        except Exception as exc:
            return BackendCapabilities(
                pytorch_available=False,
                cpu_available=False,
                cuda_available=False,
                rocm_available=False,
                xpu_available=False,
                cuda_api_device_count=0,
                xpu_device_count=0,
                torch_import_error=f"{type(exc).__name__}: {exc}",
            )

    version = getattr(torch_module, "version", None)
    cuda_runtime_version = _version_string(getattr(version, "cuda", None))
    rocm_runtime_version = _version_string(getattr(version, "hip", None))
    cuda_api_available, cuda_api_device_count, cuda_probe_error = (
        _probe_device_api(torch_module, "cuda")
    )
    xpu_available, xpu_device_count, xpu_probe_error = _probe_device_api(
        torch_module, "xpu"
    )

    rocm_available = cuda_api_available and rocm_runtime_version is not None
    cuda_available = cuda_api_available and not rocm_available

    return BackendCapabilities(
        pytorch_available=True,
        cpu_available=True,
        cuda_available=cuda_available,
        rocm_available=rocm_available,
        xpu_available=xpu_available,
        cuda_api_device_count=cuda_api_device_count,
        xpu_device_count=xpu_device_count,
        pytorch_version=_version_string(getattr(torch_module, "__version__", None)),
        cuda_runtime_version=cuda_runtime_version,
        rocm_runtime_version=rocm_runtime_version,
        cuda_probe_error=cuda_probe_error,
        xpu_probe_error=xpu_probe_error,
    )
