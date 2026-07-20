import pickle
import time
from pathlib import Path

import numpy as np
import warnings
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.exceptions import ConvergenceWarning
from sklearn.metrics import (
    accuracy_score,
    cohen_kappa_score,
    confusion_matrix,
    f1_score,
    matthews_corrcoef,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)


def _ece(y_true: np.ndarray, y_prob: np.ndarray, n_bins: int = 10) -> float:
    """Expected Calibration Error (10 bins)."""
    bins = np.linspace(0, 1, n_bins + 1)
    n = len(y_true)
    ece = 0.0
    for i in range(n_bins):
        mask = (y_prob >= bins[i]) & (y_prob < bins[i + 1])
        if mask.sum() == 0:
            continue
        ece += mask.sum() / n * abs(y_true[mask].mean() - y_prob[mask].mean())
    return float(ece)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.svm import SVC

MODEL_DIR = Path(__file__).parent.parent.parent.parent / "models"


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
    registros: [{"biomarcadores": dict, "label": 0|1}, ...]
    Treina SVM e RandomForest, retorna métricas completas para os gráficos.
    """
    X = np.array([_vetor(r["biomarcadores"]) for r in registros])
    y = np.array([r["label"] for r in registros])
    return treinar_vetores(X, y)


def treinar_vetores(X: np.ndarray, y: np.ndarray, scaling: str = "standard",
                    familia: str = "", feature_names: list[str] | None = None) -> dict:
    """Versão genérica com escalamento dinâmico baseado na estratégia decidida."""
    if scaling == "robust":
        scaler = RobustScaler()
    elif scaling == "standard":
        scaler = StandardScaler()
    else:
        scaler = None

    X_scaled = scaler.fit_transform(X) if scaler is not None else X

    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y, test_size=0.2, random_state=42, stratify=y
    )

    modelos = {
        "LogisticRegression": LogisticRegression(random_state=42, max_iter=2000),
        "KNN": KNeighborsClassifier(n_neighbors=5),
        "SVM": SVC(kernel="rbf", probability=True, random_state=42),
        "RandomForest": RandomForestClassifier(n_estimators=100, random_state=42),
        "GradientBoosting": GradientBoostingClassifier(n_estimators=100, random_state=42),
        "MLP": MLPClassifier(hidden_layer_sizes=(64, 32), max_iter=2000, random_state=42),
    }

    resultado: dict = {"metricas": {}, "roc_data": {}, "confusion_matrix": {}}

    MODEL_DIR.mkdir(exist_ok=True)

    for nome, modelo in modelos.items():
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            t0 = time.perf_counter()
            modelo.fit(X_train, y_train)
            t_treino = time.perf_counter() - t0

        t0 = time.perf_counter()
        y_pred = modelo.predict(X_test)
        latencia_ms = round((time.perf_counter() - t0) * 1000 / max(1, len(X_test)), 4)
        y_prob = modelo.predict_proba(X_test)[:, 1]
        fpr, tpr, _ = roc_curve(y_test, y_prob)
        cm = confusion_matrix(y_test, y_pred)

        tn, fp, fn, tp = confusion_matrix(y_test, y_pred, labels=[0, 1]).ravel()
        sensib = tp / (tp + fn + 1e-8)
        especif = tn / (tn + fp + 1e-8)
        auc = roc_auc_score(y_test, y_prob) if len(set(y_test.tolist())) > 1 else 0.0

        resultado["metricas"][nome] = {
            "acuracia": round(float(accuracy_score(y_test, y_pred)), 4),
            "sensibilidade": round(float(sensib), 4),
            "especificidade": round(float(especif), 4),
            "precisao": round(float(precision_score(y_test, y_pred, zero_division=0)), 4),
            "recall": round(float(recall_score(y_test, y_pred, zero_division=0)), 4),
            "f1": round(float(f1_score(y_test, y_pred, zero_division=0)), 4),
            "auc": round(float(auc), 4),
            "mcc": round(float(matthews_corrcoef(y_test, y_pred)), 4),
            "kappa": round(float(cohen_kappa_score(y_test, y_pred)), 4),
            "ece": round(_ece(y_test, y_prob), 4),
            "latencia_inferencia_ms": latencia_ms,
            "tempo_treino_s": round(t_treino, 3),
        }
        resultado["roc_data"][nome] = {"fpr": fpr.tolist(), "tpr": tpr.tolist()}
        resultado["confusion_matrix"][nome] = cm.tolist()

        with open(MODEL_DIR / f"modelo_{nome.lower()}.pkl", "wb") as f:
            pickle.dump({"modelo": modelo, "scaler": scaler}, f)

    melhor = max(
        resultado["metricas"], key=lambda k: resultado["metricas"][k]["auc"]
    )
    resultado["melhor_modelo"] = melhor

    # Persistir o vencedor do pódio para inferência individual (Aba 4 / Laudo Individual).
    try:
        from biostatusia.pipeline.inferencia import salvar_modelo_vencedor
        salvar_modelo_vencedor(
            nome=melhor, modelo=modelos[melhor], scaler=scaler,
            familia=familia or "IMG", feature_names=feature_names,
            metricas=resultado["metricas"][melhor],
        )
    except Exception:
        pass

    return resultado


def classificar(biomarcadores: dict) -> tuple[str, float]:
    """Classifica usando o melhor modelo salvo em disco. Retorna (categoria, probabilidade)."""
    nomes_possiveis = [
        "logisticregression", "knn", "svm", "randomforest", "gradientboosting", "mlp"
    ]
    for nome in nomes_possiveis:
        caminho = MODEL_DIR / f"modelo_{nome}.pkl"
        if caminho.exists():
            with open(caminho, "rb") as f:
                salvo = pickle.load(f)
            X = np.array([_vetor(biomarcadores)])
            X_scaled = salvo["scaler"].transform(X) if salvo.get("scaler") is not None else X
            prob = float(salvo["modelo"].predict_proba(X_scaled)[0][1])
            return ("MALIGNO" if prob > 0.5 else "BENIGNO"), round(prob, 4)
    return "INDEFINIDO", 0.0
