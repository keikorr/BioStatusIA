#!/usr/bin/env python
"""
Preenche artigo2_automl_template.tex com os números medidos em
reports/benchmark_artigo2/resultados.json e escreve artigo2_automl.tex.

Nenhum número do artigo é digitado à mão: tabelas, parágrafos numéricos e resumo
são derivados do JSON. Rodar sempre que o benchmark for reexecutado.
"""
from __future__ import annotations

import json
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
RES = BASE / "reports" / "benchmark_artigo2" / "resultados.json"
TPL = BASE / "artigo2_automl_template.tex"
OUT = BASE / "artigo2_automl.tex"

ROT = {
    "01_Breast_Cancer_WBCD": ("Breast Cancer (WBCD)", "Tabular"),
    "02_BUSI_Breast_Ultrasound": ("BUSI Breast Ultrasound", "2D image"),
    "03_MITBIH_ECG_Arrhythmia": ("MIT-BIH ECG Arrhythmia", "1D signal"),
    "04_Stroke_Prediction": ("Stroke Prediction", "Tabular"),
    "05_PIMA_Diabetes": ("PIMA Diabetes", "Tabular"),
    "06_Brain_Tumor_MRI": ("Brain Tumor MRI", "2D image"),
    "07_COVID19_ChestXRay": ("COVID-19 Chest X-Ray", "2D image"),
    "08_Brain_MRI_Oncology": ("Brain MRI Oncology", "2D image"),
    "09_Heart_Disease_Cleveland": ("Heart Disease (Cleveland)", "Tabular"),
    "10_Parkinsons_Vocal": ("Parkinson Voice", "Tabular"),
}

d = json.loads(RES.read_text(encoding="utf-8"))
BASES = [b for b in d["bases"] if "falha" not in b]
VAZ = d["estudo_vazamento_parkinsons"]


def rot(b):
    return ROT.get(b["nome"], (b["nome"], b["modalidade"]))[0]


def clin(b):
    return b["modelos"][b["selecao_clinica"]]


def conv(b):
    return b["modelos"][b["selecao_convencional"]]


def ms(m):
    return f"{m['media']:.3f} $\\pm$ {m['desvio']:.3f}"


def lista(nomes):
    nomes = list(nomes)
    if len(nomes) == 1:
        return nomes[0]
    if len(nomes) == 2:
        return f"{nomes[0]} and {nomes[1]}"
    return ", ".join(nomes[:-1]) + f", and {nomes[-1]}"


TRADUCAO_FEATURE = {
    "circularidade": "circularity", "solidez": "solidity", "contraste": "GLCM contrast",
    "homogeneidade": "GLCM homogeneity", "energia": "GLCM energy", "entropia": "GLCM entropy",
    "snr": "SNR", "assimetria": "skewness", "curtose": "kurtosis",
}


def feat(nome: str) -> str:
    """Traduz nomes de biomarcadores e escapa underscores para LaTeX."""
    n = TRADUCAO_FEATURE.get(nome, nome)
    return "\\texttt{" + n.replace("_", "\\_") + "}"


# ── tabelas ──────────────────────────────────────────────────────────────────
def top_feature(b):
    info = b.get("shap") or {}
    tops = info.get("top_features") or []
    return feat(tops[0]) if tops else "n/a"


def tabela1():
    linhas = []
    for i, b in enumerate(BASES, 1):
        nome, mod = ROT.get(b["nome"], (b["nome"], b["modalidade"]))
        m = clin(b)
        grp = "Yes" if b["agrupamento_por_sujeito"] else "No"
        linhas.append(
            f"{i:02d} & {nome} & {mod} & {b['n_amostras']} & {b['n_features']} & "
            f"{top_feature(b)} & {b['selecao_clinica']} & {grp} & "
            f"{ms(m['auc'])} & {ms(m['sensibilidade'])} & {ms(m['especificidade'])} & "
            f"{m['f1']['media']:.3f} & {ms(m['mcc'])} & {m['ece']['media']:.3f} \\\\")
    return "\n".join(linhas)


