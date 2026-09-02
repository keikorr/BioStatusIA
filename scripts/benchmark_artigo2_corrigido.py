#!/usr/bin/env python
"""
Benchmark corrigido para o Artigo 2 (AutoML clinicamente orientado).

Diferenças em relação ao `executar_kaggle_reais.py`:
  * nada de valores de fallback fixos — se uma base não treinar, ela é marcada como falha;
  * validação cruzada real (5 folds) em vez de um único holdout 80/20;
  * agrupamento por sujeito (StratifiedGroupKFold) sempre que existir identificador;
  * colunas identificadoras (id, name, ...) removidas das features;
  * baselines executados nos MESMOS folds + Wilcoxon pareado;
  * seleção convencional (máx. AUROC) e seleção clínica multiobjetivo calculadas lado a lado.

Saídas: reports/benchmark_artigo2/resultados.json e resumo.md
"""
from __future__ import annotations

import json
import os
import sys
import time
import warnings
from pathlib import Path

import numpy as np

os.environ["PYTHONUTF8"] = "1"
os.environ["PYTHONIOENCODING"] = "utf-8"
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "src"))

from sklearn.base import clone
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score, cohen_kappa_score, confusion_matrix, f1_score,
    matthews_corrcoef, roc_auc_score,
)
from sklearn.model_selection import StratifiedGroupKFold, StratifiedKFold
from sklearn.neighbors import KNeighborsClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from scipy.stats import t as t_dist, wilcoxon

from biostatusia.pipeline.avaliacao_modelos import (
    balancear, calcular_score_clinico, _calibration_error, _shap_importancia,
)
from biostatusia.pipeline.analise_base import decidir_estrategia
from biostatusia.pipeline.extracao import extrair_todos

KAGGLE_DIR = BASE_DIR / "dataset_kaggle_reais"
CACHE = Path.home() / ".cache" / "kagglehub" / "datasets"
OUT_DIR = BASE_DIR / "reports" / "benchmark_artigo2"
OUT_DIR.mkdir(parents=True, exist_ok=True)

SEED = 42
N_FOLDS = 5
CAP_IMG_POR_CLASSE = 1000
CAP_LINHAS_TABULAR = 3000
CAP_LINHAS_SINAL = 1200

MODELOS = {
    "LogisticRegression": LogisticRegression(random_state=SEED, max_iter=2000),
    "KNN": KNeighborsClassifier(n_neighbors=5),
    "SVM": SVC(kernel="rbf", probability=True, random_state=SEED),
    "RandomForest": RandomForestClassifier(n_estimators=100, random_state=SEED),
    "GradientBoosting": GradientBoostingClassifier(n_estimators=100, random_state=SEED),
    "MLP": MLPClassifier(hidden_layer_sizes=(64, 32), max_iter=2000, random_state=SEED),
}

METRICAS = ("auc", "sensibilidade", "especificidade", "acuracia", "f1", "mcc", "kappa", "ece")


# ─────────────────────────────── utilidades ──────────────────────────────────

def ic95(v: list[float]) -> list[float]:
    a = np.asarray(v, float)
    if len(a) < 2:
        return [round(float(a.mean()), 4)] * 2 if len(a) else [0.0, 0.0]
    m = float(a.mean())
    err = float(a.std(ddof=1) / np.sqrt(len(a)))
    marg = float(t_dist.ppf(0.975, df=len(a) - 1)) * err
    return [round(m - marg, 4), round(m + marg, 4)]


def resumo(v: list[float]) -> dict:
    a = np.asarray(v, float)
    return {"media": round(float(a.mean()), 4),
            "desvio": round(float(a.std(ddof=1)) if len(a) > 1 else 0.0, 4),
            "ic95": ic95(v),
            "folds": [round(float(x), 4) for x in a]}


