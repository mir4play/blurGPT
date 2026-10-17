from pathlib import Path

import core.jobmanager as jobmanager_module
from core.jobmanager import Job, JobManager


def make_manager(tmp_path, monkeypatch):
    folders = {
        "INPUT_DIR": tmp_path / "input",
        "PROCESSING_DIR": tmp_path / "processing",
        "TEMP_DIR": tmp_path / "temp",
        "OUTPUT_DIR": tmp_path / "output",
        "ARCHIVE_DIR": tmp_path / "input_archive",
        "ERROR_DIR": tmp_path / "input_error",
        "REMOVED_DIR": tmp_path / "input_removed",
        "LOGS_DIR": tmp_path / "logs",
    }
    for name, path in folders.items():
        monkeypatch.setattr(jobmanager_module, name, path)
    return JobManager(), folders


def test_unique_input_path_preserves_existing_file(tmp_path, monkeypatch):
    manager, folders = make_manager(tmp_path, monkeypatch)
    (folders["INPUT_DIR"] / "trip.mp4").write_bytes(b"existing")

    candidate = manager.get_unique_input_path("trip.mp4")

    assert candidate == folders["INPUT_DIR"] / "trip_1.mp4"
    assert (folders["INPUT_DIR"] / "trip.mp4").read_bytes() == b"existing"


def test_cancel_returns_job_to_input_and_removes_partial_output(
    tmp_path, monkeypatch
):
    manager, folders = make_manager(tmp_path, monkeypatch)
    job = Job(filename="trip.mp4", source="input")
    source = folders["INPUT_DIR"] / job.filename
    source.write_bytes(b"original")
    manager.start(job)
    partial = manager.get_temp_output_path(job)
    partial.write_bytes(b"partial")

    manager.cancel(job)

    assert (folders["INPUT_DIR"] / "trip.mp4").read_bytes() == b"original"
    assert not (folders["PROCESSING_DIR"] / "trip.mp4").exists()
    assert not partial.exists()
    assert job.source == "input"


def test_finish_uses_unique_output_and_archive_names(tmp_path, monkeypatch):
    manager, folders = make_manager(tmp_path, monkeypatch)
    job = Job(filename="trip.mp4", source="processing")
    (folders["PROCESSING_DIR"] / job.filename).write_bytes(b"source")
    (folders["TEMP_DIR"] / job.filename).write_bytes(b"processed")
    (folders["OUTPUT_DIR"] / job.filename).write_bytes(b"old output")
    (folders["ARCHIVE_DIR"] / job.filename).write_bytes(b"old archive")

    manager.finish(job)

    assert (folders["OUTPUT_DIR"] / "trip_1.mp4").read_bytes() == b"processed"
    assert (folders["ARCHIVE_DIR"] / "trip_1.mp4").read_bytes() == b"source"
    assert (folders["OUTPUT_DIR"] / "trip.mp4").read_bytes() == b"old output"
    assert (folders["ARCHIVE_DIR"] / "trip.mp4").read_bytes() == b"old archive"


def test_fail_moves_input_to_error_removes_temp_and_logs(
    tmp_path, monkeypatch
):
    manager, folders = make_manager(tmp_path, monkeypatch)
    job = Job(filename="trip.mp4", source="processing")
    (folders["PROCESSING_DIR"] / job.filename).write_bytes(b"source")
    (folders["TEMP_DIR"] / job.filename).write_bytes(b"partial")

    manager.fail(job, RuntimeError("encoder failed"))

    assert (folders["ERROR_DIR"] / "trip.mp4").read_bytes() == b"source"
    assert not (folders["PROCESSING_DIR"] / "trip.mp4").exists()
    assert not (folders["TEMP_DIR"] / "trip.mp4").exists()
    log = (folders["LOGS_DIR"] / "errors.log").read_text(encoding="utf-8")
    assert "trip.mp4" in log
    assert "RuntimeError: encoder failed" in log


def test_remove_from_queue_moves_file_without_deleting_it(
    tmp_path, monkeypatch
):
    manager, folders = make_manager(tmp_path, monkeypatch)
    source = folders["INPUT_DIR"] / "trip.mp4"
    source.write_bytes(b"original")

    assert manager.remove_from_queue("trip.mp4") is True
    assert not source.exists()
    assert (folders["REMOVED_DIR"] / "trip.mp4").read_bytes() == b"original"
    assert manager.remove_from_queue("trip.mp4") is False