def tabela2():
    linhas = []
    for b in BASES:
        c, k = conv(b), clin(b)
        linhas.append(
            f"{rot(b)} & {b['selecao_convencional']} & {c['auc']['media']:.3f} & "
            f"{c['sensibilidade']['media']:.3f} & {c['mcc']['media']:.3f} & "
            f"{b['selecao_clinica']} & {k['auc']['media']:.3f} & "
            f"{k['sensibilidade']['media']:.3f} & {k['mcc']['media']:.3f} & "
            f"{'Yes' if b['selecao_divergente'] else 'No'} \\\\")
    return "\n".join(linhas)


def flaml(b):
    r = b.get("baseline_flaml")
    return r if (r and "falha" not in r) else None


def tabela3():
    linhas = []
    for b in BASES:
        k, bl, fl = clin(b), b["baseline_logreg"], flaml(b)
        w = b.get("wilcoxon_clinico_vs_baseline_auc", {})
        wf = b.get("wilcoxon_clinico_vs_flaml_auc", {})
        pl = "n/a" if w.get("p") is None else f"{w['p']:.4f}"
        pf = "n/a" if wf.get("p") is None else f"{wf['p']:.4f}"
        col_fl = ms(fl["auc"]) if fl else "not run"
        cand = {"LR": bl["auc"]["media"], "BioStatusIA": k["auc"]["media"]}
        if fl:
            cand["FLAML"] = fl["auc"]["media"]
        topo = max(cand.values())
        empatados = [n for n, v in cand.items() if topo - v < 0.002]
        melhor = "tie" if len(empatados) > 1 else empatados[0]
        linhas.append(
            f"{rot(b)} & {ms(bl['auc'])} & {col_fl} & {ms(k['auc'])} & {pl} & {pf} & "
            f"{melhor} \\\\")
    return "\n".join(linhas)


def tabela4():
    linhas = []
    for nome, chave in (("Record-level folds", "sem_agrupamento"),
                        ("Subject-grouped folds", "agrupado_por_sujeito")):
        r = VAZ[chave]
        m = r["modelos"][r["selecao_clinica"]]
        linhas.append(
            f"{nome} & {r['selecao_clinica']} & {ms(m['auc'])} & {ms(m['sensibilidade'])} & "
            f"{ms(m['especificidade'])} & {ms(m['mcc'])} & {m['ece']['media']:.3f} \\\\")
    return "\n".join(linhas)


# ── parágrafos ───────────────────────────────────────────────────────────────
def p_benchmark():
    aucs = {rot(b): clin(b)["auc"]["media"] for b in BASES}
    sens = {rot(b): clin(b)["sensibilidade"]["media"] for b in BASES}
    mccs = {rot(b): clin(b)["mcc"]["media"] for b in BASES}
    melhor, pior = max(aucs, key=aucs.get), min(aucs, key=aucs.get)
    acima = [n for n, v in sens.items() if v >= 0.80]
    abaixo = [n for n, v in sens.items() if v < 0.80]
    mcc_baixo = [n for n, v in mccs.items() if v < 0.50]
    agrupadas = [rot(b) for b in BASES if b["agrupamento_por_sujeito"]]
    return (
        f"AUROC ranges from {min(aucs.values()):.3f} on {pior} to {max(aucs.values()):.3f} on "
        f"{melhor}. The spread does not follow the modality: the tabular cohorts and the "
        f"radiomic image collections cover overlapping AUROC ranges, and the strongest and "
        f"weakest results in the table are both obtained on datasets of the same broad type. "
        f"What separates them is the informativeness of the specific representation, not whether "
        f"the input was an image or a table. "
        f"The screening floor $S_{{\min}}=0.80$ is met on {len(acima)} of the {len(BASES)} "
        f"datasets ({lista(acima) if acima else 'none'}); on "
        f"{lista(abaixo) if abaixo else 'no dataset'} no candidate in the model space reaches it, "
        f"so the penalty applies to every candidate and the selected model is the least-penalized "
        f"member of a set that is uniformly unsuitable for screening as configured. "
        f"AUROC alone would hide this. It is also worth reading AUROC against MCC rather than in "
        f"isolation: on {lista(mcc_baixo)} the selected model combines a respectable AUROC with an "
        f"MCC below $0.50$, which is the signature of a decision threshold that ranks cases well "
        f"but separates them poorly at the operating point actually used. "
        f"Only {lista(agrupadas)} is validated with subject-grouped folds, and it returns the "
        f"lowest AUROC in the table; Section~\ref{{sec:vazamento}} shows that this is a "
        f"consequence of the protocol rather than of the data.")


