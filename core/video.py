import time
import cv2


class VideoProcessor:

    def __init__(
        self,
        input_video,
        output_video,
        codec="mp4v"
    ):

        self.input_video = input_video
        self.output_video = output_video
        self.codec = codec

        # ---------------------------------
        # Abre o vídeo
        # ---------------------------------

        self.cap = cv2.VideoCapture(input_video)

        if not self.cap.isOpened():
            raise Exception(f"Erro ao abrir vídeo: {input_video}")

        # ---------------------------------
        # Informações do vídeo
        # ---------------------------------

        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))

        # ---------------------------------
        # Cria o writer
        # ---------------------------------

        fourcc = cv2.VideoWriter_fourcc(*codec)

        self.writer = cv2.VideoWriter(
            output_video,
            fourcc,
            self.fps,
            (self.width, self.height)
        )

    # ---------------------------------

    def read(self):
        """
        Lê um frame do vídeo.
        """
        return self.cap.read()

    # ---------------------------------

    def write(self, frame, stats=None):
        """
        Escreve um frame no vídeo de saída.
        """

        t0 = time.perf_counter()

        self.writer.write(frame)

        if stats is not None:
            stats.tempo_write += time.perf_counter() - t0

    # ---------------------------------

    def release(self):
        """
        Libera todos os recursos.
        """

        self.cap.release()
        self.writer.release()
        cv2.destroyAllWindows()