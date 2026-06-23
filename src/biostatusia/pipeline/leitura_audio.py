"""
Leitor F2 — Áudio Biomédico.
Suporta: .wav, .flac (via soundfile), .mp3 (via librosa), .mat (via scipy).
"""
from pathlib import Path

import numpy as np


def ler_audio_biomedico(path: Path) -> "SinalNormalizado":
    from biostatusia.pipeline.io_sinais import SinalNormalizado, _downsample_para_viz

    ext = path.suffix.lower()

    if ext in {".wav", ".flac"}:
        dados, fs = _ler_soundfile(path)
    elif ext == ".mp3":
        dados, fs = _ler_librosa(path)
    elif ext == ".mat":
        dados, fs = _ler_mat_audio(path)
    else:
        raise ValueError(f"Extensão de áudio não suportada: {ext}")

    # Normalização peak para [-1, 1]
    peak = np.abs(dados).max()
    if peak > 0:
        dados = dados / peak

    return SinalNormalizado(
        familia="F2",
        tipo=_inferir_tipo(path.name),
        dados=dados,
        taxa_amostragem=float(fs),
        canais=["mono"],
        metadados={
            "duracao_s": round(dados.shape[1] / fs, 2),
            "n_amostras": dados.shape[1],
            "taxa_amostragem_hz": float(fs),
        },
        caminho_original=str(path),
        dados_viz=_downsample_para_viz(dados),
    )


def _ler_soundfile(path: Path):
    try:
        import soundfile as sf
    except ImportError:
        raise ImportError("Instale soundfile: uv add soundfile")
    data, fs = sf.read(str(path), dtype="float32", always_2d=False)
    if data.ndim == 2:
        data = data.mean(axis=1)  # estéreo → mono
    return data[np.newaxis, :].astype(np.float32), fs


def _ler_librosa(path: Path):
    try:
        import librosa
    except ImportError:
        raise ImportError("Instale librosa: uv add librosa")
    data, fs = librosa.load(str(path), sr=None, mono=True)
    return data[np.newaxis, :].astype(np.float32), fs


def _ler_mat_audio(path: Path):
    from scipy.io import loadmat

    mat = loadmat(str(path))
    candidatos = {
        k: v for k, v in mat.items()
        if not k.startswith("__") and isinstance(v, np.ndarray) and v.ndim >= 1
    }
    if not candidatos:
        raise ValueError(f"Nenhum array de áudio em '{path.name}'")

    chave = max(candidatos, key=lambda k: candidatos[k].size)
    arr = candidatos[chave].astype(np.float32).flatten()

    fs = 44100.0
    for k in ("fs", "Fs", "fs_audio", "sample_rate"):
        if k in mat:
            try:
                fs = float(mat[k].flat[0])
                break
            except Exception:
                pass

    return arr[np.newaxis, :], fs


def _inferir_tipo(nome_arquivo: str) -> str:
    nome = nome_arquivo.lower()
    if any(k in nome for k in ("heart", "cardiac", "pcg", "fono", "s1", "s2")):
        return "Fonocardiograma"
    if any(k in nome for k in ("lung", "pulm", "breath", "wheeze", "crackle", "respir")):
        return "Sons Pulmonares"
    return "Áudio Biomédico"