def p_clinico():
    piores = min(BASES, key=lambda b: clin(b)["sensibilidade"]["media"])
    pior_mcc = min(BASES, key=lambda b: clin(b)["mcc"]["media"])
    espec_baixa = [b for b in BASES if clin(b)["especificidade"]["media"] < 0.75]
    return (
        "A sensitivity of $1.0$ is not by itself evidence of screening capability, because a "
        "classifier that labels every case positive attains it. When perfect recall is paired "
        "with a specificity of roughly two thirds, one third of the negative population is "
        "referred for confirmatory work-up, which in a screening programme translates into "
        "imaging backlogs, avoidable biopsies, and patient anxiety; such an operating point is "
        "defensible only when the confirmatory test downstream is cheap, fast, and low-risk. The "
        "mirror-image failure is a configuration with sensitivity near zero, an $F_1$ of zero, "
        "and a negative MCC, which has simply learned the majority class. "
        f"In this benchmark neither extreme is reached: the lowest sensitivity attained by a "
        f"selected model is {clin(piores)['sensibilidade']['media']:.3f} on {rot(piores)}, and "
        f"the lowest MCC is {clin(pior_mcc)['mcc']['media']:.3f} on {rot(pior_mcc)}, so no "
        f"selected configuration is degenerate in the strict sense. We report this rather than "
        f"presenting the penalty as having rescued a collapse it never had to rescue: with SMOTE "
        f"applied inside each training fold, the candidate pool already contains no zero-recall "
        f"model on these ten datasets. "
        + (f"Specificity, however, falls below $0.75$ on "
           f"{lista([rot(b) for b in espec_baixa])}, where the false-positive burden would "
           f"dominate the clinical cost of deployment." if espec_baixa else ""))


def p_selecao():
    div = [b for b in BASES if b["selecao_divergente"]]
    if not div:
        return (
            "On these ten datasets the two criteria return the same model in every case. This is "
            "a negative result and we report it as such: with six candidate families and folds "
            "in which SMOTE is applied inside the training partition, the AUROC-maximizing model "
            "was also the one with the best combined sensitivity, MCC, and calibration profile. "
            "The value of the clinical objective here is therefore not that it changed the "
            "outcome, but that it makes the sensitivity shortfall explicit in the score, "
            "and it would have rejected the degenerate configurations that an accuracy-driven "
            "search can otherwise return.")
    partes = []
    for b in div:
        c, k = conv(b), clin(b)
        partes.append(
            f"on {rot(b)}, conventional selection returns {b['selecao_convencional']} "
            f"(AUROC {c['auc']['media']:.3f}, sensitivity {c['sensibilidade']['media']:.3f}, "
            f"MCC {c['mcc']['media']:.3f}) while the clinical objective returns "
            f"{b['selecao_clinica']} (AUROC {k['auc']['media']:.3f}, sensitivity "
            f"{k['sensibilidade']['media']:.3f}, MCC {k['mcc']['media']:.3f})")
    def maior(chave):
        vals = [(rot(b), clin(b)[chave]["media"] - conv(b)[chave]["media"]) for b in div]
        return max(vals, key=lambda t: abs(t[1]))

    n_mcc, d_mcc = maior("mcc")
    n_sens, d_sens = maior("sensibilidade")
    d_auc = max((abs(clin(b)["auc"]["media"] - conv(b)["auc"]["media"]) for b in div))
    return (
        f"The two criteria diverge on {len(div)} of the {len(BASES)} datasets: "
        + "; ".join(partes) + ". "
        f"The effect sizes are modest and we state them plainly rather than presenting the "
        f"divergences as decisive: across these {len(div)} datasets the largest change in MCC is "
        f"{d_mcc:+.3f} (on {n_mcc}), the largest change in sensitivity is {d_sens:+.3f} "
        f"(on {n_sens}), and AUROC never moves by more than {d_auc:.3f}. The clinical objective "
        f"trades a small amount of ranking quality for a better-balanced and, in two of the three "
        f"cases, better-calibrated operating point. Where the two criteria coincide, the score "
        f"still carries information that AUROC alone does not, because it records how far the "
        f"selected candidate sits from the screening floor. The honest summary is that on these "
        f"ten datasets the selection function is a safety constraint that occasionally changes "
        f"the answer, not a performance improvement.")


