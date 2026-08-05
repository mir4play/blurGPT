"""
==========================================================
BlurGPT - Configurações
==========================================================
Altere apenas este arquivo para configurar o programa.
"""

#==========================================================
# PROJECT 
APP_NAME = "BlurGPT"
VERSION = "0.4.0"
AUTHOR = "Adler Nicolau"
#==========================================================

# ==========================================================
# VÍDEOS
# ==========================================================

# Vídeo de entrada
# INPUT_VIDEO = "input/5.mp4" # deprecated on v0.3.1

# Vídeo de saída
# OUTPUT_VIDEO = "output/5.mp4" # deprecated on v0.3.1

# ==========================================================
# MODELOS
# ==========================================================

# Unique model path
MODEL_PATH = "models/blurGPT.pt"


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
DETECT_EVERY = 5
IMGSZ = 960

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