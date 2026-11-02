# Hardware backend inventory

**Source audit date:** 2026-11-01  
**Scope:** source-level inspection of the current `main` implementation. No alternative-hardware runtime tests were performed for this inventory.

This document records what the current code actually selects and validates. It is not a promise that every listed device or backend is supported.

## Reference configuration

The project's reference path remains:

- Inference: PyTorch/Ultralytics on NVIDIA CUDA, with device index `0` by default.
- Encoding: FFmpeg `h264_nvenc`.
- Model: external `models/blurGPT.pt`.

This is the path represented by the existing benchmark history and the maintainer's RTX 4060 Laptop validation. Compatibility work must not change its defaults or add unrelated backend dependencies to its build.

## Current source-level behavior

| Area | Current implementation | Limitation / implication |
|---|---|---|
| Device setting | `core/settings.py` accepts `"cpu"` or a non-negative integer device index. `config.py` defaults to `0`. | An integer is treated as a CUDA device index; there is no general backend/device descriptor. |
| GUI selection | `gui/settings_dialog.py` exposes GPU 0 and CPU. | The UI does not enumerate AMD, Intel XPU, or multiple named accelerator backends. |
| Capability probe | `core/backends.py` reports PyTorch CPU availability, distinguishes NVIDIA CUDA from ROCm/HIP, and probes `torch.xpu` when exposed. | Detection is informational only: it does not select devices, install dependencies, or validate inference. |
| Preflight | `core/preflight.py` uses the capability probe for GPU device checks. It accepts the existing integer device index through PyTorch's CUDA-compatible API and identifies ROCm when the HIP runtime is exposed. | XPU can be detected but cannot yet be selected. The CPU path still requires explicit selection. |
| Inference | `core/detector.py` passes the configured device directly to `YOLO.predict(device=...)`. | Hardware-independent tests cover explicit CPU and integer device forwarding; this does not constitute backend runtime validation. |
| Benchmark environment | `core/benchmark.py` records the CPU identifier, selected inference backend, PyTorch version, CUDA/ROCm runtime versions, CUDA-compatible GPU name, and XPU availability/name when exposed. | Device-name queries are best-effort. XPU is reported for diagnostics but is not selectable for inference. |
| NVENC encoding | `core/video.py` invokes FFmpeg with `h264_nvenc`; preflight checks whether the selected FFmpeg lists that encoder. | Listing the encoder does not guarantee that the installed driver can successfully initialize it at runtime. |
| OpenCV encoding | `core/video.py` supports the `mp4v` OpenCV writer. | This is the current software/compatibility encoder path; no AMF, QSV, or VAAPI path is implemented here. |

Inference and encoding are separate capabilities. Selecting CPU inference does not select a compatible encoder automatically. On a CPU-only system, the current GUI settings therefore need both **CPU** as the inference device and **OpenCV / mp4v** as the video encoder; leaving NVENC selected still triggers the NVENC preflight.

## Compatibility status

| Configuration | Source-level status | Validation status |
|---|---|---|
| NVIDIA CUDA + FFmpeg NVENC | Existing default/reference path | Maintainer benchmarked on RTX 4060 Laptop; preserve as-is |
| CPU inference + OpenCV `mp4v` | Explicit CPU device route and software encoder exist | Unit tests cover CPU setting persistence, preflight, and device forwarding; current-main/frozen-build runtime validation is not recorded, and it is likely substantially slower |
| AMD GPU / ROCm | PyTorch HIP runtime is distinguished from NVIDIA CUDA when the CUDA-compatible API exposes a device; current integer device route is unchanged | Not validated; do not claim support |
| Intel GPU / XPU | PyTorch `torch.xpu` availability is reported when exposed by the installed build | Not selectable in current settings; not implemented/validated for inference |
| New NVIDIA platforms (including DGX Spark) | No platform-specific branch; would use the NVIDIA/PyTorch stack if compatible | Not validated on those platforms |

A CPU option in the settings is not the same as an automatic fallback. BlurGPT does not silently switch from an unavailable GPU to CPU: the selected GPU path reports a preflight error. CPU must be selected explicitly.

## Safe next steps

1. Use the expanded local benchmark metadata when reviewing volunteer reports. Logs remain local; contributors should copy only relevant fields and redact private paths or filenames.
2. Invite volunteers to test CPU and alternative backends with the short procedure in [community compatibility guidance](compatibility.md). A short successful run is enough for an initial compatibility signal; long performance comparisons are optional.
3. Evaluate AMD/ROCm and Intel/XPU in separate dependency environments and, if needed, separate packaging targets. Do not add their packages to the current NVIDIA Windows build by default.
4. Consider a backend validated only after a reproducible runtime report identifies the hardware, OS, driver, PyTorch/Ultralytics versions, workload, and actual encoder.

The capability probe is intentionally descriptive, not a universal device-selection layer. The current CUDA index and NVENC defaults remain unchanged; do not implement automatic fallback or a broad backend selector until each path has a clear dependency and validation plan.

## Related documentation

- [Compatibility and community testing](compatibility.md)
- [Performance benchmarks and conditions](performance.md)
- [Development roadmap](roadmap.md)
- [Hardware portability issue #61](https://github.com/mir4play/BlurGPT/issues/61)