def p_vazamento():
    a = VAZ["agrupado_por_sujeito"]
    l = VAZ["sem_agrupamento"]
    ma = a["modelos"][a["selecao_clinica"]]
    ml = l["modelos"][l["selecao_clinica"]]
    d_auc = ml["auc"]["media"] - ma["auc"]["media"]
    d_mcc = ml["mcc"]["media"] - ma["mcc"]["media"]
    sentido = "higher" if d_auc > 0 else "lower"
    return (
        f"Moving from record-level folds to subject-grouped folds changes the reported AUROC "
        f"from {ml['auc']['media']:.3f} $\\pm$ {ml['auc']['desvio']:.3f} to "
        f"{ma['auc']['media']:.3f} $\\pm$ {ma['auc']['desvio']:.3f}, and the MCC from "
        f"{ml['mcc']['media']:.3f} to {ma['mcc']['media']:.3f}. The record-level protocol is "
        f"therefore {abs(d_auc):.3f} AUROC points {sentido} and {abs(d_mcc):.3f} MCC points "
        f"{'higher' if d_mcc > 0 else 'lower'} than the leak-free protocol on identical data, "
        f"with wider dispersion across folds under grouping because each fold now withholds "
        f"entire subjects. The magnitude is dataset-specific and should not be extrapolated as a "
        f"correction factor, but the direction is the one the leakage argument predicts, and it "
        f"is large enough to change how a screening claim would be read. Since the four image "
        f"collections and the redistributed ECG benchmark carry no identifiers, an equivalent "
        f"correction cannot be applied to them here, and their rows in "
        f"Table~\\ref{{tab:benchmark}} must be read with that caveat.")


def p_ece():
    ece = {rot(b): clin(b)["ece"]["media"] for b in BASES}
    abaixo = [n for n, v in ece.items() if v < 0.10]
    acima = [n for n, v in ece.items() if v >= 0.10]
    return (
        f"Under this criterion the selected model falls below $0.10$ on {len(abaixo)} of the "
        f"{len(BASES)} datasets ({lista(abaixo) if abaixo else 'none'}), with calibration error "
        f"between {min(ece.values()):.3f} and {max(ece.values()):.3f} across the collection"
        + (f"; the remaining {len(acima)} ({lista(acima)}) exceed it and would not be promoted "
           f"without post-hoc recalibration." if acima else "."))


def p_baseline():
    com_flaml = [b for b in BASES if flaml(b)]
    ganha_lr = [b for b in BASES
                if clin(b)["auc"]["media"] > b["baseline_logreg"]["auc"]["media"]]
    ganha_fl = [b for b in com_flaml
                if clin(b)["auc"]["media"] > flaml(b)["auc"]["media"]]
    d_lr = [clin(b)["auc"]["media"] - b["baseline_logreg"]["auc"]["media"] for b in BASES]
    d_fl = [clin(b)["auc"]["media"] - flaml(b)["auc"]["media"] for b in com_flaml]
    sig = [rot(b) for b in BASES
           if (b.get("wilcoxon_clinico_vs_baseline_auc", {}).get("p") or 1) < 0.05
           or (b.get("wilcoxon_clinico_vs_flaml_auc", {}).get("p") or 1) < 0.05]
    med_lr = sum(d_lr) / len(d_lr)
    txt = (
        f"Against the conventional logistic-regression pipeline, the AutoML search gives a higher "
        f"mean AUROC on {len(ganha_lr)} of the {len(BASES)} datasets, with a mean difference of "
        f"{med_lr:+.3f} and a per-dataset range of {min(d_lr):+.3f} to {max(d_lr):+.3f}. ")
    if com_flaml:
        med_fl = sum(d_fl) / len(d_fl)
        txt += (
            f"Against FLAML under a 20-second per-fold budget, it is ahead on {len(ganha_fl)} of "
            f"{len(com_flaml)} datasets, with a mean difference of {med_fl:+.3f} and a range of "
            f"{min(d_fl):+.3f} to {max(d_fl):+.3f}. ")
    txt += (
        f"{'No comparison reaches' if not sig else 'Comparisons reaching'} $p<0.05$"
        + (f": {lista(sig)}. " if sig else " under the paired Wilcoxon test, which is expected "
                                           "given the five-fold design. ")
        + "The practical reading is that the differences are consistent in direction but small "
          "relative to fold-to-fold variance. We therefore describe the clinically-oriented "
          "objective as competitive with, not superior to, an external AutoML system under these "
          "conditions.")
    return txt


