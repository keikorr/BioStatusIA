#!/usr/bin/env python
"""
Recalcula apenas a atribuição de features (SHAP / importância por permutação) de cada base
e regrava reports/benchmark_artigo2/resultados.json.

Necessário depois da correção do desalinhamento de nomes no `_shap_importancia`
(shap>=0.45 devolve (n, features, classes) e o ravel() misturava as colunas).
Não refaz a validação cruzada — as métricas permanecem exatamente as mesmas.
"""
from __future__ import annotations

import json
import os
import sys
import warnings
from pathlib import Path

import numpy as np

os.environ["PYTHONUTF8"] = "1"
BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE / "scripts"))
sys.path.insert(0, str(BASE / "src"))

import benchmark_artigo2_corrigido as BM  # noqa: E402
from sklearn.base import clone  # noqa: E402
from sklearn.preprocessing import StandardScaler  # noqa: E402

RES = BASE / "reports" / "benchmark_artigo2" / "resultados.json"

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


def main():
    dados = json.loads(RES.read_text(encoding="utf-8"))
    for base in dados["bases"]:
        nome = base.get("nome")
        if "falha" in base or nome not in CARREGADORES:
            continue
        X, y, _, feats = CARREGADORES[nome]()
        sc = StandardScaler().fit(X)
        Xs = sc.transform(X)
        Xb, yb, _ = BM.balancear(Xs, y, metodo="smote")
        modelo = clone(BM.MODELOS[base["selecao_clinica"]])
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            modelo.fit(Xb, yb)
        info = BM.atribuicao_features(modelo, Xb, yb, Xs, y, feats, base["selecao_clinica"])
        base["shap"] = info
        top = ", ".join(info.get("top_features", [])[:3]) or "indisponível"
        print(f"{nome:30s} {info.get('metodo', '?'):32s} {top}", flush=True)

    RES.write_text(json.dumps(dados, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\nresultados.json regravado (apenas o bloco de atribuição mudou).")


if __name__ == "__main__":
    main()
