"""
Extrator F5 — Biomarcadores de Vídeo Médico.
Features: variação temporal, motion index, textura de frames-chave.
"""
import numpy as np
import cv2
from skimage.feature import graycomatrix, graycoprops
from scipy.stats import skew, kurtosis


def extrair_biomarcadores_video(sinal) -> dict | None:
    """Recebe SinalNormalizado (F5) e retorna dict de biomarcadores."""
    try:
        frames = sinal.dados  # (n_frames, H, W) float32 [0,1]
        meta = sinal.metadados
        fps = sinal.taxa_amostragem

        bio = {
            "temporal_video": _features_temporais(frames, fps),
            "textura_keyframe": _features_textura_keyframe(frames),
            "movimento": _features_movimento(frames),
        }
        return bio
    except Exception as e:
        return {"erro": str(e)}


def _features_temporais(frames: np.ndarray, fps: float) -> dict:
    """Estatísticas globais ao longo do tempo."""
    medias = frames.mean(axis=(1, 2))
    desvios = frames.std(axis=(1, 2))
    return {
        "n_frames": len(frames),
        "fps": round(float(fps), 2),
        "intensidade_media_global": round(float(medias.mean()), 6),
        "intensidade_desvio_global": round(float(desvios.mean()), 6),
        "variacao_temporal": round(float(medias.std()), 6),
        "brilho_max_frame": round(float(medias.max()), 6),
        "brilho_min_frame": round(float(medias.min()), 6),
    }


def _features_movimento(frames: np.ndarray) -> dict:
    """Motion index: diferença média absoluta entre frames consecutivos."""
    if len(frames) < 2:
        return {"motion_index": 0.0, "max_motion_frame": -1}

    diferencas = np.abs(np.diff(frames.astype(np.float32), axis=0)).mean(axis=(1, 2))
    motion_index = float(diferencas.mean())
    max_idx = int(np.argmax(diferencas))

    # Percentil 90 de movimento (frames com mais mudança)
    p90 = float(np.percentile(diferencas, 90))

    return {
        "motion_index_medio": round(motion_index, 6),
        "motion_max_frame": max_idx,
        "motion_p90": round(p90, 6),
        "frames_alta_variacao_pct": round(float(np.mean(diferencas > p90)) * 100, 2),
    }


def _features_textura_keyframe(frames: np.ndarray) -> dict:
    """GLCM e estatísticas de textura do frame central (mais representativo)."""
    n = len(frames)
    # Frame com variância mais alta como keyframe
    variancias = np.array([frames[i].var() for i in range(n)])
    idx_key = int(np.argmax(variancias))
    frame = frames[idx_key]

    gray = (frame * 255).astype(np.uint8)
    glcm = graycomatrix(gray, [1], [0], 256, symmetric=True, normed=True)
    flat = frame.flatten()
    hist = gray.flatten()
    p = np.bincount(hist, minlength=256).astype(float)
    p /= p.sum() + 1e-10
    entropia = float(-np.sum(p * np.log2(p + 1e-10)))

    return {
        "keyframe_idx": idx_key,
        "contraste": round(float(graycoprops(glcm, "contrast")[0, 0]), 4),
        "homogeneidade": round(float(graycoprops(glcm, "homogeneity")[0, 0]), 4),
        "energia": round(float(graycoprops(glcm, "energy")[0, 0]), 4),
        "entropia": round(entropia, 4),
        "assimetria": round(float(skew(flat)), 4),
        "curtose": round(float(kurtosis(flat)), 4),
    }


def extrair_lote_video(arquivos: list[dict]) -> list[dict]:
    """Processa lista de vídeos e retorna registros com biomarcadores."""
    from biostatusia.pipeline.io_sinais import carregar_sinal

    resultados = []
    for arq in arquivos:
        try:
            sinal = carregar_sinal(arq["caminho"])
            bio = extrair_biomarcadores_video(sinal)
            if bio and "erro" not in bio:
                resultados.append({
                    "caminho": arq["caminho"],
                    "label": arq.get("label"),
                    "categoria": arq.get("categoria", "INDEFINIDO"),
                    "biomarcadores": bio,
                    "tipo": sinal.tipo,
                })
        except Exception as e:
            resultados.append({
                "caminho": arq["caminho"],
                "erro": str(e),
                "categoria": arq.get("categoria", "INDEFINIDO"),
            })
    return resultados
