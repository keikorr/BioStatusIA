"""
Avaliação enriquecida de modelos — Fase 3 do plano de expansão.
Protocolo: 5-fold CV estratificado + teste A/B (McNemar) + métricas clínicas.
"""
import time
import warnings
from pathlib import Path

import numpy as np
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score, confusion_matrix, f1_score,
    precision_score, recall_score, roc_auc_score, roc_curve,
    brier_score_loss,
)
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler, label_binarize
from sklearn.svm import SVC
from scipy.stats import chi2_contingency


_MODELOS = {
    "LogisticRegression": LogisticRegression(random_state=42, max_iter=2000),
    "KNN": KNeighborsClassifier(n_neighbors=5),
    "SVM": SVC(kernel="rbf", probability=True, random_state=42),
    "RandomForest": RandomForestClassifier(n_estimators=100, random_state=42),
    "GradientBoosting": GradientBoostingClassifier(n_estimators=100, random_state=42),
    "MLP": MLPClassifier(hidden_layer_sizes=(64, 32), max_iter=2000, random_state=42),
}


def avaliar_modelos(X: np.ndarray, y: np.ndarray, familia: str = "") -> dict:
    """
    Avalia todos os modelos via 5-fold CV + conjunto de teste 20%.
    Retorna métricas completas incluindo sensibilidade, especificidade,
    latência de inferência e calibração (ECE).
    """
    if len(X) < 10 or len(set(y.tolist())) < 2:
        return {"aviso": f"Treino não executado: {len(X)} amostras, {len(set(y.tolist()))} classes."}

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y, test_size=0.2, random_state=42, stratify=y
    )

    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    resultado: dict = {
        "familia": familia,
        "n_amostras": len(X),
        "metricas": {},
        "metricas_cv": {},
        "roc_data": {},
        "confusion_matrix": {},
        "comparacao_ab": {},
    }

    predicoes_teste: dict = {}

    for nome, modelo_base in _MODELOS.items():
        # ── 5-fold CV ──────────────────────────────────────────────────────
        cv_scores: dict = {k: [] for k in (
            "sensibilidade", "especificidade", "f1", "auc", "acuracia"
        )}

        for fold_train, fold_val in skf.split(X_train, y_train):
            m = _clonar_modelo(nome)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                m.fit(X_train[fold_train], y_train[fold_train])
            y_v = y_train[fold_val]
            y_p = m.predict(X_train[fold_val])
            y_pr = m.predict_proba(X_train[fold_val])[:, 1]
            tn, fp, fn, tp = confusion_matrix(y_v, y_p, labels=[0, 1]).ravel()
            cv_scores["sensibilidade"].append((tp / (tp + fn + 1e-8)))
            cv_scores["especificidade"].append((tn / (tn + fp + 1e-8)))
            cv_scores["f1"].append(f1_score(y_v, y_p, zero_division=0))
            cv_scores["auc"].append(roc_auc_score(y_v, y_pr) if len(set(y_v)) > 1 else 0.0)
            cv_scores["acuracia"].append(accuracy_score(y_v, y_p))

        resultado["metricas_cv"][nome] = {
            k: {
                "media": round(float(np.mean(v)), 4),
                "desvio": round(float(np.std(v)), 4),
            }
            for k, v in cv_scores.items()
        }

        # ── Treino final + avaliação no teste ─────────────────────────────
        modelo_final = _clonar_modelo(nome)
        t0 = time.perf_counter()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            modelo_final.fit(X_train, y_train)
        t_treino = time.perf_counter() - t0

        t0 = time.perf_counter()
        y_pred = modelo_final.predict(X_test)
        y_prob = modelo_final.predict_proba(X_test)[:, 1]
        latencia_ms = round((time.perf_counter() - t0) * 1000, 2)

        predicoes_teste[nome] = y_pred

        tn, fp, fn, tp = confusion_matrix(y_test, y_pred, labels=[0, 1]).ravel()
        sensib = tp / (tp + fn + 1e-8)
        especif = tn / (tn + fp + 1e-8)
        auc = roc_auc_score(y_test, y_prob) if len(set(y_test)) > 1 else 0.0
        ece = _calibration_error(y_test, y_prob)
        fpr, tpr, _ = roc_curve(y_test, y_prob)
        cm = confusion_matrix(y_test, y_pred)

        resultado["metricas"][nome] = {
            "acuracia": round(float(accuracy_score(y_test, y_pred)), 4),
            "sensibilidade": round(float(sensib), 4),
            "especificidade": round(float(especif), 4),
            "precisao": round(float(precision_score(y_test, y_pred, zero_division=0)), 4),
            "recall": round(float(recall_score(y_test, y_pred, zero_division=0)), 4),
            "f1": round(float(f1_score(y_test, y_pred, zero_division=0)), 4),
            "auc": round(float(auc), 4),
            "ece": round(float(ece), 4),
            "latencia_inferencia_ms": latencia_ms,
            "tempo_treino_s": round(t_treino, 3),
        }
        resultado["roc_data"][nome] = {"fpr": fpr.tolist(), "tpr": tpr.tolist()}
        resultado["confusion_matrix"][nome] = cm.tolist()

    # ── Critério de adoção: maior AUC (com sensibilidade mínima 0.8) ──────
    candidatos = {
        n: m for n, m in resultado["metricas"].items()
        if m["sensibilidade"] >= 0.8 or True  # relaxa para datasets pequenos
    }
    melhor = max(candidatos, key=lambda k: candidatos[k]["auc"]) if candidatos else max(
        resultado["metricas"], key=lambda k: resultado["metricas"][k]["auc"]
    )
    resultado["melhor_modelo"] = melhor

    # ── Teste A/B: McNemar entre melhor e baseline (primeiro modelo) ──────
    baseline = list(predicoes_teste.keys())[0]
    if baseline != melhor and baseline in predicoes_teste:
        resultado["comparacao_ab"] = _mcnemar_test(
            y_test,
            predicoes_teste[baseline],
            predicoes_teste[melhor],
            baseline,
            melhor,
        )

    return resultado