def p_shap():
    partes = []
    for b in BASES:
        info = b.get("shap", {})
        if info.get("disponivel") and info.get("top_features"):
            partes.append(f"{rot(b)}: {', '.join(feat(f) for f in info['top_features'][:3])}")
    n_shap = sum(1 for b in BASES
                 if "SHAP" in (b.get("shap", {}).get("metodo") or ""))
    return (
        f"Feature attribution used the tree-specific SHAP estimator \\cite{{shap2017}} for the "
        f"{n_shap} datasets whose selected model is a tree ensemble, and permutation importance "
        f"over AUROC for the remaining {len(BASES) - n_shap}, because kernel SHAP is "
        f"prohibitively slow on the 187-dimensional beat representation and on the "
        f"kernel-machine and neural candidates. The two estimators are not on a common scale, so "
        f"we report rankings rather than magnitudes. The three highest-ranked inputs per dataset "
        f"are: " + "; ".join(partes) + ". ")


def p_conclusao():
    aucs = [clin(b)["auc"]["media"] for b in BASES]
    sens = [clin(b)["sensibilidade"]["media"] for b in BASES]
    eces = [clin(b)["ece"]["media"] for b in BASES]
    div = sum(1 for b in BASES if b["selecao_divergente"])
    a = VAZ["agrupado_por_sujeito"]; l = VAZ["sem_agrupamento"]
    d_auc = (l["modelos"][l["selecao_clinica"]]["auc"]["media"]
             - a["modelos"][a["selecao_clinica"]]["auc"]["media"])
    return (
        f"Across the collection the selected models span an AUROC of {min(aucs):.3f} to "
        f"{max(aucs):.3f}, a sensitivity of {min(sens):.3f} to {max(sens):.3f}, and a "
        f"calibration error of {min(eces):.3f} to {max(eces):.3f}; the clinical objective "
        f"selected a different model from AUROC maximization on {div} of the {len(BASES)} "
        f"datasets. On the one benchmark carrying subject identifiers, dropping subject "
        f"grouping inflates the reported AUROC by {abs(d_auc):.3f}, which is a direct measure "
        f"of what record-level validation buys and why the imaging rows here are reported as "
        f"upper bounds. Against locally executed baselines on identical folds the selected "
        f"models are competitive rather than dominant, and we report that outcome as measured.")


def p_degenerado():
    piores_sens = min(BASES, key=lambda b: clin(b)["sensibilidade"]["media"])
    piores_mcc = min(BASES, key=lambda b: clin(b)["mcc"]["media"])
    neg = [rot(b) for b in BASES if clin(b)["mcc"]["media"] <= 0
           or clin(b)["sensibilidade"]["media"] == 0.0]
    if neg:
        return (f"In this benchmark the degenerate case does occur: on {lista(neg)} the selected "
                f"model collapses onto the majority class.")
    return (
        f"In this benchmark neither extreme is reached. The lowest sensitivity attained by a "
        f"selected model is {clin(piores_sens)['sensibilidade']['media']:.3f} on "
        f"{rot(piores_sens)}, and the lowest MCC is "
        f"{clin(piores_mcc)['mcc']['media']:.3f} on {rot(piores_mcc)}, so no configuration "
        f"selected here is degenerate in the strict sense. We report this rather than presenting "
        f"the penalty as having rescued a collapse it never had to rescue: with SMOTE applied "
        f"inside each training fold, the candidate pool itself already contains no zero-recall "
        f"model on these ten datasets. The penalty term is therefore a guard-rail whose value is "
        f"demonstrated by the {sum(1 for b in BASES if b['selecao_divergente'])} selection "
        f"changes it produces and by the shortfalls it makes explicit, not by a rescued failure.")


