"""
AutoML do BioStatusIA — implementação única usada por todas as modalidades.

Protocolo (sem vazamento entre seleção e avaliação):
1) Split externo estratificado 80/20 (seed 42). Se houver identificador de
   sujeito/paciente (`grupos`), o split é feito por grupo, para que o mesmo
   sujeito nunca apareça em treino e teste.
2) Seleção do modelo: validação cruzada repetida (até 5 folds x 3 repetições)
   executada só dentro do treino. Imputação e escalonamento ficam dentro de um
   `Pipeline` e são reajustados em cada fold.
3) Critério: score interno (AUROC, MCC, ECE e penalidade de sensibilidade),
   com piso rígido de sensibilidade média na CV. Se nenhum candidato atinge o
   piso, o de maior score é devolvido com `piso_sensibilidade_atingido=False`.
4) Avaliação final: cada candidato é retreinado no treino completo e avaliado
   uma única vez no teste. Essas métricas são reportadas e NÃO influenciam a
   escolha.

Binário e multiclasse são tratados no mesmo código; em multiclasse as
métricas de sensibilidade/especificidade são médias macro e o recall por
classe é devolvido separadamente.
"""
from __future__ import annotations

import time
import warnings

import numpy as np
from sklearn.base import clone
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score, cohen_kappa_score, confusion_matrix, f1_score,
    matthews_corrcoef, roc_auc_score, roc_curve,
)
from sklearn.model_selection import (
    RepeatedStratifiedKFold, StratifiedGroupKFold, train_test_split,
)
from sklearn.neighbors import KNeighborsClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import RobustScaler, StandardScaler
from sklearn.svm import SVC

SEED = 42
S_MIN = 0.80
N_REPETICOES_CV = 3

_MODELOS = {
    "LogisticRegression": LogisticRegression(random_state=SEED, max_iter=2000),
    "KNN": KNeighborsClassifier(n_neighbors=5),
    "SVM": SVC(kernel="rbf", probability=True, random_state=SEED),
    "RandomForest": RandomForestClassifier(n_estimators=100, random_state=SEED),
    "GradientBoosting": GradientBoostingClassifier(n_estimators=100, random_state=SEED),
    "MLP": MLPClassifier(hidden_layer_sizes=(64, 32), max_iter=2000, random_state=SEED),
}

CAMPOS_CV = ("sensibilidade", "especificidade", "f1", "auc", "acuracia", "mcc", "kappa", "ece")


# ── Pipeline por candidato ────────────────────────────────────────────────────

def _scaler(scaling: str):
    if scaling == "robust":
        return RobustScaler()
    if scaling == "standard":
        return StandardScaler()
    return "passthrough"


def montar_pipeline(nome: str, scaling: str = "standard", imputacao: str = "median") -> Pipeline:
    """Imputação + escalonamento + modelo num único estimador, para que todo
    ajuste aconteça só sobre os dados de treino de cada fold."""
    estrategia = "mean" if imputacao == "mean" else "median"
    return Pipeline([
        ("imputacao", SimpleImputer(strategy=estrategia, keep_empty_features=True)),
        ("escala", _scaler(scaling)),
        ("modelo", clone(_MODELOS[nome])),
    ])


# ── Métricas ──────────────────────────────────────────────────────────────────

def calcular_ece(y_true: np.ndarray, y_proba: np.ndarray, classes: list, n_bins: int = 10) -> float:
    """Expected Calibration Error com 10 bins de largura igual.

    O último bin é fechado ([0.9, 1.0]); com bins semiabertos, probabilidades
    iguais a 1.0 ficariam fora de todos os bins mas dentro do denominador, o
    que subestima o ECE de modelos muito confiantes.
    Binário: probabilidade da classe positiva vs. frequência observada.
    Multiclasse: confiança da classe prevista vs. acerto.
    """
    y_true = np.asarray(y_true)
    if y_proba is None or len(y_true) == 0:
        return 0.0
    if len(classes) == 2:
        conf = y_proba[:, 1]
        alvo = (y_true == classes[1]).astype(float)
    else:
        idx = np.argmax(y_proba, axis=1)
        conf = y_proba[np.arange(len(y_proba)), idx]
        alvo = (np.asarray(classes)[idx] == y_true).astype(float)
    bordas = np.linspace(0.0, 1.0, n_bins + 1)
    ece, n = 0.0, len(y_true)
    for i in range(n_bins):
        superior = conf <= bordas[i + 1] if i == n_bins - 1 else conf < bordas[i + 1]
        m = (conf >= bordas[i]) & superior
        if m.any():
            ece += m.sum() / n * abs(alvo[m].mean() - conf[m].mean())
    return float(ece)


