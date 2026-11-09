import pickle
from pathlib import Path

import numpy as np

from biostatusia.pipeline.avaliacao_modelos import avaliar_e_treinar

MODEL_DIR = Path(__file__).parent.parent.parent.parent / "models"
ARQUIVO_VENCEDOR = "modelo_vencedor.pkl"

NOMES_BIOMARCADORES_IMAGEM = [
    "circularidade", "solidez", "contraste", "homogeneidade", "energia",
    "entropia", "snr", "assimetria", "curtose",
]


def _vetor(biomarcadores: dict) -> list[float]:
    m = biomarcadores.get("morfologia", {})
    t = biomarcadores.get("textura_glcm", {})
    d = biomarcadores.get("distribuicao_intensidade", {})
    return [
        m.get("circularidade", 0),
        m.get("solidez", 0),
        t.get("contraste", 0),
        t.get("homogeneidade", 0),
        t.get("energia", 0),
        t.get("entropia", 0),
        d.get("snr", 0),
        d.get("assimetria", 0),
        d.get("curtose", 0),
    ]


def treinar(registros: list[dict]) -> dict:
    """
    registros: [{"biomarcadores": dict, "label": int}, ...]
    Compara os 6 classificadores pelo protocolo de `avaliacao_modelos`.
    """
    X = np.array([_vetor(r["biomarcadores"]) for r in registros], dtype=float)
    y = np.array([r["label"] for r in registros])
    return treinar_vetores(X, y, feature_names=NOMES_BIOMARCADORES_IMAGEM, familia="imagem")


def treinar_vetores(X: np.ndarray, y: np.ndarray, scaling: str = "standard",
                    imputacao: str = "median", grupos: np.ndarray | None = None,
                    feature_names: list[str] | None = None, label_map: dict | None = None,
                    familia: str = "", persistir: bool = True) -> dict:
    """Treina e avalia os 6 candidatos sem vazamento (imputação e escala
    ajustadas só no treino de cada fold) e persiste o vencedor."""
    resultado, treinados = avaliar_e_treinar(
        X, y, familia=familia, scaling=scaling, imputacao=imputacao, grupos=grupos,
    )
    if not treinados or not persistir:
        return resultado

    melhor = resultado["melhor_modelo"]
    MODEL_DIR.mkdir(exist_ok=True)
    with open(MODEL_DIR / ARQUIVO_VENCEDOR, "wb") as f:
        pickle.dump({
            "nome": melhor,
            "pipeline": treinados[melhor],
            "feature_names": feature_names,
            "classes": resultado["classes"],
            "label_map": label_map,
            "piso_sensibilidade_atingido": resultado["piso_sensibilidade_atingido"],
        }, f)
    resultado["modelo_persistido"] = str(MODEL_DIR / ARQUIVO_VENCEDOR)
    return resultado


def classificar(biomarcadores: dict) -> tuple[str, float]:
    """Classifica uma imagem com o modelo vencedor salvo por `treinar`.
    Retorna (categoria, probabilidade da classe positiva)."""
    caminho = MODEL_DIR / ARQUIVO_VENCEDOR
    if not caminho.exists():
        return "INDEFINIDO", 0.0
    with open(caminho, "rb") as f:
        salvo = pickle.load(f)
    if salvo.get("feature_names") != NOMES_BIOMARCADORES_IMAGEM or len(salvo["classes"]) != 2:
        return "INDEFINIDO", 0.0
    X = np.array([_vetor(biomarcadores)], dtype=float)
    prob = float(salvo["pipeline"].predict_proba(X)[0][1])
    return ("MALIGNO" if prob > 0.5 else "BENIGNO"), round(prob, 4)