def metricas_fold(y_true, y_pred, y_prob) -> dict:
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    return {
        "auc": float(roc_auc_score(y_true, y_prob)) if len(set(y_true)) > 1 else 0.0,
        "sensibilidade": float(tp / (tp + fn + 1e-8)),
        "especificidade": float(tn / (tn + fp + 1e-8)),
        "acuracia": float(accuracy_score(y_true, y_pred)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
        "mcc": float(matthews_corrcoef(y_true, y_pred)),
        "kappa": float(cohen_kappa_score(y_true, y_pred)),
        "ece": float(_calibration_error(np.asarray(y_true), np.asarray(y_prob))),
    }


def gerar_folds(X, y, groups):
    if groups is not None:
        cv = StratifiedGroupKFold(n_splits=N_FOLDS, shuffle=True, random_state=SEED)
        return list(cv.split(X, y, groups)), "StratifiedGroupKFold (por sujeito)"
    cv = StratifiedKFold(n_splits=N_FOLDS, shuffle=True, random_state=SEED)
    return list(cv.split(X, y)), "StratifiedKFold (sem identificador de sujeito)"


# ─────────────────────────── núcleo da avaliação ─────────────────────────────

def rodar_cv(X, y, folds, balancear_treino=True) -> dict:
    """Treina os 6 modelos nos MESMOS folds. Escala e SMOTE só dentro do treino."""
    por_modelo = {n: {m: [] for m in METRICAS} for n in MODELOS}
    latencias = {n: [] for n in MODELOS}
    tempos = {n: [] for n in MODELOS}
    oof = {n: {"y": [], "prob": [], "pred": []} for n in MODELOS}

    for tr, va in folds:
        sc = StandardScaler().fit(X[tr])
        Xtr, Xva = sc.transform(X[tr]), sc.transform(X[va])
        ytr, yva = y[tr], y[va]
        if balancear_treino:
            Xtr, ytr, _ = balancear(Xtr, ytr, metodo="smote")

        for nome, base in MODELOS.items():
            m = clone(base)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                t0 = time.perf_counter()
                m.fit(Xtr, ytr)
                tempos[nome].append(time.perf_counter() - t0)
                t0 = time.perf_counter()
                yp = m.predict(Xva)
                latencias[nome].append((time.perf_counter() - t0) * 1000 / max(1, len(Xva)))
                ypr = m.predict_proba(Xva)[:, 1]
            for k, v in metricas_fold(yva, yp, ypr).items():
                por_modelo[nome][k].append(v)
            oof[nome]["y"] += yva.tolist()
            oof[nome]["prob"] += [round(float(v), 5) for v in ypr]
            oof[nome]["pred"] += [int(v) for v in yp]

    saida = {}
    for nome in MODELOS:
        r = {k: resumo(v) for k, v in por_modelo[nome].items()}
        r["latencia_ms"] = round(float(np.mean(latencias[nome])), 4)
        r["tempo_treino_s"] = round(float(np.mean(tempos[nome])), 3)
        medias = {k: r[k]["media"] for k in METRICAS}
        r["score_clinico"] = round(calcular_score_clinico(medias), 4)
        r["score_clinico_folds"] = [
            round(calcular_score_clinico({k: por_modelo[nome][k][i] for k in METRICAS}), 4)
            for i in range(len(folds))
        ]
        r["oof"] = oof[nome]
        saida[nome] = r
    return saida


def baseline_logreg(X, y, folds) -> dict:
    """Prática convencional: regressão logística padrão, sem balanceamento nem seleção."""
    acc = {m: [] for m in METRICAS}
    for tr, va in folds:
        sc = StandardScaler().fit(X[tr])
        m = LogisticRegression(random_state=SEED, max_iter=2000)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            m.fit(sc.transform(X[tr]), y[tr])
        Xva = sc.transform(X[va])
        for k, v in metricas_fold(y[va], m.predict(Xva), m.predict_proba(Xva)[:, 1]).items():
            acc[k].append(v)
    return {k: resumo(v) for k, v in acc.items()}


def wilcoxon_pareado(a: list[float], b: list[float]) -> dict:
    a, b = np.asarray(a, float), np.asarray(b, float)
    dif = a - b
    if len(a) < 3 or np.allclose(dif, 0):
        return {"p": None, "nota": "diferenças nulas ou n<3 — teste não aplicável"}
    try:
        stat, p = wilcoxon(a, b)
        return {"estatistica": round(float(stat), 4), "p": round(float(p), 4),
                "significativo": bool(p < 0.05), "delta_medio": round(float(dif.mean()), 4)}
    except Exception as e:  # pragma: no cover
        return {"p": None, "nota": str(e)}


def atribuicao_features(modelo, X_bal, y_bal, X, y, nomes, nome_modelo):
    """SHAP (TreeExplainer) para ensembles de árvore; importância por permutação para
    os demais — KernelExplainer é proibitivo em bases com centenas de features."""
    if nome_modelo in ("RandomForest", "GradientBoosting"):
        info = _shap_importancia(modelo, X_bal, X[:300], nomes, nome_modelo)
        info["metodo"] = "SHAP TreeExplainer"
        return info
    from sklearn.inspection import permutation_importance
    rng = np.random.default_rng(SEED)
    idx = rng.choice(len(X), min(400, len(X)), replace=False)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            r = permutation_importance(modelo, X[idx], y[idx], n_repeats=5,
                                       random_state=SEED, scoring="roc_auc")
        nomes_f = nomes if (nomes and len(nomes) == X.shape[1]) else [f"f{i}" for i in range(X.shape[1])]
        rank = sorted(zip(nomes_f, r.importances_mean.tolist()), key=lambda kv: kv[1], reverse=True)
        return {"disponivel": True, "modelo": nome_modelo,
                "metodo": "permutation importance (AUROC)",
                "importancia_media_abs": {n: round(float(v), 5) for n, v in rank},
                "top_features": [n for n, _ in rank[:10]]}
    except Exception as e:
        return {"disponivel": False, "modelo": nome_modelo, "motivo": str(e)}


def avaliar(nome_base, X, y, groups, feature_names, familia, fonte, modalidade, obs=""):
    folds, protocolo = gerar_folds(X, y, groups)
    print(f"    protocolo: {protocolo} | n={len(X)} | feats={X.shape[1]} | "
          f"classes={np.bincount(y).tolist()}")

    modelos = rodar_cv(X, y, folds)
    conv = max(modelos, key=lambda k: modelos[k]["auc"]["media"])
    clin = max(modelos, key=lambda k: modelos[k]["score_clinico"])
    base_lr = baseline_logreg(X, y, folds)

    # SHAP no vencedor clínico, treinado uma vez sobre toda a base escalada.
    sc = StandardScaler().fit(X)
    Xs = sc.transform(X)
    Xb, yb, _ = balancear(Xs, y, metodo="smote")
    venc = clone(MODELOS[clin])
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        venc.fit(Xb, yb)
    shap_info = atribuicao_features(venc, Xb, yb, Xs, y, feature_names, clin)

    return {
        "nome": nome_base,
        "familia": familia,
        "modalidade": modalidade,
        "fonte": fonte,
        "observacao": obs,
        "n_amostras": int(len(X)),
        "n_features": int(X.shape[1]),
        "distribuicao_classes": np.bincount(y).tolist(),
        "protocolo_cv": protocolo,
        "n_folds": N_FOLDS,
        "agrupamento_por_sujeito": groups is not None,
        "n_sujeitos": int(len(set(groups.tolist()))) if groups is not None else None,
        "modelos": modelos,
        "selecao_convencional": conv,
        "selecao_clinica": clin,
        "selecao_divergente": conv != clin,
        "baseline_logreg": base_lr,
        "wilcoxon_clinico_vs_convencional_auc": wilcoxon_pareado(
            modelos[clin]["auc"]["folds"], modelos[conv]["auc"]["folds"]),
        "wilcoxon_clinico_vs_convencional_sens": wilcoxon_pareado(
            modelos[clin]["sensibilidade"]["folds"], modelos[conv]["sensibilidade"]["folds"]),
        "wilcoxon_clinico_vs_baseline_auc": wilcoxon_pareado(
            modelos[clin]["auc"]["folds"], base_lr["auc"]["folds"]),
        "wilcoxon_clinico_vs_baseline_mcc": wilcoxon_pareado(
            modelos[clin]["mcc"]["folds"], base_lr["mcc"]["folds"]),
        "shap": shap_info,
    }


# ───────────────────────────── carregadores ──────────────────────────────────

import csv as _csv


def ler_csv(caminho: Path):
    with open(caminho, "r", encoding="utf-8", errors="replace", newline="") as f:
        amostra = f.read(8192)
        f.seek(0)
        try:
            dial = _csv.Sniffer().sniff(amostra, delimiters=",;\t|")
            sep = dial.delimiter
        except Exception:
            sep = ","
        linhas = list(_csv.reader(f, delimiter=sep))
    return linhas[0], linhas[1:]


ID_COLS = {"id", "name", "index", "unnamed: 0", "subject", "patient", "record"}


def tabular(caminho: Path, col_rotulo: str, mapa=None, drop=(), grupo_col=None,
            grupo_fn=None, cap=CAP_LINHAS_TABULAR):
    hdr, linhas = ler_csv(caminho)
    # colunas sem nome (vírgula final) são descartadas; linhas curtas são preenchidas
    validos = [i for i, c in enumerate(hdr) if c.strip() != ""]
    hdr = [hdr[i] for i in validos]
    linhas = [[(l[i] if i < len(l) else "") for i in validos] for l in linhas]
    idx_r = hdr.index(col_rotulo)
    grupos_raw = None
    if grupo_col is not None:
        gi = hdr.index(grupo_col)
        grupos_raw = [l[gi] for l in linhas]

    descartar = {i for i, c in enumerate(hdr)
                 if i == idx_r or c.strip().lower() in ID_COLS or c in drop}
    nomes = [c for i, c in enumerate(hdr) if i not in descartar]

    X, y, g = [], [], []
    for k, l in enumerate(linhas):
        if len(l) <= idx_r or not l[idx_r].strip():
            continue
        alvo = l[idx_r].strip()
        rot = mapa(alvo) if callable(mapa) else (mapa.get(alvo) if mapa else None)
        if rot is None:
            continue
        linha = []
        ok = True
        for i, v in enumerate(l):
            if i in descartar:
                continue
            v = v.strip()
            if v in ("", "?", "NA", "N/A", "nan"):
                linha.append(np.nan)
                continue
            try:
                linha.append(float(v))
            except ValueError:
                linha.append(float(abs(hash(v)) % 1000))  # categórica → código estável
                ok = ok
        X.append(linha)
        y.append(rot)
        if grupos_raw is not None:
            g.append(grupo_fn(grupos_raw[k]) if grupo_fn else grupos_raw[k])

    X = np.asarray(X, float)
    y = np.asarray(y, int)
    # imputação por mediana da coluna (calculada na base inteira; sem rótulo envolvido)
    for j in range(X.shape[1]):
        col = X[:, j]
        if np.isnan(col).any():
            col[np.isnan(col)] = np.nanmedian(col) if not np.isnan(col).all() else 0.0
            X[:, j] = col
    grupos = np.asarray(g) if g else None

    if len(X) > cap:
        rng = np.random.default_rng(SEED)
        idx = rng.choice(len(X), cap, replace=False)
        X, y = X[idx], y[idx]
        grupos = grupos[idx] if grupos is not None else None
    return X, y, grupos, nomes


CACHE_FEATS = OUT_DIR / "cache_features"
CACHE_FEATS.mkdir(parents=True, exist_ok=True)


def imagens(pares, cap=CAP_IMG_POR_CLASSE, chave: str = ""):
    """pares = [(pasta, rotulo)] ou [(pasta, rotulo, cap)]; extrai os 9 biomarcadores
    radiômicos (morfologia + GLCM + distribuição de intensidade) de cada imagem."""
    cache = CACHE_FEATS / f"{chave}.npz" if chave else None
    if cache is not None and cache.exists():
        d = np.load(cache, allow_pickle=True)
        return d["X"], d["y"], None, list(d["nomes"])

    est = decidir_estrategia({"ruido_medio": 0.04, "outliers_pct": 5.0,
                              "contraste_medio": 45, "tamanhos_heterogeneos": False})
    rng = np.random.default_rng(SEED)
    X, y, nomes = [], [], None
    for par in pares:
        pasta, rot = par[0], par[1]
        cap_local = par[2] if len(par) > 2 else cap
        arqs = sorted([p for p in pasta.rglob("*")
                       if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".bmp", ".tif"}
                       and "_mask" not in p.name.lower() and "mask" not in p.parent.name.lower()])
        if len(arqs) > cap_local:
            arqs = [arqs[i] for i in sorted(rng.choice(len(arqs), cap_local, replace=False))]
        for p in arqs:
            bio = extrair_todos(str(p), estrategia=est)
            if bio is None:
                continue
            d = {**bio["morfologia"], **bio["textura_glcm"], **bio["distribuicao_intensidade"]}
            if nomes is None:
                nomes = list(d.keys())
            X.append([d[k] for k in nomes])
            y.append(rot)
    X, y = np.asarray(X, float), np.asarray(y, int)
    if cache is not None:
        np.savez_compressed(cache, X=X, y=y, nomes=np.array(nomes, dtype=object))
    return X, y, None, nomes


