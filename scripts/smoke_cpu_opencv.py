"""Run a real CPU + OpenCV batch-processing smoke test on Windows CI."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import sys

import numpy as np
import torch

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

import cv2

import core.benchmark as benchmark_module
import core.jobmanager as jobmanager_module
import core.settings as settings_module
from core.jobmanager import JobManager
from core.preflight import validate_processing_environment
from core.processor import BatchProcessor


def _configure_isolated_runtime(root: Path) -> None:
    """Redirect every runtime write into a temporary directory."""
    directories = {
        "ARCHIVE_DIR": root / "input_archive",
        "ERROR_DIR": root / "input_error",
        "INPUT_DIR": root / "input",
        "LOGS_DIR": root / "logs",
        "OUTPUT_DIR": root / "output",
        "PROCESSING_DIR": root / "processing",
        "REMOVED_DIR": root / "input_removed",
        "TEMP_DIR": root / "temp",
        "CONFIG_DIR": root / "config",
    }
    for name, path in directories.items():
        setattr(jobmanager_module, name, path)

    settings_module.SETTINGS_DIR = directories["CONFIG_DIR"]
    settings_module.SETTINGS_PATH = directories["CONFIG_DIR"] / "settings.json"
    benchmark_module.LOG_PATH = directories["LOGS_DIR"] / "benchmarks.jsonl"


def _create_input_video(path: Path, frame_count: int = 4) -> None:
    width, height, fps = 320, 240, 12.0
    writer = cv2.VideoWriter(
        str(path),
        cv2.VideoWriter_fourcc(*"mp4v"),
        fps,
        (width, height),
    )
    if not writer.isOpened():
        raise RuntimeError("OpenCV could not create the synthetic mp4v input clip")

    try:
        for index in range(frame_count):
            frame = np.zeros((height, width, 3), dtype=np.uint8)
            cv2.rectangle(
                frame,
                (30 + index * 3, 35),
                (150 + index * 3, 190),
                (220, 220, 220),
                thickness=-1,
            )
            cv2.circle(frame, (235, 115), 35, (80, 180, 240), thickness=-1)
            writer.write(frame)
    finally:
        writer.release()


def _count_decoded_frames(path: Path) -> tuple[int, tuple[int, int], float]:
    capture = cv2.VideoCapture(str(path))
    if not capture.isOpened():
        raise RuntimeError(f"OpenCV could not reopen processed output: {path}")

    count = 0
    dimensions = (0, 0)
    try:
        while True:
            ok, frame = capture.read()
            if not ok:
                break
            count += 1
            dimensions = (int(frame.shape[1]), int(frame.shape[0]))
        fps = float(capture.get(cv2.CAP_PROP_FPS))
    finally:
        capture.release()

    return count, dimensions, fps


def main() -> None:
    torch.set_num_threads(2)
    model_path = ROOT_DIR / "models" / "blurGPT.pt"
    if not model_path.is_file():
        raise FileNotFoundError(f"Required repository model is missing: {model_path}")

    with tempfile.TemporaryDirectory(prefix="blurgpt-cpu-opencv-") as temp_dir:
        runtime_root = Path(temp_dir)
        _configure_isolated_runtime(runtime_root)

        settings = settings_module.DEFAULTS.copy()
        settings.update(
            {
                "model_path": str(model_path),
                "device": "cpu",
                "detect_every": 1,
                "imgsz": 640,
                "video_encoder": "opencv",
                "video_codec": "mp4v",
            }
        )
        settings_module.save_settings(settings)

        preflight_errors = validate_processing_environment(settings)
        if preflight_errors:
            raise RuntimeError(
                "CPU + OpenCV preflight failed:\n- "
                + "\n- ".join(preflight_errors)
            )

        manager = JobManager()
        input_video = manager.input_dir / "cpu-opencv-smoke.mp4"
        _create_input_video(input_video)

        processor = BatchProcessor(manager)
        summary = processor.run()
        if summary != {"succeeded": 1, "failed": 0, "cancelled": False}:
            raise RuntimeError(f"CPU + OpenCV batch did not succeed: {summary}")

        output_video = manager.output_dir / input_video.name
        archived_input = manager.archive_dir / input_video.name
        if not output_video.is_file() or output_video.stat().st_size == 0:
            raise RuntimeError("The processed output video is missing or empty")
        if not archived_input.is_file():
            raise RuntimeError("The original input was not archived after processing")

        decoded_frames, dimensions, output_fps = _count_decoded_frames(output_video)
        if decoded_frames != 4:
            raise RuntimeError(
                f"Expected 4 decoded output frames, found {decoded_frames}"
            )
        if dimensions != (320, 240) or abs(output_fps - 12.0) > 0.5:
            raise RuntimeError(
                f"Unexpected output metadata: {dimensions} at {output_fps:.3f} FPS"
            )

        benchmark_path = manager.logs_dir / "benchmarks.jsonl"
        records = [
            json.loads(line)
            for line in benchmark_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        if not records:
            raise RuntimeError("The successful CPU run did not write a benchmark record")

        record = records[-1]
        if record["device"] != "cpu":
            raise RuntimeError(f"Benchmark recorded an unexpected device: {record['device']}")
        if record["encoder"] != "opencv:mp4v":
            raise RuntimeError(
                f"Benchmark recorded an unexpected encoder: {record['encoder']}"
            )
        if record["environment"]["selected_inference_backend"] != "CPU":
            raise RuntimeError("Benchmark did not identify CPU as the inference backend")

        print(
            "CPU + OpenCV runtime smoke passed: "
            f"{decoded_frames} frames, {dimensions[0]}x{dimensions[1]} "
            f"at {output_fps:.2f} FPS; "
            f"encoder={record['encoder']}; "
            f"processing_fps={record['processing_fps']:.2f}"
        )


if __name__ == "__main__":
    main()
