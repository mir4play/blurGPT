import sys
from types import SimpleNamespace
from unittest.mock import Mock

# The release tests exercise process/pipe cleanup only; no OpenCV runtime is
# needed. Keep the real module when OpenCV is installed, otherwise stub its
# import-time dependency for this focused unit test.
sys.modules.setdefault("cv2", SimpleNamespace(destroyAllWindows=lambda: None))

import core.video as video_module
from core.video import VideoProcessor


def make_processor(*, close_side_effect=None, return_code=1, stderr=b"encoder stopped"):
    processor = VideoProcessor.__new__(VideoProcessor)
    processor._released = False
    processor.cap = Mock()
    processor.writer = None
    processor.ffmpeg = SimpleNamespace(
        stdin=Mock(),
        wait=Mock(return_value=return_code),
        stderr=Mock(),
    )
    processor.ffmpeg.stdin.close.side_effect = close_side_effect
    processor.ffmpeg.stderr.read.return_value = stderr
    return processor


def test_cancelled_release_ignores_pipe_and_encoder_shutdown_errors():
    processor = make_processor(close_side_effect=BrokenPipeError("pipe closed"))

    processor.release(ignore_encoder_error=True)

    processor.cap.release.assert_called_once()
    processor.ffmpeg.stdin.close.assert_called_once()
    processor.ffmpeg.wait.assert_called_once()
    processor.ffmpeg.stderr.read.assert_called_once()
    assert processor._released is True


def test_cancelled_release_still_reaps_ffmpeg_when_stdin_close_raises_oserror():
    processor = make_processor(close_side_effect=OSError("pipe unavailable"))

    processor.release(ignore_encoder_error=True)

    processor.ffmpeg.wait.assert_called_once()
    assert processor._released is True


def test_normal_release_reports_nonzero_ffmpeg_exit():
    processor = make_processor(return_code=1, stderr=b"nvenc initialization failed")

    try:
        processor.release()
    except RuntimeError as error:
        assert "FFmpeg/NVENC exited with code 1" in str(error)
        assert "nvenc initialization failed" in str(error)
    else:
        raise AssertionError("A non-zero FFmpeg exit must be reported")

    processor.ffmpeg.wait.assert_called_once()
    assert processor._released is True


def test_nvenc_writer_hides_console_on_windows(monkeypatch, tmp_path):
    processor = VideoProcessor.__new__(VideoProcessor)
    processor.output_video = str(tmp_path / "output.mp4")
    processor.nvenc_preset = "p4"
    processor.nvenc_cq = 23
    processor.width = 1920
    processor.height = 1080
    processor.fps = 29.97
    processor.cap = Mock()

    calls = []
    no_window_flag = 0x08000000

    monkeypatch.setattr(
        video_module,
        "resolve_ffmpeg",
        lambda: tmp_path / "ffmpeg.exe",
    )
    monkeypatch.setattr(video_module.sys, "platform", "win32")
    monkeypatch.setattr(
        video_module.subprocess,
        "CREATE_NO_WINDOW",
        no_window_flag,
        raising=False,
    )

    def fake_popen(command, **kwargs):
        calls.append((command, kwargs))
        return Mock()

    monkeypatch.setattr(video_module.subprocess, "Popen", fake_popen)

    processor._create_nvenc_writer()

    assert calls[0][0][0] == str(tmp_path / "ffmpeg.exe")
    assert calls[0][1]["creationflags"] == no_window_flag
    assert calls[0][1]["stdin"] == video_module.subprocess.PIPE
    assert calls[0][1]["stdout"] == video_module.subprocess.DEVNULL
    assert calls[0][1]["stderr"] == video_module.subprocess.PIPE
    assert processor.write_backend == "ffmpeg:h264_nvenc"