def calcular_metricas_classificacao(y_true, y_pred, y_proba, classes: list) -> dict:
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    cm = confusion_matrix(y_true, y_pred, labels=classes)
    binario = len(classes) == 2

    recall_por_classe, espec_por_classe = [], []
    for i in range(len(classes)):
        tp = cm[i, i]
        fn = cm[i, :].sum() - tp
        fp = cm[:, i].sum() - tp
        tn = cm.sum() - tp - fn - fp
        recall_por_classe.append(tp / (tp + fn) if tp + fn else 0.0)
        espec_por_classe.append(tn / (tn + fp) if tn + fp else 0.0)

    if binario:
        tn, fp, fn, tp = cm.ravel()
        sensib = tp / (tp + fn) if tp + fn else 0.0
        especif = tn / (tn + fp) if tn + fp else 0.0
        vpp = tp / (tp + fp) if tp + fp else 0.0
        vpn = tn / (tn + fn) if tn + fn else 0.0
        f1 = f1_score(y_true, y_pred, pos_label=classes[1], zero_division=0)
    else:
        sensib = float(np.mean(recall_por_classe))
        especif = float(np.mean(espec_por_classe))
        vpp = vpn = None
        f1 = f1_score(y_true, y_pred, average="macro", labels=classes, zero_division=0)

    auc, brier = 0.0, None
    if y_proba is not None and len(np.unique(y_true)) > 1:
        try:
            if binario:
                p1 = y_proba[:, 1]
                auc = roc_auc_score(y_true == classes[1], p1)
                brier = float(np.mean((p1 - (y_true == classes[1])) ** 2))
            else:
                auc = roc_auc_score(y_true, y_proba, multi_class="ovr", average="macro", labels=classes)
        except ValueError:
            auc = 0.0

    m = {
        "acuracia": float(accuracy_score(y_true, y_pred)),
        "acuracia_balanceada": float(np.mean(recall_por_classe)),
        "sensibilidade": float(sensib),
        "especificidade": float(especif),
        "precisao": None if vpp is None else float(vpp),
        "vpn": None if vpn is None else float(vpn),
        "recall": float(sensib),
        "f1": float(f1),
        "auc": float(auc),
        "mcc": float(matthews_corrcoef(y_true, y_pred)),
        "kappa": float(cohen_kappa_score(y_true, y_pred)),
        "ece": calcular_ece(y_true, y_proba, classes),
        "brier": brier,
        "recall_por_classe": [float(v) for v in recall_por_classe],
        "n_classes": len(classes),
    }
    return {k: (round(v, 4) if isinstance(v, float) else v) for k, v in m.items()}


def calcular_score_clinico(metricas: dict, s_min: float = S_MIN, w_auc: float = 0.40,
                           w_mcc: float = 0.40, w_ece: float = 0.20,
                           penalty_lambda: float = 1.0) -> float:
    """Score interno de ranqueamento. Os pesos e o piso são configurações
    operacionais do pipeline, não limiares clínicos validados."""
    auc = metricas.get("auc", 0.0)
    mcc_norm = max(0.0, (metricas.get("mcc", 0.0) + 1.0) / 2.0)
    ece = min(1.0, max(0.0, metricas.get("ece", 0.0)))
    deficit = max(0.0, s_min - metricas.get("sensibilidade", 0.0))
    return float(w_auc * auc + w_mcc * mcc_norm - w_ece * ece - penalty_lambda * deficit ** 1.5)


def selecionar_melhor_modelo(metricas_cv: dict, s_min: float = S_MIN) -> dict:
    """Escolhe o vencedor só com médias da CV interna."""
    nomes = list(metricas_cv)
    convencional = max(nomes, key=lambda k: (metricas_cv[k]["auc"], metricas_cv[k]["acuracia"]))
    elegiveis = [n for n in nomes if metricas_cv[n]["sensibilidade"] >= s_min]
    piso = bool(elegiveis)
    pool = elegiveis if piso else nomes
    ranking = sorted(pool, key=lambda k: metricas_cv[k]["score_clinico"], reverse=True)
    melhor = ranking[0]
    m = metricas_cv[melhor]
    aviso = None
    if not piso:
        aviso = (
            f"Nenhum dos {len(nomes)} classificadores atingiu sensibilidade média >= {s_min:.2f} "
            f"na validação cruzada interna. '{melhor}' foi devolvido apenas como o de maior score "
            f"(sensibilidade CV = {m['sensibilidade']:.3f}) e não deve ser tratado como seleção "
            f"que cumpre o critério."
        )
    return {
        "melhor_modelo": melhor,
        "melhor_modelo_clinico": melhor,
        "melhor_modelo_convencional": convencional,
        "selecao_divergente": melhor != convencional,
        "segundo_colocado": next(
            (n for n in sorted(nomes, key=lambda k: metricas_cv[k]["score_clinico"], reverse=True)
             if n != melhor), None),
        "piso_sensibilidade_atingido": piso,
        "aviso_piso_sensibilidade": aviso,
        "criterio_selecao": (
            f"Score interno na CV [score={m['score_clinico']:.4f}; AUROC={m['auc']:.3f}; "
            f"MCC={m['mcc']:.3f}; ECE={m['ece']:.3f}; sens={m['sensibilidade']:.3f}]"
            + ("" if piso else " — piso de sensibilidade não atingido por nenhum candidato")
        ),
    }


