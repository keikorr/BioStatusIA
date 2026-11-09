import cv2
import numpy as np
from io import BytesIO

from skimage.feature import graycomatrix, graycoprops
from scipy.stats import skew, kurtosis


def extrair_morfologia(gray_u8: np.ndarray) -> dict:
    thresh = cv2.adaptiveThreshold(
        gray_u8, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 11, 2,
    )
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return {"circularidade": 0.0, "solidez": 0.0}
    cnt = max(contours, key=cv2.contourArea)
    area = cv2.contourArea(cnt)
    perimeter = cv2.arcLength(cnt, True)
    circularidade = (4 * np.pi * area) / (perimeter ** 2) if perimeter > 0 else 0.0
    hull_area = cv2.contourArea(cv2.convexHull(cnt))
    solidez = area / hull_area if hull_area > 0 else 0.0
    return {
        "circularidade": round(float(circularidade), 4),
        "solidez": round(float(solidez), 4),
    }


def extrair_intensidade(img: np.ndarray) -> dict:
    flat = img.flatten()
    mean = np.mean(flat)
    std = np.std(flat)
    return {
        "snr": round(float(mean / (std + 1e-8)), 4),
        "assimetria": round(float(skew(flat)), 4),
        "curtose": round(float(kurtosis(flat)), 4),
    }


ANGULOS_GLCM = [0, np.pi / 4, np.pi / 2, 3 * np.pi / 4]


def extrair_glcm(gray_u8: np.ndarray) -> dict:
    """Textura de Haralick a partir da GLCM (distância 1, média dos ângulos
    0/45/90/135 graus, 256 níveis). A entropia é a da própria GLCM; a
    entropia de primeira ordem (histograma) fica em `entropia_histograma`."""
    glcm = graycomatrix(gray_u8, [1], ANGULOS_GLCM, 256, symmetric=True, normed=True)
    p = glcm[:, :, 0, :]
    entropia_glcm = float(np.mean([-np.sum(p[:, :, a][p[:, :, a] > 0] * np.log2(p[:, :, a][p[:, :, a] > 0]))
                                   for a in range(p.shape[2])]))
    hist = cv2.calcHist([gray_u8], [0], None, [256], [0, 256]).ravel()
    ph = hist / (hist.sum() + 1e-10)
    entropia_hist = float(-np.sum(ph[ph > 0] * np.log2(ph[ph > 0])))
    return {
        "contraste": round(float(graycoprops(glcm, "contrast").mean()), 4),
        "homogeneidade": round(float(graycoprops(glcm, "homogeneity").mean()), 4),
        "energia": round(float(graycoprops(glcm, "energy").mean()), 4),
        "entropia": round(entropia_glcm, 4),
        "entropia_histograma": round(entropia_hist, 4) + 0.0,
    }


def extrair_todos(caminho: str, estrategia: dict | None = None) -> dict | None:
    """Extrai biomarcadores. Se `estrategia` for fornecida, aplica pré-processamento adaptativo."""
    if estrategia is not None:
        from biostatusia.pipeline.preprocessamento import preprocessar_adaptativo
        arr_norm = preprocessar_adaptativo(caminho, estrategia)
        if arr_norm is None:
            return None
        gray = (arr_norm * 255).astype(np.uint8)
        return {
            "morfologia": extrair_morfologia(gray),
            "textura_glcm": extrair_glcm(gray),
            "distribuicao_intensidade": extrair_intensidade(arr_norm),
        }

    try:
        if caminho.startswith("http"):
            import requests
            response = requests.get(caminho, headers={"User-Agent": "Mozilla/5.0"})
            from PIL import Image
            img_pil = Image.open(BytesIO(response.content)).convert("RGB")
        else:
            from PIL import Image
            img_pil = Image.open(caminho).convert("RGB")
    except Exception:
        return None

    arr = np.array(img_pil).astype(np.float32)
    arr = (arr - arr.min()) / (arr.max() - arr.min() + 1e-8)

    img_u8 = (arr * 255).astype(np.uint8)
    gray = cv2.cvtColor(img_u8, cv2.COLOR_RGB2GRAY)

    return {
        "morfologia": extrair_morfologia(gray),
        "textura_glcm": extrair_glcm(gray),
        "distribuicao_intensidade": extrair_intensidade(arr),
    }