# ───────────────────────────────── bases ─────────────────────────────────────

def busi():
    r = CACHE / "aryashah2k/breast-ultrasound-images-dataset/versions/1/Dataset_BUSI_with_GT"
    return imagens([(r / "benign", 0), (r / "malignant", 1)], chave="busi")


def brain_tumor():
    """notumor (0) vs. glioma/meningioma/pituitary (1); amostragem equilibrada."""
    r = CACHE / "masoudnickparvar/brain-tumor-mri-dataset/versions/2"
    pares = [(r / "Training/notumor", 0, 500)]
    for c in ("glioma", "meningioma", "pituitary"):
        pares.append((r / "Training" / c, 1, 167))
    return imagens(pares, chave="brain_tumor")


def covid_xray():
    r = CACHE / "tawsifurrahman/covid19-radiography-database/versions/5/COVID-19_Radiography_Dataset"
    return imagens([(r / "Normal/images", 0), (r / "COVID/images", 1)], chave="covid_xray")


def brain_onco():
    r = CACHE / "navoneel/brain-mri-images-for-brain-tumor-detection/versions/1/brain_tumor_dataset"
    return imagens([(r / "no", 0), (r / "yes", 1)], chave="brain_onco")


def wbcd():
    return tabular(KAGGLE_DIR / "01_Breast_Cancer_Wisconsin_Real/dataset.csv",
                   "diagnosis", {"B": 0, "M": 1})