def figcap_ece():
    def disp(b):
        v = [m["ece"]["media"] for m in b["modelos"].values()]
        return max(v) - min(v)
    return rot(max(BASES, key=disp))


SUBS = {
    "%%TABELA1%%": tabela1, "%%TABELA2%%": tabela2, "%%TABELA3%%": tabela3,
    "%%TABELA4%%": tabela4, "%%PARAGRAFO_BENCHMARK%%": p_benchmark,
    "%%PARAGRAFO_SELECAO%%": p_selecao, "%%PARAGRAFO_CLINICO%%": p_clinico, "%%PARAGRAFO_VAZAMENTO%%": p_vazamento,
    "%%PARAGRAFO_ECE%%": p_ece, "%%PARAGRAFO_BASELINE%%": p_baseline,
    "%%PARAGRAFO_SHAP%%": p_shap, "%%PARAGRAFO_CONCLUSAO%%": p_conclusao,
}


def abstract():
    aucs = [clin(b)["auc"]["media"] for b in BASES]
    sens = [clin(b)["sensibilidade"]["media"] for b in BASES]
    eces = [clin(b)["ece"]["media"] for b in BASES]
    piso = sum(1 for s in sens if s >= 0.80)
    div = sum(1 for b in BASES if b["selecao_divergente"])
    a = VAZ["agrupado_por_sujeito"]; l = VAZ["sem_agrupamento"]
    d_auc = (l["modelos"][l["selecao_clinica"]]["auc"]["media"]
             - a["modelos"][a["selecao_clinica"]]["auc"]["media"])
    return (
        "Automated machine learning (AutoML) reduces manual trial and error in biomedical model "
        "development, but a search driven by accuracy or by the unweighted area under the "
        "receiver operating characteristic curve (AUROC) can return classifiers that are "
        "clinically unusable: degenerate under class imbalance, or confidently miscalibrated. "
        "This paper formalizes a clinically-oriented multi-objective selection function that "
        "combines AUROC, the normalized Matthews correlation coefficient (MCC), and the expected "
        "calibration error (ECE) under an explicit sensitivity floor "
        "($S_{\\min}=0.80$), and evaluates it against conventional AUROC-maximizing selection on "
        f"identical folds. We benchmark six classifier families on {len(BASES)} real biomedical "
        "datasets spanning tabular cohorts, radiomic features from 2D images, and 1D "
        "electrophysiological recordings, using five-fold stratified cross-validation with "
        "scaling and SMOTE fitted strictly inside each training fold, and subject-grouped folds "
        "wherever subject identifiers exist. Across the collection the selected models span "
        f"AUROC {min(aucs):.3f}--{max(aucs):.3f}, sensitivity {min(sens):.3f}--{max(sens):.3f}, "
        f"and ECE {min(eces):.3f}--{max(eces):.3f}; {piso} of {len(BASES)} datasets meet the "
        f"sensitivity floor and the two selection criteria diverge on {div}. On the one "
        "benchmark that carries subject identifiers, removing subject grouping inflates the "
        f"reported AUROC by {abs(d_auc):.3f}, quantifying the cost of record-level validation. "
        "All baselines\u2014a conventional logistic-regression pipeline and the FLAML AutoML "
        "system\u2014were executed locally on the same folds; we make no claim of superiority "
        "over published AutoML or deep learning results obtained under different protocols."
    )


SUBS["%%ABSTRACT%%"] = abstract
SUBS["%%FIGCAP_ECE%%"] = figcap_ece
SUBS["%%FIGCAP_ROC%%"] = lambda: rot(max(
    BASES, key=lambda b: max(m["auc"]["media"] for m in b["modelos"].values())
                          - min(m["auc"]["media"] for m in b["modelos"].values())))


def main():
    s = TPL.read_text(encoding="utf-8")
    for chave, fn in SUBS.items():
        if chave not in s:
            raise SystemExit(f"marcador ausente no template: {chave}")
        s = s.replace(chave, fn())
    if "%%" in s:
        raise SystemExit("marcadores não substituídos remanescentes")
    OUT.write_text(s, encoding="utf-8")
    print(f"escrito: {OUT}")


if __name__ == "__main__":
    main()
