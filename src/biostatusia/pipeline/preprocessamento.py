import cv2
import numpy as np
from skimage.restoration import denoise_nl_means


def preprocessar(caminho: str, tamanho: tuple[int, int] = (256, 256)) -> np.ndarray | None:
    """Pré-processamento padrão (compatibilidade com main.py)."""
    img = cv2.imread(caminho, cv2.IMREAD_GRAYSCALE)
    if img is None:
        return None
    redimensionada = cv2.resize(img, tamanho)
    suavizada = cv2.GaussianBlur(redimensionada, (5, 5), 0)
    normalizada = suavizada.astype(np.float32) / 255.0
    return normalizada


def preprocessar_adaptativo(caminho: str, estrategia: dict) -> np.ndarray | None:
    """Aplica a estratégia decidida por decidir_estrategia()."""
    img = cv2.imread(caminho, cv2.IMREAD_GRAYSCALE)
    if img is None:
        return None

    if estrategia.get("redimensionar", True):
        tamanho = tuple(estrategia.get("tamanho_alvo", [256, 256]))
        img = cv2.resize(img, tamanho)

    if estrategia.get("equalizacao") == "clahe":
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        img = clahe.apply(img)

    if estrategia.get("denoising") == "nlmeans":
        img_float = img.astype(np.float32) / 255.0
        img_float = denoise_nl_means(
            img_float, h=0.1, fast_mode=True, patch_size=5, patch_distance=6
        )
        img = (np.clip(img_float, 0, 1) * 255).astype(np.uint8)
    else:
        img = cv2.GaussianBlur(img, (5, 5), 0)

    if estrategia.get("normalizacao") == "percentil":
        p1, p99 = np.percentile(img, [1, 99])
        clipped = np.clip(img, p1, p99).astype(np.float32)
        normalizada = (clipped - p1) / ((p99 - p1) + 1e-8)
    else:
        normalizada = img.astype(np.float32) / 255.0

    return normalizada
