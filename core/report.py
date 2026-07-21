import time


class Stats:
    """
    Armazena todas as estatísticas do processamento.
    """

    def __init__(self):

        # Tempo de início
        self.start_time = time.time()

        # Quantidade de frames processados
        self.frames = 0

        # Tempos parciais
        self.tempo_yolo = 0.0
        self.tempo_pixel = 0.0
        self.tempo_write = 0.0

    def frame_processed(self):
        """
        Incrementa o contador de frames.
        """
        self.frames += 1

    @property
    def total_time(self):
        """
        Tempo total do processamento.
        """
        return time.time() - self.start_time

    @property
    def fps(self):
        """
        FPS médio do processamento.
        """
        if self.total_time == 0:
            return 0

        return self.frames / self.total_time


def print_report(stats, video):
    """
    Imprime o relatório final.
    """

    print()
    print("========== BlurGPT ==========")
    print(f"Frames..............: {stats.frames}")
    print(f"Tempo...............: {stats.total_time:.2f} s")
    print(f"FPS médio...........: {stats.fps:.2f}")
    print(f"Resolução...........: {video.width}x{video.height}")
    print(f"FPS do vídeo........: {video.fps:.2f}")
    print(f"Tempo YOLO..........: {stats.tempo_yolo:.2f}s")
    print(f"Tempo Pixel.........: {stats.tempo_pixel:.2f}s")
    print(f"Tempo Gravação......: {stats.tempo_write:.2f}s")
    print("============================")