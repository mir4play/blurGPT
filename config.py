"""
==========================================================
BlurGPT - Configurações
==========================================================
Altere apenas este arquivo para configurar o programa.
"""

#==========================================================
# PROJECT 
APP_NAME = "BlurGPT"
VERSION = "0.2.0"
AUTHOR = "Adler Nicolau"
#==========================================================

# ==========================================================
# VÍDEOS
# ==========================================================

# Vídeo de entrada
INPUT_VIDEO = "input/5.mp4" # obssolete, will be removed in the next version

# Vídeo de saída
OUTPUT_VIDEO = "output/5.mp4" # obssolete, will be removed in the next version

# ==========================================================
# MODELOS
# ==========================================================

# Modelo principal (faces) Yolo26s
FACE_MODEL = "models/yolo26s.pt"

# Modelo de placas YOLOv8
PLATE_MODEL = "models/platesYOLOv8.pt"

# ==========================================================
# DISPOSITIVO
# ==========================================================

# 0 = primeira GPU CUDA
# "cpu" = processador
DEVICE = 0

# ==========================================================
# CLASSES
# ==========================================================

# Classes treinadas
CLASSES = {
    "face": 1,
    "plate": 0
}

# ==========================================================
# DETECÇÃO
# ==========================================================

# Detecta a cada N frames
# 1 = todos os frames
# 2 = metade dos frames
# 3 = um a cada três
FACE_DETECT_EVERY = 8
PLATE_DETECT_EVERY = 5
FACE_IMGSZ = 640
PLATE_IMGSZ = 1280

# ==========================================================
# PIXELIZAÇÃO
# ==========================================================

# Quanto maior, mais pixelado
PIXEL_SIZE = 10

# Margem adicionada ao redor da caixa
BOX_MARGIN = 0

# ==========================================================
# VÍDEO
# ==========================================================

# Codec do OpenCV
VIDEO_CODEC = "mp4v"

# Mostrar vídeo durante processamento
SHOW_VIDEO = False

# Salvar vídeo
SAVE_VIDEO = True

# ==========================================================
# RELATÓRIO
# ==========================================================

SHOW_REPORT = True