"""
Avaliação enriquecida de modelos — Fase 3 do plano de expansão.
Protocolo: CV estratificada REPETIDA (5x3) + teste A/B (McNemar) + métricas clínicas.
Sem vazamento: escala e balanceamento ajustados por partição (T1/T2);
seleção com piso clínico de sensibilidade (T3); intervalos de confiança 95% (T4).
"""
import time
import warnings
from pathlib import Path

import numpy as np
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score, cohen_kappa_score, confusion_matrix, f1_score,
    matthews_corrcoef, precision_score, recall_score, roc_auc_score, roc_curve,
    brier_score_loss,
)
from sklearn.model_selection import (
    RepeatedStratifiedKFold, StratifiedKFold, train_test_split,
)
from sklearn.neighbors import KNeighborsClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler, label_binarize
from sklearn.svm import SVC


_MODELOS = {
    "LogisticRegression": LogisticRegression(random_state=42, max_iter=2000),
    "KNN": KNeighborsClassifier(n_neighbors=5),
    "SVM": SVC(kernel="rbf", probability=True, random_state=42),
    "RandomForest": RandomForestClassifier(n_estimators=100, random_state=42),
    "GradientBoosting": GradientBoostingClassifier(n_estimators=100, random_state=42),
    "MLP": MLPClassifier(hidden_layer_sizes=(64, 32), max_iter=2000, random_state=42),
}


# ── Balanceamento de classes (SMOTE / ADASYN) ─────────────────────────────────

def balancear(X: np.ndarray, y: np.ndarray, metodo: str = "smote") -> tuple[np.ndarray, np.ndarray, dict]:
    """
    Reamostra o conjunto de treino para equilibrar as classes.
    Só aplica se houver desbalanceamento e amostras suficientes (SMOTE precisa
    de ao menos k_neighbors+1 exemplos na classe minoritária). Falha de forma
    segura devolvendo os dados originais.
    """
    info = {"aplicado": False, "metodo": metodo}
    classes, contagens = np.unique(y, return_counts=True)
    if len(classes) < 2:
        info["motivo"] = "classe única"
        return X, y, info

    minoria = int(contagens.min())
    info["distribuicao_original"] = {int(c): int(n) for c, n in zip(classes, contagens)}
    if contagens.max() == contagens.min():
        info["motivo"] = "já balanceado"
        return X, y, info

    k = min(5, minoria - 1)
    if k < 1:
        info["motivo"] = f"classe minoritária com {minoria} amostras — insuficiente para reamostragem"
        return X, y, info

    try:
        if metodo == "adasyn":
            from imblearn.over_sampling import ADASYN
            sampler = ADASYN(random_state=42, n_neighbors=k)
        else:
            from imblearn.over_sampling import SMOTE
            sampler = SMOTE(random_state=42, k_neighbors=k)
        X_bal, y_bal = sampler.fit_resample(X, y)
        cls_b, cont_b = np.unique(y_bal, return_counts=True)
        info["aplicado"] = True
        info["distribuicao_balanceada"] = {int(c): int(n) for c, n in zip(cls_b, cont_b)}
        return X_bal, y_bal, info
    except Exception as e:
        info["erro"] = str(e)
        return X, y, info


# ── Seleção de features (RFE / PCA) ───────────────────────────────────────────

