"""
Leitor F5 — Vídeo Médico.
Suporta: .mp4, .avi, .mov via OpenCV (já disponível no projeto).
Extrai frames com estratégia adaptativa baseada no modo de uso.
"""
from pathlib import Path

import cv2
import numpy as np


def ler_video_medico(path: Path, max_frames: int = 300) -> "SinalNormalizado":
    """
    Lê vídeo e extrai frames representativos.
    max_frames: limite de frames extraídos (evita sobrecarga de memória).
    """
    from biostatusia.pipeline.io_sinais import SinalNormalizado

    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise ValueError(f"OpenCV não conseguiu abrir '{path.name}'")

    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    largura = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    altura = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # Estratégia de amostragem: 1 frame por segundo ou todos se poucos
    passo = max(1, total_frames // max_frames)
    frames_extraidos: list[np.ndarray] = []
    idx = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if idx % passo == 0:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.resize(gray, (256, 256))
            frames_extraidos.append(gray.astype(np.float32) / 255.0)
        idx += 1

    cap.release()

    if not frames_extraidos:
        raise ValueError(f"Nenhum frame extraído de '{path.name}'")

    volume = np.stack(frames_extraidos, axis=0)  # (n_frames, H, W)
    duracao_s = total_frames / fps

    return SinalNormalizado(
        familia="F5",
        tipo=_inferir_tipo_video(path.name),
        dados=volume,
        taxa_amostragem=fps,
        canais=["grayscale"],
        metadados={
            "total_frames": total_frames,
            "fps": round(fps, 2),
            "duracao_s": round(duracao_s, 2),
            "resolucao": [largura, altura],
            "frames_amostrados": len(frames_extraidos),
            "passo_amostragem": passo,
        },
        caminho_original=str(path),
        dados_viz=[],
    )


def extrair_frame(path: Path, frame_idx: int) -> np.ndarray:
    """Extrai um frame específico (grayscale float32 [0,1])."""
    cap = cv2.VideoCapture(str(path))
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
    ret, frame = cap.read()
    cap.release()
    if not ret:
        raise ValueError(f"Frame {frame_idx} não encontrado em '{path.name}'")
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0
    return gray


def frame_para_png_base64(frame: np.ndarray) -> str:
    """Converte frame (float32 [0,1]) para base64 PNG."""
    import base64
    import io

    from PIL import Image

    img = Image.fromarray((frame * 255).astype(np.uint8), mode="L")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def _inferir_tipo_video(nome: str) -> str:
    nome = nome.lower()
    if any(k in nome for k in ("endoscop", "colon", "gastro", "polyp")):
        return "Endoscopia"
    if any(k in nome for k in ("echo", "cardio", "ultrasound", "us_", "eco")):
        return "Ultrassom Dinâmico"
    return "Vídeo Médico"
