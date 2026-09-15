#!/usr/bin/env python
"""
Figuras 2-5 do Artigo 2, geradas EXCLUSIVAMENTE a partir de
reports/benchmark_artigo2/resultados.json (nenhum valor sintético).

Todo texto das figuras está em inglês (pedido do revisor).
Saída: artigo-latex/figuras_artigo2/*.png e *.pdf (300 dpi).
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.metrics import roc_curve, auc as auc_score, confusion_matrix

os.environ["PYTHONUTF8"] = "1"

BASE = Path(__file__).resolve().parent.parent
RES = BASE / "reports" / "benchmark_artigo2" / "resultados.json"
OUT = [BASE / "figuras_artigo2", BASE / "reports" / "benchmark_artigo2" / "figuras"]
for d in OUT:
    d.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["DejaVu Serif", "Times New Roman"],
    "font.size": 10, "axes.labelsize": 10.5, "axes.titlesize": 11.5,
    "xtick.labelsize": 9, "ytick.labelsize": 9, "legend.fontsize": 8.5,
    "figure.dpi": 300, "savefig.dpi": 300, "savefig.bbox": "tight",
})

C = {"auroc": "#0f766e", "sens": "#2563eb", "spec": "#7c3aed", "mcc": "#d97706",
     "red": "#dc2626", "grey": "#64748b", "green": "#16a34a"}

ROTULOS = {
    "01_Breast_Cancer_WBCD": "Breast Cancer (WBCD)",
    "02_BUSI_Breast_Ultrasound": "Breast US (BUSI)",
    "03_MITBIH_ECG_Arrhythmia": "ECG Arrhythmia (MIT-BIH)",
    "04_Stroke_Prediction": "Stroke Prediction",
    "05_PIMA_Diabetes": "PIMA Diabetes",
    "06_Brain_Tumor_MRI": "Brain Tumor (MRI)",
    "07_COVID19_ChestXRay": "COVID-19 Chest X-Ray",
    "08_Brain_MRI_Oncology": "Brain MRI Oncology",
    "09_Heart_Disease_Cleveland": "Heart Disease (Cleveland)",
    "10_Parkinsons_Vocal": "Parkinson Voice (grouped)",
}

dados = json.loads(RES.read_text(encoding="utf-8"))
BASES = [b for b in dados["bases"] if "falha" not in b]
VAZ = dados["estudo_vazamento_parkinsons"]


def salvar(fig, nome):
    for d in OUT:
        fig.savefig(d / f"{nome}.png", dpi=300, bbox_inches="tight")
        fig.savefig(d / f"{nome}.pdf", bbox_inches="tight")
    plt.close(fig)
    print(f"  [ok] {nome}")


def sel(b):
    return b["modelos"][b["selecao_clinica"]]


def meia_largura_ic(m):
    lo, hi = m["ic95"]
    return max(0.0, (hi - lo) / 2.0)



# ── Fig. 1 — diagrama do pipeline ────────────────────────────────────────────
def figura1():
    import matplotlib.patches as mpatches

    fig, ax = plt.subplots(figsize=(11.0, 3.5))
    ax.set_xlim(0, 100); ax.set_ylim(0, 34); ax.axis("off")

    etapas = [
        ("STEP 1\nData ingestion",
         "10 real datasets\n(Kaggle + UCI)\ntabular | 2D image | 1D signal", C["auroc"]),
        ("STEP 2\nFeature extraction",
         "9 radiomic descriptors\n(morphology, GLCM,\nintensity) | 187-sample\nECG beat | clinical vars",
         C["sens"]),
        ("STEP 3\nLeak-free 5-fold CV",
         "StratifiedGroupKFold\nby subject when IDs exist;\nscaler + SMOTE fitted\ninside each fold",
         C["spec"]),
        ("STEP 4\nClinical selection",
         "6 classifiers scored on\nAUROC + MCC - ECE with\nsensitivity floor\n$S_{\\min}=0.80$", C["mcc"]),
    ]
    larg, gap = 21.0, 5.0
    for i, (titulo, corpo, cor) in enumerate(etapas):
        x = 1 + i * (larg + gap)
        ax.add_patch(mpatches.FancyBboxPatch(
            (x, 3), larg, 26, boxstyle="round,pad=0.4", linewidth=1.2,
            edgecolor=cor, facecolor=cor, alpha=0.10))
        ax.add_patch(mpatches.FancyBboxPatch(
            (x, 22.5), larg, 6.5, boxstyle="round,pad=0.4", linewidth=0,
            facecolor=cor, alpha=0.88))
        ax.text(x + larg / 2, 25.7, titulo, ha="center", va="center", color="white",
                fontsize=9.5, fontweight="bold", linespacing=1.4)
        ax.text(x + larg / 2, 12.5, corpo, ha="center", va="center", fontsize=8.2,
                linespacing=1.6)
        if i < len(etapas) - 1:
            ax.annotate("", xy=(x + larg + gap - 0.6, 16), xytext=(x + larg + 0.6, 16),
                        arrowprops=dict(arrowstyle="-|>", lw=1.6, color=C["grey"]))
    ax.text(50, 0.6,
            "Paired Wilcoxon comparison against a logistic-regression pipeline and FLAML "
            "on identical folds",
            ha="center", va="center", fontsize=8.4, style="italic", color=C["grey"])
    salvar(fig, "fig1_pipeline")


# ── Fig. 5 — ranking de biomarcadores ────────────────────────────────────────
def _importancias(b):
    return (b.get("shap") or {}).get("importancia_media_abs") or {}


def figura5():
    """(a) radiomica agregada nas 4 colecoes de imagem (mesmas features, mesmo estimador);
    (b) top-4 por base tabular/sinal, com importancia normalizada pelo maximo da base."""
    RADIOMICA = {
        "circularidade": "Circularity", "solidez": "Solidity", "contraste": "GLCM contrast",
        "homogeneidade": "GLCM homogeneity", "energia": "GLCM energy",
        "entropia": "GLCM entropy", "snr": "SNR", "assimetria": "Skewness",
        "curtose": "Kurtosis",
    }
    imagens = [b for b in BASES if set(_importancias(b)) >= set(RADIOMICA)]
    outras = [b for b in BASES if b not in imagens and _importancias(b)]

    acum = {k: [] for k in RADIOMICA}
    for b in imagens:
        imp = _importancias(b)
        topo = max(imp.values()) or 1.0
        for k in RADIOMICA:
            acum[k].append(imp[k] / topo)
    medias = {RADIOMICA[k]: (np.mean(v), np.std(v)) for k, v in acum.items()}
    ordem = sorted(medias, key=lambda k: medias[k][0])

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.4, 4.6))
    fig.subplots_adjust(wspace=0.55)
    y = np.arange(len(ordem))
    ax1.barh(y, [medias[k][0] for k in ordem], 0.62,
             xerr=[medias[k][1] for k in ordem], capsize=2.5,
             color=C["auroc"], alpha=0.9, edgecolor="black", linewidth=0.5,
             error_kw={"lw": 0.8})
    ax1.set_yticks(y); ax1.set_yticklabels(ordem)
    ax1.set_xlabel("Mean normalized |SHAP| value", fontweight="bold")
    ax1.set_title("(a) Radiomic descriptors, averaged over the\n"
                  f"{len(imagens)} image collections (TreeExplainer)", fontweight="bold")
    ax1.xaxis.grid(True, ls=":", alpha=0.6); ax1.set_axisbelow(True)

    rotulos, valores, cores = [], [], []
    paleta = [C["sens"], C["spec"], C["mcc"], C["red"], C["green"], C["grey"]]
    for i, b in enumerate(outras):
        imp = _importancias(b)
        topo = max(imp.values()) or 1.0
        for k, v in list(imp.items())[:4]:
            rotulos.append(f"{k.replace('_', ' ')}  ({ROTULOS.get(b['nome'], b['nome'])[:14]})")
            valores.append(v / topo)
            cores.append(paleta[i % len(paleta)])
    ordem2 = np.argsort(valores)
    y2 = np.arange(len(valores))
    ax2.barh(y2, [valores[i] for i in ordem2], 0.62,
             color=[cores[i] for i in ordem2], alpha=0.9, edgecolor="black", linewidth=0.4)
    ax2.set_yticks(y2)
    ax2.set_yticklabels([rotulos[i] for i in ordem2], fontsize=6.8)
    ax2.set_xlabel("Importance normalized within each dataset", fontweight="bold")
    ax2.set_title("(b) Top-ranked inputs of the tabular and\nsignal cohorts",
                  fontweight="bold")
    ax2.xaxis.grid(True, ls=":", alpha=0.6); ax2.set_axisbelow(True)

    fig.suptitle("Discriminative biomarkers of the clinically selected models",
                 fontweight="bold", y=1.02)
    salvar(fig, "fig5_ranking_biomarcadores")


# ── Fig. 2 — benchmark por base ───────────────────────────────────────────────
def figura2():
    nomes = [ROTULOS.get(b["nome"], b["nome"]) for b in BASES]
    series = [("auc", "AUROC", C["auroc"]),
              ("sensibilidade", "Sensitivity", C["sens"]),
              ("especificidade", "Specificity", C["spec"]),
              ("mcc", "MCC", C["mcc"])]
    y = np.arange(len(BASES))
    h = 0.20
    fig, ax = plt.subplots(figsize=(10.0, 6.4))
    for k, (chave, rot, cor) in enumerate(series):
        offs = (1.5 - k) * h
        vals = [sel(b)[chave]["media"] for b in BASES]
        errs = [meia_largura_ic(sel(b)[chave]) for b in BASES]
        ax.barh(y + offs, vals, h, xerr=errs, label=rot, color=cor, alpha=0.92,
                capsize=2.5, edgecolor="black", linewidth=0.4, error_kw={"lw": 0.8})
    ax.axvline(0.80, color=C["red"], ls="--", lw=1.3,
               label=r"Clinical sensitivity floor ($S_{\min}=0.80$)")
    ax.set_yticks(y)
    ax.set_yticklabels(nomes)
    ax.invert_yaxis()
    ax.set_xlim(-0.05, 1.05)
    ax.set_xlabel("5-fold cross-validation score (mean, error bars = 95% CI)", fontweight="bold")
    ax.set_title("Performance of the clinically selected model on ten real biomedical datasets",
                 fontweight="bold", pad=10)
    ax.xaxis.grid(True, ls=":", alpha=0.6)
    ax.set_axisbelow(True)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.09), ncol=5,
              framealpha=0.95, columnspacing=1.2, handlelength=1.6)
    salvar(fig, "fig2_benchmark_desempenho")


# ── Fig. 3 — ROC reais (OOF) + matriz de confusão real ───────────────────────
def dispersao_auc(b):
    v = [m["auc"]["media"] for m in b["modelos"].values()]
    return max(v) - min(v)


def figura3():
    alvo_roc = max(BASES, key=dispersao_auc)
    alvo_cm = next(b for b in BASES if b["nome"] == "07_COVID19_ChestXRay")

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.4, 4.9))
    fig.subplots_adjust(wspace=0.42)
    cores = ["#0f766e", "#2563eb", "#7c3aed", "#d97706", "#16a34a", "#64748b"]
    for cor, (nome, m) in zip(cores, alvo_roc["modelos"].items()):
        yt = np.array(m["oof"]["y"])
        yp = np.array(m["oof"]["prob"])
        fpr, tpr, _ = roc_curve(yt, yp)
        ax1.plot(fpr, tpr, lw=1.8, color=cor,
                 label=f"{nome} (AUROC = {auc_score(fpr, tpr):.3f})")
    ax1.plot([0, 1], [0, 1], "k:", lw=1, label="Random classifier (0.500)")
    ax1.set_xlim(-0.02, 1.0)
    ax1.set_ylim(0.0, 1.02)
    ax1.set_xlabel("False positive rate (1 - specificity)", fontweight="bold")
    ax1.set_ylabel("True positive rate (sensitivity)", fontweight="bold")
    ax1.set_title("(a) ROC, pooled out-of-fold predictions\n"
                  f"{ROTULOS.get(alvo_roc['nome'], alvo_roc['nome'])}", fontweight="bold")
    ax1.legend(loc="lower right", framealpha=0.9)
    ax1.grid(True, ls=":", alpha=0.6)

    m = alvo_cm["modelos"][alvo_cm["selecao_clinica"]]
    cm = confusion_matrix(np.array(m["oof"]["y"]), np.array(m["oof"]["pred"]), labels=[0, 1])
    cmn = 100 * cm / cm.sum(axis=1, keepdims=True)
    im = ax2.imshow(cmn, cmap="GnBu", vmin=0, vmax=100)
    cb = fig.colorbar(im, ax=ax2, fraction=0.046, pad=0.04)
    cb.set_label("Row-normalized (%)", fontweight="bold")
    classes = ["Negative\n(Normal)", "Positive\n(COVID-19)"]
    ax2.set_xticks([0, 1]); ax2.set_xticklabels(classes)
    ax2.set_yticks([0, 1]); ax2.set_yticklabels(classes)
    for i in range(2):
        for j in range(2):
            ax2.text(j, i, f"{cmn[i, j]:.1f}%\n(n={cm[i, j]})", ha="center", va="center",
                     color="white" if cmn[i, j] > 55 else "black", fontsize=10.5,
                     fontweight="bold")
    ax2.set_xlabel("Predicted label", fontweight="bold")
    ax2.set_ylabel("True label", fontweight="bold")
    ax2.set_title(f"(b) Out-of-fold confusion matrix - COVID-19 X-ray\n"
                  f"({alvo_cm['selecao_clinica']}, clinically selected)", fontweight="bold")
    fig.suptitle("Discriminative capacity and clinical error distribution "
                 "(measured, not simulated)", fontweight="bold", y=1.03)
    salvar(fig, "fig3_curvas_roc_matriz_confusao")


# ── Fig. 4 — calibração real ─────────────────────────────────────────────────
def _reliability(y, p, bins=10):
    b = np.linspace(0, 1, bins + 1)
    xs, ys = [], []
    for i in range(bins):
        m = (p >= b[i]) & (p < b[i + 1] if i < bins - 1 else p <= b[i + 1])
        if m.sum() > 0:
            xs.append(p[m].mean())
            ys.append(y[m].mean())
    return np.array(xs), np.array(ys)


def dispersao_ece(b):
    v = [m["ece"]["media"] for m in b["modelos"].values()]
    return max(v) - min(v)


def figura4():
    alvo = max(BASES, key=dispersao_ece)
    modelos = alvo["modelos"]
    melhor = min(modelos, key=lambda k: modelos[k]["ece"]["media"])
    pior = max(modelos, key=lambda k: modelos[k]["ece"]["media"])

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.0, 4.9))
    ax1.plot([0, 1], [0, 1], "k--", lw=1.4, label="Perfect calibration")
    for nome, cor, marca in ((melhor, C["auroc"], "s-"), (pior, C["red"], "o--")):
        y = np.array(modelos[nome]["oof"]["y"], float)
        p = np.array(modelos[nome]["oof"]["prob"], float)
        xs, ys = _reliability(y, p)
        ax1.plot(xs, ys, marca, color=cor, lw=1.9,
                 label=f"{nome} (ECE = {modelos[nome]['ece']['media']:.3f})")
    ax1.set_xlim(-0.02, 1.02); ax1.set_ylim(-0.02, 1.02)
    ax1.set_xlabel("Mean predicted probability", fontweight="bold")
    ax1.set_ylabel("Empirical fraction of positives", fontweight="bold")
    ax1.set_title(f"(a) Reliability diagram - {ROTULOS.get(alvo['nome'], alvo['nome'])}"
              f" (out-of-fold)", fontweight="bold")
    ax1.legend(loc="upper left", framealpha=0.9)
    ax1.grid(True, ls=":", alpha=0.6)

    nomes = [ROTULOS.get(b["nome"], b["nome"]) for b in BASES]
    ece = [sel(b)["ece"]["media"] for b in BASES]
    err = [meia_largura_ic(sel(b)["ece"]) for b in BASES]
    cores = [C["auroc"] if v < 0.10 else C["red"] for v in ece]
    x = np.arange(len(nomes))
    ax2.bar(x, ece, 0.6, yerr=err, color=cores, edgecolor="black", linewidth=0.5,
            capsize=2.5, error_kw={"lw": 0.8})
    ax2.axhline(0.10, color=C["red"], ls="--", lw=1.4,
                label="Operational threshold (ECE < 0.10), not a safety guarantee")
    ax2.set_xticks(x)
    ax2.set_xticklabels(nomes, rotation=35, ha="right")
    ax2.set_ylabel("Expected calibration error (ECE)", fontweight="bold")
    ax2.set_title("(b) Calibration of the selected model per dataset", fontweight="bold")
    ax2.legend(loc="upper left", framealpha=0.95)
    ax2.grid(True, axis="y", ls=":", alpha=0.6)
    fig.suptitle("Probability calibration measured on out-of-fold predictions",
                 fontweight="bold", y=1.0)
    salvar(fig, "fig4_analise_calibracao_ece")


# ── Fig. 5 — seleção clínica vs convencional + vazamento por sujeito ─────────
def figura6():
    def efeito(b):
        c = b["modelos"][b["selecao_convencional"]]
        k = b["modelos"][b["selecao_clinica"]]
        return max(abs(k[m]["media"] - c[m]["media"])
                   for m in ("auc", "sensibilidade", "especificidade", "mcc"))

    divergentes = [b for b in BASES if b["selecao_divergente"]]
    alvo = max(divergentes or BASES, key=efeito)
    conv = alvo["modelos"][alvo["selecao_convencional"]]
    clin = alvo["modelos"][alvo["selecao_clinica"]]

    fig = plt.figure(figsize=(11.6, 5.1))
    ax1 = fig.add_subplot(1, 2, 1, polar=True)
    ax2 = fig.add_subplot(1, 2, 2)

    cats = ["AUROC", "MCC\n(normalized)", "Sensitivity", "Specificity", "1 - ECE"]
    ang = [n / len(cats) * 2 * np.pi for n in range(len(cats))]
    ang += ang[:1]

    def perfil(m):
        v = [m["auc"]["media"], (m["mcc"]["media"] + 1) / 2, m["sensibilidade"]["media"],
             m["especificidade"]["media"], 1 - m["ece"]["media"]]
        return v + v[:1]

    ax1.set_theta_offset(np.pi / 2); ax1.set_theta_direction(-1)
    ax1.set_xticks(ang[:-1]); ax1.set_xticklabels(cats, size=8.5, fontweight="bold")
    ax1.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0]); ax1.set_ylim(0, 1.05)
    ax1.set_yticklabels(["0.2", "0.4", "0.6", "0.8", "1.0"], color=C["grey"], size=7.5)
    ax1.plot(ang, perfil(clin), lw=2.3, color=C["auroc"],
             label=f"Clinical objective: {alvo['selecao_clinica']}\n(score = {clin['score_clinico']:.3f})")
    ax1.fill(ang, perfil(clin), color=C["auroc"], alpha=0.22)
    ax1.plot(ang, perfil(conv), lw=2.0, ls="--", color=C["red"],
             label=f"Conventional (max AUROC): {alvo['selecao_convencional']}\n(score = {conv['score_clinico']:.3f})")
    ax1.fill(ang, perfil(conv), color=C["red"], alpha=0.13)
    ax1.set_title(f"(a) Metric profile - {ROTULOS.get(alvo['nome'], alvo['nome'])}",
                  fontweight="bold", pad=26)
    ax1.legend(loc="upper center", bbox_to_anchor=(0.5, -0.08), fontsize=7.8, framealpha=0.95)

    agr = VAZ["agrupado_por_sujeito"]
    livre = VAZ["sem_agrupamento"]
    ma = agr["modelos"][agr["selecao_clinica"]]
    ml = livre["modelos"][livre["selecao_clinica"]]
    metricas = [("auc", "AUROC"), ("sensibilidade", "Sensitivity"),
                ("especificidade", "Specificity"), ("mcc", "MCC")]
    x = np.arange(len(metricas)); w = 0.36
    v_livre = [ml[k]["media"] for k, _ in metricas]
    e_livre = [meia_largura_ic(ml[k]) for k, _ in metricas]
    v_agr = [ma[k]["media"] for k, _ in metricas]
    e_agr = [meia_largura_ic(ma[k]) for k, _ in metricas]
    ax2.bar(x - w / 2, v_livre, w, yerr=e_livre, capsize=3, color=C["red"], alpha=0.9,
            edgecolor="black", linewidth=0.5, label="Record-level folds (subject leakage)")
    ax2.bar(x + w / 2, v_agr, w, yerr=e_agr, capsize=3, color=C["auroc"], alpha=0.9,
            edgecolor="black", linewidth=0.5, label="Subject-grouped folds (leak-free)")
    for i in range(len(metricas)):
        ax2.text(x[i] - w / 2, v_livre[i] + 0.03, f"{v_livre[i]:.3f}", ha="center", fontsize=8)
        ax2.text(x[i] + w / 2, v_agr[i] + 0.03, f"{v_agr[i]:.3f}", ha="center", fontsize=8)
    ax2.set_xticks(x); ax2.set_xticklabels([r for _, r in metricas])
    ax2.set_ylim(0, 1.18)
    ax2.set_ylabel("5-fold score (mean, 95% CI)", fontweight="bold")
    ax2.set_title("(b) Subject-level leakage - UCI Parkinson voice\n"
                  "(195 recordings, 32 subjects)", fontweight="bold")
    ax2.legend(loc="lower left", framealpha=0.95)
    ax2.grid(True, axis="y", ls=":", alpha=0.6)

    fig.subplots_adjust(top=0.80)
    fig.suptitle("Clinically-oriented selection and the cost of ignoring subject grouping",
                 fontweight="bold", y=1.06)
    salvar(fig, "fig6_selecao_e_vazamento")


if __name__ == "__main__":
    print("Gerando figuras a partir de", RES)
    figura1(); figura2(); figura3(); figura4(); figura5(); figura6()
    print("Concluido.")