def stroke():
    return tabular(KAGGLE_DIR / "04_Stroke_Prediction_Clinical_Real/dataset.csv",
                   "stroke", {"0": 0, "1": 1})


def pima():
    return tabular(KAGGLE_DIR / "05_PIMA_Diabetes_Metabolic_Real/dataset.csv",
                   "outcome", {"0": 0, "1": 1})


def cleveland():
    return tabular(KAGGLE_DIR / "09_Heart_Disease_Cleveland_Real/dataset.csv",
                   "num", lambda v: 0 if v.strip() in ("0", "0.0") else 1)


def parkinsons(agrupado=True):
    return tabular(KAGGLE_DIR / "10_Parkinsons_Vocal_Biomarkers_Real/dataset.csv",
                   "status", {"0": 0, "1": 1},
                   grupo_col="name" if agrupado else None,
                   grupo_fn=(lambda s: s.split("_")[2]) if agrupado else None)


def ecg_mitbih():
    """mitbih_train.csv: 187 amostras do batimento + rótulo multiclasse na última coluna.
    Binarizado em normal (0) vs arrítmico (1..4), como no benchmark original."""
    p = CACHE / "shayanfazeli/heartbeat/versions/1/mitbih_train.csv"
    rng = np.random.default_rng(SEED)
    X, y = [], []
    with open(p, "r") as f:
        for linha in f:
            vals = linha.strip().split(",")
            if len(vals) < 10:
                continue
            X.append([float(v) for v in vals[:-1]])
            y.append(0 if float(vals[-1]) == 0.0 else 1)
    X, y = np.asarray(X, float), np.asarray(y, int)
    if len(X) > CAP_LINHAS_SINAL:
        idx = rng.choice(len(X), CAP_LINHAS_SINAL, replace=False)
        X, y = X[idx], y[idx]
    return X, y, None, [f"amp_{i}" for i in range(X.shape[1])]


