#!/usr/bin/env python
"""
Converte reports/benchmark_artigo2/resultados.json nas linhas LaTeX das tabelas do
Artigo 2 e num resumo em Markdown. Nenhum número é digitado à mão.
"""
from __future__ import annotations

import json
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
RES = BASE / "reports" / "benchmark_artigo2" / "resultados.json"
OUT = BASE / "reports" / "benchmark_artigo2"

ROTULOS = {
    "01_Breast_Cancer_WBCD": ("Breast Cancer (WBCD)", "Tabular"),
    "02_BUSI_Breast_Ultrasound": ("BUSI Breast Ultrasound", "2D image"),
    "03_MITBIH_ECG_Arrhythmia": ("MIT-BIH ECG Arrhythmia", "1D signal"),
    "04_Stroke_Prediction": ("Stroke Prediction", "Tabular"),
    "05_PIMA_Diabetes": ("PIMA Diabetes", "Tabular"),
    "06_Brain_Tumor_MRI": ("Brain Tumor MRI", "2D image"),
    "07_COVID19_ChestXRay": ("COVID-19 Chest X-Ray", "2D image"),
    "08_Brain_MRI_Oncology": ("Brain MRI Oncology", "2D image"),
    "09_Heart_Disease_Cleveland": ("Heart Disease (Cleveland)", "Tabular"),
    "10_Parkinsons_Vocal": ("Parkinson Voice Biomarkers", "Tabular"),
}


def ms(m):
    return f"{m['media']:.3f} $\\pm$ {m['desvio']:.3f}"


def main():
    d = json.loads(RES.read_text(encoding="utf-8"))
    bases = [b for b in d["bases"] if "falha" not in b]
    linhas = []

    # ── Tabela I — benchmark principal
    t1 = []
    for i, b in enumerate(bases, 1):
        rot, mod = ROTULOS.get(b["nome"], (b["nome"], b["modalidade"]))
        m = b["modelos"][b["selecao_clinica"]]
        grp = "Yes" if b["agrupamento_por_sujeito"] else "No"
        t1.append(
            f"{i:02d} & {rot} & {mod} & {b['n_amostras']} & {b['n_features']} & "
            f"{b['selecao_clinica']} & {grp} & "
            f"{ms(m['auc'])} & {ms(m['sensibilidade'])} & {ms(m['especificidade'])} & "
            f"{ms(m['mcc'])} & {m['ece']['media']:.3f} \\\\"
        )
    linhas.append(("TABELA I - benchmark", "\n".join(t1)))

    # ── Tabela II — seleção convencional vs clínica
    t2 = []
    for b in bases:
        rot, _ = ROTULOS.get(b["nome"], (b["nome"], ""))
        c = b["modelos"][b["selecao_convencional"]]
        k = b["modelos"][b["selecao_clinica"]]
        div = "Yes" if b["selecao_divergente"] else "No"
        t2.append(
            f"{rot} & {b['selecao_convencional']} & {c['auc']['media']:.3f} & "
            f"{c['sensibilidade']['media']:.3f} & {c['mcc']['media']:.3f} & "
            f"{b['selecao_clinica']} & {k['auc']['media']:.3f} & "
            f"{k['sensibilidade']['media']:.3f} & {k['mcc']['media']:.3f} & {div} \\\\"
        )
    linhas.append(("TABELA II - selecao convencional vs clinica", "\n".join(t2)))

    # ── Tabela III — comparação pareada com o baseline nos mesmos folds
    t3 = []
    for b in bases:
        rot, _ = ROTULOS.get(b["nome"], (b["nome"], ""))
        k = b["modelos"][b["selecao_clinica"]]
        bl = b["baseline_logreg"]
        w = b["wilcoxon_clinico_vs_baseline_auc"]
        wm = b["wilcoxon_clinico_vs_baseline_mcc"]
        p = "n/a" if w.get("p") is None else f"{w['p']:.3f}"
        pm = "n/a" if wm.get("p") is None else f"{wm['p']:.3f}"
        t3.append(
            f"{rot} & {ms(bl['auc'])} & {ms(k['auc'])} & {p} & "
            f"{bl['mcc']['media']:.3f} & {k['mcc']['media']:.3f} & {pm} \\\\"
        )
    linhas.append(("TABELA III - baseline pareado (mesmos folds)", "\n".join(t3)))

    # ── Estudo de vazamento
    vaz = d["estudo_vazamento_parkinsons"]
    t4 = []
    for rot, chave in (("Record-level folds (leakage)", "sem_agrupamento"),
                       ("Subject-grouped folds", "agrupado_por_sujeito")):
        r = vaz[chave]
        m = r["modelos"][r["selecao_clinica"]]
        t4.append(
            f"{rot} & {r['selecao_clinica']} & {ms(m['auc'])} & {ms(m['sensibilidade'])} & "
            f"{ms(m['especificidade'])} & {ms(m['mcc'])} & {m['ece']['media']:.3f} \\\\"
        )
    linhas.append(("TABELA IV - vazamento por sujeito (Parkinsons)", "\n".join(t4)))

    # ── SHAP top features
    shap_txt = []
    for b in bases:
        rot, _ = ROTULOS.get(b["nome"], (b["nome"], ""))
        s = b.get("shap", {})
        top = s.get("top_features", [])[:3] if s.get("disponivel") else []
        shap_txt.append(f"- {rot}: {', '.join(top) if top else 'SHAP indisponivel'}"
                        f" (modelo {b['selecao_clinica']})")
    linhas.append(("SHAP top-3 por base", "\n".join(shap_txt)))

    # ── métricas agregadas úteis ao texto
    aucs = [b["modelos"][b["selecao_clinica"]]["auc"]["media"] for b in bases]
    sens = [b["modelos"][b["selecao_clinica"]]["sensibilidade"]["media"] for b in bases]
    eces = [b["modelos"][b["selecao_clinica"]]["ece"]["media"] for b in bases]
    div = [b["nome"] for b in bases if b["selecao_divergente"]]
    piso = [b["nome"] for b in bases
            if b["modelos"][b["selecao_clinica"]]["sensibilidade"]["media"] < 0.80]
    resumo = (
        f"n_bases = {len(bases)}\n"
        f"AUROC min/max = {min(aucs):.3f} / {max(aucs):.3f}\n"
        f"Sensibilidade min/max = {min(sens):.3f} / {max(sens):.3f}\n"
        f"ECE min/max = {min(eces):.3f} / {max(eces):.3f}\n"
        f"Bases com selecao divergente ({len(div)}): {div}\n"
        f"Bases em que nenhum modelo atinge S_min=0.80 ({len(piso)}): {piso}\n"
    )
    linhas.append(("RESUMO NUMERICO", resumo))

    texto = "\n\n".join(f"% ===== {t} =====\n{c}" for t, c in linhas)
    (OUT / "tabelas_latex.txt").write_text(texto, encoding="utf-8")
    print(texto)


if __name__ == "__main__":
    main()
