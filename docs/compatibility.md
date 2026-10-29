# Hardware compatibility and community testing

BlurGPT's current reference path is the NVIDIA/CUDA inference setup with FFmpeg `h264_nvenc` encoding. It reflects the performance-focused path developed and tested on the maintainer's hardware. Compatibility work exists to make the application usable by more people, not to replace or slow down that reference path.

Alternative configurations may be slower, may need different dependencies, or may require separate builds. Do not assume that a GPU is supported just because it is detected by the operating system.

## Current support status

Use precise status descriptions when sharing results:

- **Community-reported** — a contributor reports a result on a named configuration; maintainers have not independently reproduced it.
- **Reproduced** — another test has repeated the result with sufficiently similar hardware, software, and workload details.
- **Maintainer-validated** — the maintainers have tested the configuration and documented the relevant environment and outcome.

A successful report for one model, driver, operating system, or encoder does not establish universal support for that hardware family.

## Run a small, safe test

Volunteers do not need to run long videos or benchmark every profile. A short, representative clip is enough to provide an initial compatibility signal.

1. Keep your known-working installation intact. For experimental backends or dependency sets, use a separate checkout, environment, or build rather than replacing the NVIDIA reference setup.
2. Use a short video you own or are permitted to test. Around 30–60 seconds is a useful starting point; no long batch is required.
3. Record the BlurGPT version/build, operating system, CPU/GPU, inference backend/device, and actual video encoder if known.
4. Record the input resolution and frame rate, clip duration or frame count, and the relevant inference settings (profile, `detect_every`, and `imgsz`).
5. Check that processing finishes, the output video opens, and faces/license plates in the output are pixelated adequately. Do not upload the source or output video to the issue.
6. If convenient, record processing FPS or elapsed time. Performance is workload-dependent; one number is not a universal comparison.

The current benchmark log is written to `logs/benchmarks.jsonl` after a successful job. It can provide fields such as `processing_fps`, `total_time_s`, `frames`, `resolution`, `encoder`, settings, and runtime versions. **Review the record before sharing anything:** it can include the input filename, model path, platform details, and other environment information. Copy only the relevant fields into the report and redact private information; do not attach the raw log by default.

## Submit a report

Use the [Hardware compatibility report form](https://github.com/mir4play/BlurGPT/issues/new?template=hardware_compatibility.yml). Reports are voluntary. Include the error text, if any, only after removing usernames, private paths, tokens, and other sensitive information.

For a general question or discussion, use GitHub Discussions if enabled for the repository; otherwise open a regular issue and explain that it is a question rather than a confirmed defect.

## Scope and expectations

- No automatic telemetry is added by this feedback process.
- The maintainer is not expected to personally benchmark every alternative backend or slower configuration.
- CPU, AMD/ROCm, Intel/XPU, and other combinations remain subject to the current implementation, supported dependencies, operating system, and available validation.
- Inference acceleration and video encoding are separate capabilities. For example, a working GPU inference backend does not imply that FFmpeg `h264_nvenc` is available.
- Community feedback helps prioritize future work, but it does not by itself change the default backend or prove that a configuration is officially supported.
- Preserve the current NVIDIA/CUDA + NVENC reference path. Alternative dependencies and packaging should remain isolated when combining them would add risk or unnecessary size.

See [the roadmap](roadmap.md), [performance methodology](performance.md), and [hardware portability issue #61](https://github.com/mir4play/BlurGPT/issues/61).