BASES = [
    ("01_Breast_Cancer_WBCD", wbcd, "Tabular", "Tabular",
     "Kaggle uciml/breast-cancer-wisconsin-data (UCI WBCD)",
     "Um registro por paciente — agrupamento por sujeito não se aplica."),
    ("02_BUSI_Breast_Ultrasound", busi, "Imagem 2D", "Ultrassom",
     "Kaggle aryashah2k/breast-ultrasound-images-dataset",
     "Sem identificador de paciente na redistribuição pública."),
    ("03_MITBIH_ECG_Arrhythmia", ecg_mitbih, "F1", "Sinal 1D",
     "Kaggle shayanfazeli/heartbeat (MIT-BIH, PhysioNet)",
     "O CSV redistribuído não preserva o identificador do registro/paciente."),
    ("04_Stroke_Prediction", stroke, "Tabular", "Tabular",
     "Kaggle fedesoriano/stroke-prediction-dataset",
     "Um registro por paciente."),
    ("05_PIMA_Diabetes", pima, "Tabular", "Tabular",
     "UCI Pima Indians Diabetes (mirror publico)",
     "Um registro por paciente."),
    ("06_Brain_Tumor_MRI", brain_tumor, "Imagem 2D", "RM (fatias)",
     "Kaggle masoudnickparvar/brain-tumor-mri-dataset",
     "Sem identificador de paciente na redistribuição pública."),
    ("07_COVID19_ChestXRay", covid_xray, "Imagem 2D", "Radiografia",
     "Kaggle tawsifurrahman/covid19-radiography-database",
     "Sem identificador de paciente na redistribuição pública."),
    ("08_Brain_MRI_Oncology", brain_onco, "Imagem 2D", "RM",
     "Kaggle navoneel/brain-mri-images-for-brain-tumor-detection",
     "Sem identificador de paciente na redistribuição pública."),
    ("09_Heart_Disease_Cleveland", cleveland, "Tabular", "Tabular",
     "UCI Heart Disease (Cleveland)",
     "Um registro por paciente."),
    ("10_Parkinsons_Vocal", parkinsons, "Tabular", "Sinal de voz (features)",
     "UCI Parkinsons (Little et al.)",
     "195 gravações de 31 sujeitos — identificador presente, folds agrupados por sujeito."),
]


