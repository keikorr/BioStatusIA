from datetime import datetime
from pathlib import Path

EXT_IMAGENS = (".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff")
EXT_TABULARES = (".csv", ".txt", ".tsv")
PASTAS_BENIGNAS = {"benign", "benigno", "normal", "negative", "0"}
PASTAS_MALIGNAS = {"malignant", "malign", "maligno", "abnormal", "positive", "1"}

RUNS_DIR = Path(__file__).parent.parent / "static" / "runs"


def eh_imagem(arquivo: Path) -> bool:
    return arquivo.suffix.lower() in EXT_IMAGENS and "mask" not in arquivo.name.lower()


def eh_tabular(arquivo: Path) -> bool:
    return arquivo.suffix.lower() in EXT_TABULARES


def label_pasta(nome_pasta: str) -> int | None:
    nome = nome_pasta.lower()
    if nome in PASTAS_BENIGNAS:
        return 0
    if nome in PASTAS_MALIGNAS:
        return 1
    return None


def listar_imagens(caminho: Path) -> list[dict]:
    """Lista imagens em qualquer caminho. Detecta rótulo pelas pastas pai."""
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