# ── Particionamento ───────────────────────────────────────────────────────────

def _contagem_min(y) -> int:
    _, c = np.unique(y, return_counts=True)
    return int(c.min())


def _split_externo(X, y, grupos):
    if grupos is not None and len(np.unique(grupos)) >= 5:
        sgkf = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=SEED)
        tr, te = next(sgkf.split(X, y, grupos))
        return tr, te, "StratifiedGroupKFold (1 de 5 folds como teste; por sujeito)"
    idx = np.arange(len(y))
    tr, te = train_test_split(idx, test_size=0.2, random_state=SEED, stratify=y)
    return tr, te, "train_test_split estratificado 80/20 (por amostra)"


def _folds_internos(X, y, grupos):
    n_splits = max(2, min(5, _contagem_min(y)))
    if grupos is not None and len(np.unique(grupos)) >= n_splits:
        folds = []
        for r in range(N_REPETICOES_CV):
            sgkf = StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=SEED + r)
            folds += list(sgkf.split(X, y, grupos))
        return folds, n_splits, "StratifiedGroupKFold repetido (por sujeito)"
    rskf = RepeatedStratifiedKFold(n_splits=n_splits, n_repeats=N_REPETICOES_CV, random_state=SEED)
    return list(rskf.split(X, y)), n_splits, "RepeatedStratifiedKFold (por amostra)"


def _resumo(valores: list[float]) -> dict:
    v = np.asarray(valores, dtype=float)
    media = float(v.mean())
    if len(v) > 1:
        from scipy.stats import t as t_dist
        dp = float(v.std(ddof=1))
        margem = float(t_dist.ppf(0.975, df=len(v) - 1)) * dp / np.sqrt(len(v))
    else:
        dp, margem = 0.0, 0.0
    return {"media": round(media, 4), "desvio": round(dp, 4),
            "ic95": [round(float(media - margem), 4), round(float(media + margem), 4)]}


# ── Núcleo ────────────────────────────────────────────────────────────────────