def main():
    resultados = []
    for nome, carregar, familia, modalidade, fonte, obs in BASES:
        print(f"\n[{nome}] carregando...")
        t0 = time.time()
        try:
            X, y, g, feats = carregar()
        except Exception as e:
            print(f"    FALHA no carregamento: {type(e).__name__}: {e}")
            resultados.append({"nome": nome, "falha": f"{type(e).__name__}: {e}"})
            continue
        if len(X) < 30 or len(set(y.tolist())) < 2:
            print(f"    FALHA: {len(X)} amostras / {len(set(y.tolist()))} classes")
            resultados.append({"nome": nome, "falha": "amostras ou classes insuficientes"})
            continue
        print(f"    carregado em {time.time()-t0:.1f}s")
        r = avaliar(nome, X, y, g, feats, familia, fonte, modalidade, obs)
        print(f"    convencional={r['selecao_convencional']} | clinico={r['selecao_clinica']} | "
              f"AUROC={r['modelos'][r['selecao_clinica']]['auc']['media']:.4f} "
              f"Sens={r['modelos'][r['selecao_clinica']]['sensibilidade']['media']:.4f}")
        resultados.append(r)

    # Estudo de vazamento: Parkinsons com e sem agrupamento por sujeito.
    print("\n[ESTUDO DE VAZAMENTO] Parkinsons agrupado vs. não agrupado")
    vaz = {}
    for rotulo, agr in (("agrupado_por_sujeito", True), ("sem_agrupamento", False)):
        X, y, g, feats = parkinsons(agrupado=agr)
        r = avaliar(f"10_Parkinsons_{rotulo}", X, y, g, feats, "Tabular",
                    "UCI Parkinsons", "Sinal de voz (features)")
        vaz[rotulo] = r
    resultados_final = {"bases": resultados, "estudo_vazamento_parkinsons": vaz,
                        "config": {"seed": SEED, "n_folds": N_FOLDS,
                                   "cap_img_por_classe": CAP_IMG_POR_CLASSE,
                                   "cap_linhas_tabular": CAP_LINHAS_TABULAR,
                                   "gerado_em": time.strftime("%Y-%m-%d %H:%M:%S")}}

    with open(OUT_DIR / "resultados.json", "w", encoding="utf-8") as f:
        json.dump(resultados_final, f, ensure_ascii=False, indent=1)
    print(f"\nSalvo em {OUT_DIR/'resultados.json'}")


if __name__ == "__main__":
    main()
