from datetime import datetime
from pathlib import Path

# ── Famílias existentes ────────────────────────────────────────────────────────
EXT_IMAGENS   = (".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff")
EXT_TABULARES = (".csv", ".txt", ".tsv")

# ── Novas famílias de sinais biomédicos ───────────────────────────────────────
EXT_SINAIS_TEMPORAIS = frozenset({
    ".edf", ".bdf", ".dat", ".hea", ".atr",
    ".mat", ".cnt", ".eeg", ".rec", ".c3d", ".set", ".xml",
})
EXT_AUDIO_BIOMEDICO = frozenset({".wav", ".mp3", ".flac"})
EXT_DICOM           = frozenset({".dcm"})
EXT_VIDEO           = frozenset({".mp4", ".avi", ".mov"})
# .nii.gz precisa de checagem dupla via Path.suffixes — veja eh_volumetrico()
EXT_VOLUMETRICO_SIMPLES = frozenset({".nii", ".mha"})

PASTAS_BENIGNAS = {"benign", "benigno", "normal", "negative", "0"}
PASTAS_MALIGNAS = {"malignant", "malign", "maligno", "abnormal", "positive", "1"}

RUNS_DIR = Path(__file__).parent.parent / "static" / "runs"


# ── Predicados por família ────────────────────────────────────────────────────

def eh_imagem(arquivo: Path) -> bool:
    return arquivo.suffix.lower() in EXT_IMAGENS and "mask" not in arquivo.name.lower()


def eh_tabular(arquivo: Path) -> bool:
    return arquivo.suffix.lower() in EXT_TABULARES


def eh_sinal_temporal(arquivo: Path) -> bool:
    return arquivo.suffix.lower() in EXT_SINAIS_TEMPORAIS


def eh_audio_biomedico(arquivo: Path) -> bool:
    return arquivo.suffix.lower() in EXT_AUDIO_BIOMEDICO


def eh_dicom(arquivo: Path) -> bool:
    return arquivo.suffix.lower() in EXT_DICOM


def eh_volumetrico(arquivo: Path) -> bool:
    ext = arquivo.suffix.lower()
    suffixes = [s.lower() for s in arquivo.suffixes]
    return ext in EXT_VOLUMETRICO_SIMPLES or suffixes == [".nii", ".gz"]


def eh_video(arquivo: Path) -> bool:
    return arquivo.suffix.lower() in EXT_VIDEO


def eh_sinal_novo(arquivo: Path) -> bool:
    """True para qualquer extensão das 5 novas famílias."""
    return (
        eh_sinal_temporal(arquivo)
        or eh_audio_biomedico(arquivo)
        or eh_dicom(arquivo)
        or eh_volumetrico(arquivo)
        or eh_video(arquivo)
    )


# ── Utilitários de rótulo e listagem ─────────────────────────────────────────

def label_pasta(nome_pasta: str) -> int | None:
    nome = nome_pasta.lower()
    if nome in PASTAS_BENIGNAS:
        return 0
    if nome in PASTAS_MALIGNAS:
        return 1
    return None


def listar_imagens(caminho: Path) -> list[dict]:
    """Lista imagens (famílias existentes). Detecta rótulo pelas pastas pai."""
    if caminho.is_file() and eh_imagem(caminho):
        return [{"caminho": str(caminho), "label": None, "categoria": "INDEFINIDO"}]
    if not caminho.is_dir():
        return []
    registros: list[dict] = []
    for arq in sorted(caminho.rglob("*")):
        if not (arq.is_file() and eh_imagem(arq)):
            continue
        label = label_pasta(arq.parent.name)
        categoria = "MALIGNO" if label == 1 else "BENIGNO" if label == 0 else "INDEFINIDO"
        registros.append({"caminho": str(arq), "label": label, "categoria": categoria})
    return registros


def listar_sinais(caminho: Path, predicado) -> list[dict]:
    """Lista arquivos de sinal usando um predicado (ex: eh_sinal_temporal)."""
    if caminho.is_file() and predicado(caminho):
        return [{"caminho": str(caminho), "label": None, "categoria": "INDEFINIDO"}]
    if not caminho.is_dir():
        return []
    registros: list[dict] = []
    for arq in sorted(caminho.rglob("*")):
        if not (arq.is_file() and predicado(arq)):
            continue
        label = label_pasta(arq.parent.name)
        categoria = "MALIGNO" if label == 1 else "BENIGNO" if label == 0 else "INDEFINIDO"
        registros.append({"caminho": str(arq), "label": label, "categoria": categoria})
    return registros


def encontrar_csv(caminho: Path) -> Path | None:
    if caminho.is_file() and eh_tabular(caminho):
        return caminho
    if not caminho.is_dir():
        return None
    for arq in sorted(caminho.rglob("*")):
        if arq.is_file() and eh_tabular(arq):
            return arq
    return None


def criar_pasta_run() -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    pasta = RUNS_DIR / f"run_{timestamp}"
    pasta.mkdir(parents=True, exist_ok=True)
    return pasta
