# BlurGPT

Ferramenta para anonimização automática de vídeos utilizando YOLO.

# Instalação

## 1. Criar ambiente virtual

```bash
python -m venv .venv
```

## 2. Ativar

Windows

```bash
.venv\Scripts\activate
```

## 3. Instalar PyTorch com CUDA

Para GPUs NVIDIA com CUDA:

```bash
python -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cu132
```

## 4. Instalar as demais dependências

```bash
pip install -r requirements.txt
```

## 5. Executar

```bash
python blurGPT.py
```

## Recursos

- Detecção de rostos

- Pixelização

- CUDA

- Processamento em tempo real

- Barra de progresso

- Arquitetura modular

## Estrutura

core/

models/

input/

output/

## Requisitos

Python 3.12

pip install -r requirements.txt

## Executar

python [blurGPT.py](http://blurGPT.py)