import shutil
import subprocess
import time

import cv2


class VideoProcessor:

    def __init__(
        self,
        input_video,
        output_video,
        codec="mp4v",
        encoder="opencv",
        nvenc_cq=23,
        nvenc_preset="p4"
    ):

        self.input_video = input_video
        self.output_video = output_video
        self.codec = codec
        self.encoder = encoder
        self.nvenc_cq = nvenc_cq
        self.nvenc_preset = nvenc_preset
        self.writer = None
        self.ffmpeg = None
        self.write_backend = "opencv"

        self.cap = cv2.VideoCapture(input_video)

        if not self.cap.isOpened():
            raise Exception(f"Erro ao abrir vídeo: {input_video}")

        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))

        if self.fps <= 0:
            raise Exception("Não foi possível determinar o FPS do vídeo.")

        if encoder == "h264_nvenc":
            self._create_nvenc_writer()
        else:
            self._create_opencv_writer(codec)

    def _create_opencv_writer(self, codec):
        """Create the legacy OpenCV software writer."""
        fourcc = cv2.VideoWriter_fourcc(*codec)

        self.writer = cv2.VideoWriter(
            self.output_video,
            fourcc,
            self.fps,
            (self.width, self.height)
        )

        if not self.writer.isOpened():
            raise Exception(
                f"Não foi possível abrir o VideoWriter com codec '{codec}'."
            )

        self.write_backend = f"opencv:{codec}"

    def _create_nvenc_writer(self):
        """Create an FFmpeg pipe using NVIDIA hardware H.264 encoding."""
        ffmpeg_path = shutil.which("ffmpeg")

        if ffmpeg_path is None:
            raise RuntimeError(
                "FFmpeg não encontrado. Instale o FFmpeg e coloque-o no PATH "
                "ou use VIDEO_ENCODER='opencv'."
            )

        command = [
            ffmpeg_path,
            "-hide_banner",
            "-loglevel", "error",
            "-f", "rawvideo",
            "-pix_fmt", "bgr24",
            "-s", f"{self.width}x{self.height}",
            "-r", str(self.fps),
            "-i", "-",
            "-an",
            "-c:v", "h264_nvenc",
            "-preset", self.nvenc_preset,
            "-cq", str(self.nvenc_cq),
            "-pix_fmt", "yuv420p",
            "-y",
            self.output_video,
        ]

        self.ffmpeg = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            bufsize=0,
        )

        self.write_backend = "ffmpeg:h264_nvenc"

    def read(self):
        """Lê um frame do vídeo."""
        return self.cap.read()

    def write(self, frame, stats=None):
        """Escreve um frame no vídeo de saída."""
        t0 = time.perf_counter()

        if self.ffmpeg is not None:
            try:
                self.ffmpeg.stdin.write(frame.tobytes())
            except (BrokenPipeError, OSError) as exc:
                error = self.ffmpeg.stderr.read().decode(
                    "utf-8", errors="replace"
                )
                raise RuntimeError(
                    f"FFmpeg/NVENC falhou durante a gravação: {error.strip()}"
                ) from exc
        else:
            self.writer.write(frame)

        if stats is not None:
            stats.tempo_write += time.perf_counter() - t0

    def release(self):
        """Libera recursos e finaliza o encoder."""
        self.cap.release()

        if self.ffmpeg is not None:
            if self.ffmpeg.stdin is not None:
                self.ffmpeg.stdin.close()

            return_code = self.ffmpeg.wait()
            error = self.ffmpeg.stderr.read().decode(
                "utf-8", errors="replace"
            )

            if return_code != 0:
                raise RuntimeError(
                    f"FFmpeg/NVENC terminou com código {return_code}: "
                    f"{error.strip()}"
                )
        elif self.writer is not None:
            self.writer.release()

        cv2.destroyAllWindows()