def avaliar_e_treinar(X: np.ndarray, y: np.ndarray, familia: str = "",
                      scaling: str = "standard", imputacao: str = "median",
                      grupos: np.ndarray | None = None) -> tuple[dict, dict]:
    """Executa o protocolo completo. Devolve (resultado serializável, pipelines
    treinados no treino completo, por nome)."""
    t_inicio = time.perf_counter()
    X = np.asarray(X, dtype=float)
    y = np.asarray(y)
    classes = sorted(np.unique(y).tolist())
    if len(X) < 10 or len(classes) < 2:
        return {"aviso": f"Treino não executado: {len(X)} amostras, {len(classes)} classes."}, {}
    if _contagem_min(y) < 2:
        return {"aviso": "Treino não executado: alguma classe tem menos de 2 amostras."}, {}

    grupos = None if grupos is None else np.asarray(grupos)
    tr, te, protocolo_externo = _split_externo(X, y, grupos)
    X_tr, X_te, y_tr, y_te = X[tr], X[te], y[tr], y[te]
    g_tr = None if grupos is None else grupos[tr]
    folds, n_splits, protocolo_interno = _folds_internos(X_tr, y_tr, g_tr)

    resultado: dict = {
        "familia": familia,
        "n_amostras": int(len(X)),
        "n_treino": int(len(tr)),
        "n_teste": int(len(te)),
        "n_classes": len(classes),
        "classes": [c if isinstance(c, str) else int(c) for c in classes],
        "metricas": {}, "metricas_cv": {}, "roc_data": {}, "confusion_matrix": {},
        "comparacao_ab": {},
        "protocolo_validacao": {
            "split_externo": protocolo_externo,
            "selecao": f"{protocolo_interno}: {n_splits} folds x {N_REPETICOES_CV} repetições, só no treino",
            "pre_processamento": f"imputação ({imputacao}) e escala ({scaling}) ajustadas dentro de cada fold",
            "avaliacao_final": "conjunto de teste usado uma única vez; não participa da seleção",
            "agrupamento_por_sujeito": grupos is not None and "sujeito" in protocolo_externo,
        },
    }

    for nome in _MODELOS:
        acumulado = {k: [] for k in CAMPOS_CV}
        for f_tr, f_va in folds:
            pipe = montar_pipeline(nome, scaling, imputacao)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                pipe.fit(X_tr[f_tr], y_tr[f_tr])
            yv = y_tr[f_va]
            mf = calcular_metricas_classificacao(yv, pipe.predict(X_tr[f_va]),
                                                 pipe.predict_proba(X_tr[f_va]), classes)
            for k in CAMPOS_CV:
                acumulado[k].append(mf[k])
        resumo = {k: _resumo(v) for k, v in acumulado.items()}
        medias = {k: resumo[k]["media"] for k in CAMPOS_CV}
        resumo["score_clinico"] = round(calcular_score_clinico(medias), 4)
        resultado["metricas_cv"][nome] = resumo

    medias_cv = {n: {**{k: r[k]["media"] for k in CAMPOS_CV}, "score_clinico": r["score_clinico"]}
                 for n, r in resultado["metricas_cv"].items()}
    selecao = selecionar_melhor_modelo(medias_cv)
    resultado.update(selecao)

    treinados: dict = {}
    predicoes: dict = {}
    for nome in _MODELOS:
        pipe = montar_pipeline(nome, scaling, imputacao)
        t0 = time.perf_counter()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            pipe.fit(X_tr, y_tr)
        t_treino = time.perf_counter() - t0
        t0 = time.perf_counter()
        proba = pipe.predict_proba(X_te)
        pred = pipe.predict(X_te)
        latencia = (time.perf_counter() - t0) * 1000 / max(1, len(X_te))

        mt = calcular_metricas_classificacao(y_te, pred, proba, classes)
        mt["latencia_inferencia_ms"] = round(latencia, 4)
        mt["tempo_treino_s"] = round(t_treino, 3)
        mt["sensibilidade_cv"] = medias_cv[nome]["sensibilidade"]
        mt["score_clinico_cv"] = medias_cv[nome]["score_clinico"]
        resultado["metricas"][nome] = mt
        resultado["confusion_matrix"][nome] = confusion_matrix(y_te, pred, labels=classes).tolist()
        if len(classes) == 2:
            fpr, tpr, _ = roc_curve(y_te == classes[1], proba[:, 1])
            resultado["roc_data"][nome] = {"fpr": fpr.tolist(), "tpr": tpr.tolist()}
        treinados[nome] = pipe
        predicoes[nome] = pred

    melhor, segundo = selecao["melhor_modelo"], selecao["segundo_colocado"]
    if segundo:
        resultado["comparacao_ab"] = _mcnemar_test(y_te, predicoes[segundo], predicoes[melhor],
                                                   segundo, melhor)
    resultado["tempo_automl_s"] = round(time.perf_counter() - t_inicio, 3)
    return resultado, treinados


def avaliar_modelos(X: np.ndarray, y: np.ndarray, familia: str = "", **kwargs) -> dict:
    """Interface usada pelas tools de sinal, áudio, DICOM, volume e vídeo."""
    resultado, _ = avaliar_e_treinar(X, y, familia=familia, **kwargs)
    return resultado


def _mcnemar_test(y_true, pred_a, pred_b, nome_a: str, nome_b: str) -> dict:
    """McNemar com correção de continuidade entre o vencedor e o segundo
    colocado pelo score interno, no conjunto de teste. Descritivo: o teste
    não participa da seleção."""
    b = int(np.sum((pred_a == y_true) & (pred_b != y_true)))
    c = int(np.sum((pred_a != y_true) & (pred_b == y_true)))
    base = {"modelo_a": nome_a, "modelo_b": nome_b,
            "b_a_acerta_b_erra": b, "c_b_acerta_a_erra": c}
    if b + c == 0:
        return {**base, "chi2": 0.0, "p_valor": 1.0, "diferenca_significativa": False}
    from scipy.stats import chi2 as chi2_dist
    chi2 = (abs(b - c) - 1) ** 2 / (b + c)
    p = float(1 - chi2_dist.cdf(chi2, df=1))
    return {**base, "chi2": round(chi2, 4), "p_valor": round(p, 6),
            "diferenca_significativa": p < 0.05}