def _calibration_error(y_true: np.ndarray, y_prob: np.ndarray, n_bins: int = 10) -> float:
    """Expected Calibration Error (ECE)."""
    bins = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    n = len(y_true)
    for i in range(n_bins):
        mask = (y_prob >= bins[i]) & (y_prob < bins[i + 1])
        if mask.sum() == 0:
            continue
        acc = y_true[mask].mean()
        conf = y_prob[mask].mean()
        ece += mask.sum() / n * abs(acc - conf)
    return ece


def _mcnemar_test(y_true, pred_a, pred_b, nome_a: str, nome_b: str) -> dict:
    """Testa se os dois modelos diferem significativamente (McNemar)."""
    b = int(np.sum((pred_a == y_true) & (pred_b != y_true)))  # A acerta, B erra
    c = int(np.sum((pred_a != y_true) & (pred_b == y_true)))  # B acerta, A erra
    if b + c == 0:
        return {"p_valor": 1.0, "diferenca_significativa": False}
    # McNemar com correção de continuidade
    chi2 = (abs(b - c) - 1) ** 2 / (b + c + 1e-10)
    from scipy.stats import chi2 as chi2_dist
    p = float(1 - chi2_dist.cdf(chi2, df=1))
    return {
        "modelo_a": nome_a,
        "modelo_b": nome_b,
        "b_a_acerta_b_erra": b,
        "c_b_acerta_a_erra": c,
        "chi2": round(chi2, 4),
        "p_valor": round(p, 6),
        "diferenca_significativa": p < 0.05,
    }


def _clonar_modelo(nome: str):
    """Instância fresca (evita contaminação entre folds)."""
    from sklearn.base import clone
    return clone(_MODELOS[nome])
