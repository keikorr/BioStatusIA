#!/usr/bin/env python
"""
Baseline AutoML externo (FLAML) executado nos MESMOS folds do benchmark do Artigo 2.

Auto-Sklearn não instala em Windows (dependência de POSIX), então usamos FLAML,
um sistema AutoML publicado e amplamente citado, com orçamento de tempo fixo por fold.
O resultado é anexado a reports/benchmark_artigo2/resultados.json na chave
"baseline_flaml" de cada base, junto do Wilcoxon pareado contra o modelo escolhido
pela função clínica.
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
BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE / "scripts"))
sys.path.insert(0, str(BASE / "src"))

import benchmark_artigo2_corrigido as BM  # noqa: E402
from sklearn.preprocessing import StandardScaler  # noqa: E402

RES = BASE / "reports" / "benchmark_artigo2" / "resultados.json"
ORCAMENTO_S = float(os.environ.get("FLAML_BUDGET", "20"))

CARREGADORES = {
    "01_Breast_Cancer_WBCD": BM.wbcd,
    "02_BUSI_Breast_Ultrasound": BM.busi,
    "03_MITBIH_ECG_Arrhythmia": BM.ecg_mitbih,
    "04_Stroke_Prediction": BM.stroke,
    "05_PIMA_Diabetes": BM.pima,
    "06_Brain_Tumor_MRI": BM.brain_tumor,
    "07_COVID19_ChestXRay": BM.covid_xray,
    "08_Brain_MRI_Oncology": BM.brain_onco,
    "09_Heart_Disease_Cleveland": BM.cleveland,
    "10_Parkinsons_Vocal": BM.parkinsons,
}


def rodar_flaml(X, y, folds):
    from flaml import AutoML
    acc = {m: [] for m in BM.METRICAS}
    for tr, va in folds:
        sc = StandardScaler().fit(X[tr])
        automl = AutoML()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            automl.fit(sc.transform(X[tr]), y[tr], task="classification",
                       metric="roc_auc", time_budget=ORCAMENTO_S, verbose=0, seed=BM.SEED)
        Xva = sc.transform(X[va])
        prob = automl.predict_proba(Xva)[:, 1]
        pred = (prob >= 0.5).astype(int)
        for k, v in BM.metricas_fold(y[va], pred, prob).items():
            acc[k].append(v)
    return {k: BM.resumo(v) for k, v in acc.items()}


def main():
    dados = json.loads(RES.read_text(encoding="utf-8"))
    for base in dados["bases"]:
        nome = base.get("nome")
        if "falha" in base or nome not in CARREGADORES:
            continue
        print(f"[{nome}] FLAML ({ORCAMENTO_S:.0f}s/fold)...", flush=True)
        t0 = time.time()
        X, y, g, _ = CARREGADORES[nome]()
        folds, _ = BM.gerar_folds(X, y, g)
        try:
            r = rodar_flaml(X, y, folds)
        except Exception as e:
            print(f"    falha: {type(e).__name__}: {e}")
            base["baseline_flaml"] = {"falha": f"{type(e).__name__}: {e}"}
            continue
        clin = base["modelos"][base["selecao_clinica"]]
        base["baseline_flaml"] = r
        base["baseline_flaml_config"] = {"time_budget_s": ORCAMENTO_S, "metric": "roc_auc",
                                         "biblioteca": "flaml.AutoML"}
        base["wilcoxon_clinico_vs_flaml_auc"] = BM.wilcoxon_pareado(
            clin["auc"]["folds"], r["auc"]["folds"])
        base["wilcoxon_clinico_vs_flaml_mcc"] = BM.wilcoxon_pareado(
            clin["mcc"]["folds"], r["mcc"]["folds"])
        print(f"    FLAML AUROC={r['auc']['media']:.4f} vs BioStatusIA "
              f"{clin['auc']['media']:.4f} ({time.time()-t0:.0f}s)", flush=True)

    RES.write_text(json.dumps(dados, ensure_ascii=False, indent=1), encoding="utf-8")
    print("resultados.json atualizado com baseline FLAML")


if __name__ == "__main__":
    main()