def selecionar_features(X: np.ndarray, y: np.ndarray, metodo: str = "rfe",
                        n_features: int | None = None):
    """
    Reduz a dimensionalidade por importância (RFE) ou variância (PCA).
    Retorna (X_reduzido, transformador_ou_None, info). Segura para datasets pequenos.
    """
    info = {"metodo": metodo, "aplicado": False, "n_original": X.shape[1]}
    n_alvo = n_features or max(2, min(X.shape[1], X.shape[0] // 3, 20))
    if X.shape[1] <= n_alvo:
        info["motivo"] = "dimensionalidade já baixa"
        return X, None, info

    try:
        if metodo == "pca":
            from sklearn.decomposition import PCA
            transf = PCA(n_components=n_alvo, random_state=42)
            X_red = transf.fit_transform(X)
            info["variancia_explicada"] = round(float(transf.explained_variance_ratio_.sum()), 4)
        else:
            from sklearn.feature_selection import RFE
            transf = RFE(RandomForestClassifier(n_estimators=50, random_state=42),
                         n_features_to_select=n_alvo)
            X_red = transf.fit_transform(X, y)
            info["mascara_selecionadas"] = transf.support_.tolist()
        info["aplicado"] = True
        info["n_selecionadas"] = n_alvo
        return X_red, transf, info
    except Exception as e:
        info["erro"] = str(e)
        return X, None, info


def avaliar_modelos(X: np.ndarray, y: np.ndarray, familia: str = "",
                    balancear_treino: str = "smote",
                    feature_names: list[str] | None = None,
                    persistir_vencedor: bool = True) -> dict:
    """
    Avalia todos os modelos via 5-fold CV + conjunto de teste 20%.
    Retorna métricas completas: sensibilidade, especificidade, precisão, recall,
    F1, AUC, MCC (Matthews), Kappa (Cohen), ECE, latência e tempo de treino.
    Aplica balanceamento (SMOTE/ADASYN) apenas no conjunto de treino, e calcula
    importância de features por SHAP para o modelo vencedor.
    """
    if len(X) < 10 or len(set(y.tolist())) < 2:
        return {"aviso": f"Treino não executado: {len(X)} amostras, {len(set(y.tolist()))} classes."}

    # T1 — split ANTES de qualquer escalonamento/balanceamento (sem vazamento).
    X_train_raw, X_test_raw, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Scaler ajustado SÓ no treino; o teste é apenas transformado.
    scaler = StandardScaler().fit(X_train_raw)
    X_test = scaler.transform(X_test_raw)

    # Treino final (compartilhado entre modelos): escala + balanceamento
    # aplicados apenas ao treino — o teste permanece intocado.
    X_train_scaled = scaler.transform(X_train_raw)
    X_train_bal, y_train_bal, info_balanceamento = balancear(
        X_train_scaled, y_train, metodo=balancear_treino
    )

    # T2/T4 — CV estratificada REPETIDA; escala e balanceamento reajustados
    # DENTRO de cada fold, sobre a partição de treino do fold.
    n_min = int(np.min(np.bincount(y_train)))
    n_splits = max(2, min(5, n_min))
    n_repeats = 3
    rskf = RepeatedStratifiedKFold(
        n_splits=n_splits, n_repeats=n_repeats, random_state=42
    )
    resultado: dict = {
        "familia": familia,
        "n_amostras": len(X),
        "balanceamento": info_balanceamento,
        "cv_protocolo": {"n_splits": n_splits, "n_repeats": n_repeats},
        "metricas": {},
        "metricas_cv": {},
        "roc_data": {},
        "confusion_matrix": {},
        "comparacao_ab": {},
        "shap": {},
    }

    predicoes_teste: dict = {}
    modelos_treinados: dict = {}

    for nome, modelo_base in _MODELOS.items():
        # ── T2/T4 — CV repetida; escala e balanceamento POR fold ───────────
        cv_scores: dict = {k: [] for k in (
            "sensibilidade", "especificidade", "f1", "auc", "acuracia", "mcc", "kappa"
        )}

        for fold_train, fold_val in rskf.split(X_train_raw, y_train):
            sc_fold = StandardScaler().fit(X_train_raw[fold_train])
            Xf_tr = sc_fold.transform(X_train_raw[fold_train])
            Xf_val = sc_fold.transform(X_train_raw[fold_val])
            yf_tr = y_train[fold_train]
            Xf_tr, yf_tr, _ = balancear(Xf_tr, yf_tr, metodo=balancear_treino)

            m = _clonar_modelo(nome)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                m.fit(Xf_tr, yf_tr)
            y_v = y_train[fold_val]
            y_p = m.predict(Xf_val)
            y_pr = m.predict_proba(Xf_val)[:, 1]
            tn, fp, fn, tp = confusion_matrix(y_v, y_p, labels=[0, 1]).ravel()
            cv_scores["sensibilidade"].append((tp / (tp + fn + 1e-8)))
            cv_scores["especificidade"].append((tn / (tn + fp + 1e-8)))
            cv_scores["f1"].append(f1_score(y_v, y_p, zero_division=0))
            cv_scores["auc"].append(roc_auc_score(y_v, y_pr) if len(set(y_v)) > 1 else 0.0)
            cv_scores["acuracia"].append(accuracy_score(y_v, y_p))
            cv_scores["mcc"].append(matthews_corrcoef(y_v, y_p))
            cv_scores["kappa"].append(cohen_kappa_score(y_v, y_p))

        resultado["metricas_cv"][nome] = {
            k: {
                "media": round(float(np.mean(v)), 4),
                "desvio": round(float(np.std(v)), 4),
                "ic95": _ic95(v),
            }
            for k, v in cv_scores.items()
        }

        # ── Treino final + avaliação no teste (treino escalado+balanceado) ─
        modelo_final = _clonar_modelo(nome)
        t0 = time.perf_counter()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            modelo_final.fit(X_train_bal, y_train_bal)
        t_treino = time.perf_counter() - t0

        t0 = time.perf_counter()
        y_pred = modelo_final.predict(X_test)
        y_prob = modelo_final.predict_proba(X_test)[:, 1]
        latencia_ms = round((time.perf_counter() - t0) * 1000, 2)

        predicoes_teste[nome] = y_pred
        modelos_treinados[nome] = modelo_final

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
            "mcc": round(float(matthews_corrcoef(y_test, y_pred)), 4),
            "kappa": round(float(cohen_kappa_score(y_test, y_pred)), 4),
            "ece": round(float(ece), 4),
            "latencia_inferencia_ms": latencia_ms,
            "tempo_treino_s": round(t_treino, 3),
        }
        # Score clínico multiobjetivo para o modelo
        score_clin = calcular_score_clinico(resultado["metricas"][nome])
        resultado["metricas"][nome]["score_clinico"] = round(float(score_clin), 4)
        resultado["roc_data"][nome] = {"fpr": fpr.tolist(), "tpr": tpr.tolist()}
        resultado["confusion_matrix"][nome] = cm.tolist()

    # ── Seleção Convencional (Critério Clássico: Maior Acurácia / AUC Bruta) ────
    melhor_convencional = max(
        resultado["metricas"], key=lambda k: (resultado["metricas"][k]["auc"], resultado["metricas"][k]["acuracia"])
    )

    # ── Seleção BioStatusIA: Função de Otimização Multiobjetivo Clinicamente Orientada ──
    # Combina AUROC (0.40) + MCC (0.40) - ECE (0.20) com penalização severa se Sensibilidade < S_min (0.80)
    melhor_clinico = max(
        resultado["metricas"], key=lambda k: resultado["metricas"][k]["score_clinico"]
    )

    melhor = melhor_clinico
    resultado["melhor_modelo"] = melhor
    resultado["melhor_modelo_clinico"] = melhor_clinico
    resultado["melhor_modelo_convencional"] = melhor_convencional
    resultado["selecao_divergente"] = (melhor_clinico != melhor_convencional)
    resultado["criterio_selecao"] = (
        f"Multiobjetivo Clínico [Score={resultado['metricas'][melhor]['score_clinico']:.4f} | "
        f"AUROC={resultado['metricas'][melhor]['auc']:.2f}, MCC={resultado['metricas'][melhor]['mcc']:.2f}, "
        f"ECE={resultado['metricas'][melhor]['ece']:.3f}, Sens={resultado['metricas'][melhor]['sensibilidade']:.2f}]"
    )

    # ── Interpretabilidade SHAP para o modelo vencedor ────────────────────
    resultado["shap"] = _shap_importancia(
        modelos_treinados[melhor], X_train_bal, X_test, feature_names, melhor
    )

    # ── Persistir o vencedor do pódio para inferência individual ──────────
    if persistir_vencedor:
        from biostatusia.pipeline.inferencia import salvar_modelo_vencedor
        resultado["modelo_persistido"] = salvar_modelo_vencedor(
            nome=melhor, modelo=modelos_treinados[melhor], scaler=scaler,
            familia=familia, feature_names=feature_names,
            metricas=resultado["metricas"][melhor],
        )

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


def calcular_score_clinico(metricas: dict, s_min: float = 0.80,
                           w_auc: float = 0.40, w_mcc: float = 0.40,
                           w_ece: float = 0.20, penalty_lambda: float = 1.0) -> float:
    """
    Função de Seleção AutoML Clinicamente Orientada (BioStatusIA).
    Equilibra capacidade discriminatória (AUROC), robustez contra desbalanceamento (MCC)
    e confiabilidade probabilística (ECE), aplicando penalidade para modelos que falham
    no piso de sensibilidade clínica exigido para triagem / screening (S_min).
    """
    auc = metricas.get("auc", 0.0)
    mcc = metricas.get("mcc", 0.0)
    ece = metricas.get("ece", 0.0)
    sens = metricas.get("sensibilidade", 0.0)

    # Normaliza MCC de [-1, 1] para [0, 1]
    mcc_norm = max(0.0, (mcc + 1.0) / 2.0)
    # ECE é penalizado (menor é melhor)
    ece_penalty = min(1.0, max(0.0, ece))

    # Score base multiobjetivo
    score_base = (w_auc * auc) + (w_mcc * mcc_norm) - (w_ece * ece_penalty)

    # Penalidade por déficit de sensibilidade mínima
    deficit_sens = max(0.0, s_min - sens)
    penalidade = penalty_lambda * (deficit_sens ** 1.5)

    return float(score_base - penalidade)


def _ic95(valores: list[float]) -> list[float]:
    """Intervalo de confiança 95% (t-Student) da média das métricas por fold — T4."""
    v = np.asarray(valores, dtype=float)
    n = len(v)
    if n < 2:
        return [round(float(v.mean()), 4), round(float(v.mean()), 4)] if n else [0.0, 0.0]
    from scipy.stats import t as t_dist
    media = float(v.mean())
    erro = float(v.std(ddof=1) / np.sqrt(n))
    margem = float(t_dist.ppf(0.975, df=n - 1)) * erro
    return [round(media - margem, 4), round(media + margem, 4)]


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


def _shap_importancia(modelo, X_train: np.ndarray, X_test: np.ndarray,
                      feature_names: list[str] | None, nome_modelo: str) -> dict:
    """
    Importância global de features via SHAP para o modelo vencedor.
    Usa TreeExplainer para modelos de árvore e KernelExplainer (amostrado) como
    fallback. Falha de forma segura devolvendo {'disponivel': False}.
    """
    resultado = {"disponivel": False, "modelo": nome_modelo}
    n_feat = X_test.shape[1]
    nomes = feature_names if (feature_names and len(feature_names) == n_feat) \
        else [f"f{i}" for i in range(n_feat)]
    try:
        import shap

        if nome_modelo in ("RandomForest", "GradientBoosting"):
            explainer = shap.TreeExplainer(modelo)
            valores = explainer.shap_values(X_test)
            if isinstance(valores, list):          # binário → lista por classe
                valores = valores[1]
        else:
            fundo = shap.sample(X_train, min(50, len(X_train)), random_state=42)
            explainer = shap.KernelExplainer(lambda d: modelo.predict_proba(d)[:, 1], fundo)
            valores = explainer.shap_values(X_test[:min(30, len(X_test))], nsamples=100)

        importancia = np.abs(np.array(valores)).mean(axis=0).ravel()
        ranking = sorted(zip(nomes, importancia.tolist()), key=lambda kv: kv[1], reverse=True)
        resultado.update({
            "disponivel": True,
            "importancia_media_abs": {n: round(float(v), 5) for n, v in ranking},
            "top_features": [n for n, _ in ranking[:10]],
        })
    except Exception as e:
        resultado["motivo"] = str(e)
    return resultado
