"""
==========================================================
BlurGPT - Configurações
==========================================================
Altere apenas este arquivo para configurar o programa.
"""

#==========================================================
# VERSION "0.1.0"
#==========================================================

# ==========================================================
# VÍDEOS
# ==========================================================

# Vídeo de entrada
INPUT_VIDEO = "input/1 minuto teste.mp4"

# Vídeo de saída
OUTPUT_VIDEO = "output/saida.mp4"

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
FACE_DETECT_EVERY = 2
PLATE_DETECT_EVERY = 2

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