import sys
from types import SimpleNamespace
from unittest.mock import Mock

# The release tests exercise process/pipe cleanup only; no OpenCV runtime is
# needed. Keep the real module when OpenCV is installed, otherwise stub its
# import-time dependency for this focused unit test.
sys.modules.setdefault("cv2", SimpleNamespace(destroyAllWindows=lambda: None))

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
