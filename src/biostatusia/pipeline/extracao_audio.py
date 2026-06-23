"""
Extrator F2 — Biomarcadores de Áudio Biomédico.
Features: MFCCs, espectro mel, ZCR, RMS, energia por banda.
"""
import numpy as np


def extrair_biomarcadores_audio(sinal) -> dict | None:
    """Recebe SinalNormalizado (F2) e retorna dict de biomarcadores."""
    try:
        import librosa
    except ImportError:
        return {"erro": "librosa não instalado — execute: uv add librosa"}

    try:
        y = sinal.dados[0].astype(np.float32)
        fs = float(sinal.taxa_amostragem)

        bio = {
            "mfcc": _extrair_mfcc(y, fs, librosa),
            "espectral": _extrair_espectral(y, fs, librosa),
            "temporal_audio": _extrair_temporal_audio(y, fs, librosa),
            "energia_bandas": _extrair_energia_bandas(y, fs),
        }
        return bio
    except Exception as e:
        return {"erro": str(e)}


def _extrair_mfcc(y: np.ndarray, fs: float, librosa) -> dict:
    mfccs = librosa.feature.mfcc(y=y, sr=fs, n_mfcc=20)
    delta = librosa.feature.delta(mfccs)
    return {
        "mfcc_media": [round(float(v), 4) for v in mfccs.mean(axis=1)],
        "mfcc_desvio": [round(float(v), 4) for v in mfccs.std(axis=1)],
        "delta_mfcc_media": [round(float(v), 4) for v in delta.mean(axis=1)],
    }


def _extrair_espectral(y: np.ndarray, fs: float, librosa) -> dict:
    centroide = librosa.feature.spectral_centroid(y=y, sr=fs)[0]
    largura = librosa.feature.spectral_bandwidth(y=y, sr=fs)[0]
    rolloff = librosa.feature.spectral_rolloff(y=y, sr=fs)[0]
    chroma = librosa.feature.chroma_stft(y=y, sr=fs)
    flatness = librosa.feature.spectral_flatness(y=y)[0]
    contrast = librosa.feature.spectral_contrast(y=y, sr=fs)

    return {
        "centroide_hz_media": round(float(centroide.mean()), 2),
        "centroide_hz_desvio": round(float(centroide.std()), 2),
        "largura_espectral_hz": round(float(largura.mean()), 2),
        "rolloff_hz": round(float(rolloff.mean()), 2),
        "chroma_media": [round(float(v), 4) for v in chroma.mean(axis=1)],
        "flatness_media": round(float(flatness.mean()), 6),
        "contraste_espectral_media": [round(float(v), 4) for v in contrast.mean(axis=1)],
    }


def _extrair_temporal_audio(y: np.ndarray, fs: float, librosa) -> dict:
    zcr = librosa.feature.zero_crossing_rate(y)[0]
    rms = librosa.feature.rms(y=y)[0]
    return {
        "zcr_media": round(float(zcr.mean()), 6),
        "zcr_desvio": round(float(zcr.std()), 6),
        "rms_media": round(float(rms.mean()), 6),
        "rms_max": round(float(rms.max()), 6),
        "duracao_s": round(float(len(y) / fs), 3),
    }


def _extrair_energia_bandas(y: np.ndarray, fs: float) -> dict:
    from scipy import signal as sig_

    bandas = {
        "sub_20hz":   (1, 20),
        "baixa_20_200hz": (20, 200),
        "media_200_1k":  (200, 1000),
        "alta_1k_2k":    (1000, 2000),
        "muito_alta_2k": (2000, min(int(fs / 2) - 1, 8000)),
    }
    resultado = {}
    freqs, psd = sig_.welch(y, fs=fs, nperseg=min(1024, len(y) // 4))
    pot_total = float(np.trapz(psd, freqs)) + 1e-12

    for nome, (f1, f2) in bandas.items():
        if f2 > fs / 2:
            f2 = fs / 2 - 1
        if f1 >= f2:
            resultado[nome] = 0.0
            continue
        mask = (freqs >= f1) & (freqs < f2)
        pot = float(np.trapz(psd[mask], freqs[mask])) if mask.any() else 0.0
        resultado[nome] = round(pot / pot_total, 6)

    return resultado


def extrair_lote_audio(arquivos: list[dict]) -> list[dict]:
    """Processa lista de arquivos de áudio e retorna registros com biomarcadores."""
    from biostatusia.pipeline.io_sinais import carregar_sinal

    resultados = []
    for arq in arquivos:
        try:
            sinal = carregar_sinal(arq["caminho"])
            bio = extrair_biomarcadores_audio(sinal)
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
