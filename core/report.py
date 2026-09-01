import time


class Stats:
    """Store processing statistics."""

    def __init__(self):
        self.start_time = time.perf_counter()
        self.frames = 0
        self.tempo_yolo = 0.0
        self.tempo_pixel = 0.0
        self.tempo_write = 0.0
        self._finalized = False
        self._total_time = 0.0

    def frame_processed(self):
        """Increment the processed frame counter."""
        self.frames += 1

    def finalize(self):
        """Freeze final timing values for consistent reporting."""
        if not self._finalized:
            self._total_time = time.perf_counter() - self.start_time
            self._finalized = True

    @property
    def total_time(self):
        """Return the final processing time."""
        if not self._finalized:
            return time.perf_counter() - self.start_time
        return self._total_time

    @property
    def fps(self):
        """Return average processing FPS."""
        total = self.total_time
        if total == 0:
            return 0
        return self.frames / total


def print_report(stats, video):
    """Print the final processing report."""
    stats.finalize()
    print()
    print("========== BlurGPT ==========")
    print(f"Frames..............: {stats.frames}")
    print(f"Tempo...............: {stats.total_time:.2f} s")
    print(f"FPS médio...........: {stats.fps:.2f}")
    print(f"Resolução...........: {video.width}x{video.height}")
    print(f"FPS do vídeo........: {video.fps:.2f}")
    print(f"Encoder.............: {video.write_backend}")
    print(f"Tempo YOLO..........: {stats.tempo_yolo:.2f}s")
    print(f"Tempo Pixel.........: {stats.tempo_pixel:.2f}s")
    print(f"Tempo Gravação......: {stats.tempo_write:.2f}s")
    print("============================")