#!/usr/bin/env python3
"""
03_calibration_oof.py
------------------------------------------------------------------------------
Tier D of the BioStatusIA audit: calibration analysis wherever per-sample
probability outputs exist.

The eight audited execution reports contain no per-sample probabilities, so
their calibration cannot be re-estimated beyond the single ECE they report.
The only probability outputs in either repository are the out-of-fold (OOF)
predictions stored by the lineage benchmark
(keikorr/BioStatusIA @ atualizacao_features, reports/benchmark_artigo2/resultados.json,
produced by scripts/benchmark_artigo2_corrigido.py on 2026-08-30).
That benchmark is a DIFFERENT execution: 5-fold CV instead of an 80/20 split,
capped sample sizes, identifier columns removed, binary task definitions for
BUSI (benign vs malignant, normal excluded), Brain Tumor (tumour vs no tumour)
and Heart (num > 0), and subject-grouped folds for Parkinson's. Its results
describe that execution only.

For every dataset and every candidate model the script computes, on pooled
OOF probabilities:
  * AUROC; Brier score and scaled Brier (1 - Brier / [prev (1 - prev)])
  * ECE, 10 equal-width bins, last bin CLOSED          (ece_closed)
  * ECE exactly as implemented at 2d89637 (half-open)  (ece_pipeline)
  * calibration-in-the-large (intercept, slope fixed at 1) and calibration
    slope, by logistic recalibration on logit(p) (Cox 1958)
  * observed / expected ratio
  * 95 % percentile bootstrap intervals (2,000 resamples, seed 42) for the
    selected model
and draws reliability diagrams for the model chosen by the clinical score.

Usage  : python scripts/03_calibration_oof.py --results <path/to/resultados.json>
Outputs: outputs/03_calibration_selected.csv, outputs/03_calibration_all_models.csv,
         outputs/03_parkinsons_grouping.csv, figures/fig_reliability.pdf/.png
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np
from scipy.special import expit, logit

ap = argparse.ArgumentParser()
ap.add_argument("--results", required=True)
ap.add_argument("--n-boot", type=int, default=2000)
args = ap.parse_args()

ROOT = Path(__file__).resolve().parents[1]
OUT, FIG = ROOT / "outputs", ROOT / "figures"
OUT.mkdir(exist_ok=True)
FIG.mkdir(exist_ok=True)
R = json.loads(Path(args.results).read_text(encoding="utf-8"))
EPS = 1e-6

# benchmark name -> (audit label, task note)
MAP = {
    "01_Breast_Cancer_WBCD": ("01 Wisconsin", "same task; id removed (30 features)"),
    "02_BUSI_Breast_Ultrasound": ("02 BUSI", "benign vs malignant; normal images excluded"),
    "04_Stroke_Prediction": ("03 Stroke", "random subsample of 3,000 rows"),
    "05_PIMA_Diabetes": ("04 PIMA", "same task"),
    "06_Brain_Tumor_MRI": ("05 Brain tumor", "binary tumour vs no tumour, 1,001 Training-folder images"),
    "08_Brain_MRI_Oncology": ("06 Brain oncology", "same task"),
    "09_Heart_Disease_Cleveland": ("07 Heart", "binary num > 0 (not 5-class)"),
    "10_Parkinsons_Vocal": ("08 Parkinson's", "subject-grouped 5-fold"),
}


def auroc(y, p):
    y = np.asarray(y)
    pos, neg = p[y == 1], p[y == 0]
    if len(pos) == 0 or len(neg) == 0:
        return np.nan
    order = np.argsort(np.concatenate([pos, neg]), kind="mergesort")
    ranks = np.empty(len(order))
    allv = np.concatenate([pos, neg])[order]
    # average ranks for ties
    i = 0
    r = np.empty(len(allv))
    while i < len(allv):
        j = i
        while j + 1 < len(allv) and allv[j + 1] == allv[i]:
            j += 1
        r[i:j + 1] = (i + j) / 2 + 1
        i = j + 1
    ranks[order] = r
    rp = ranks[:len(pos)].sum()
    return (rp - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg))


def ece(y, p, closed=True, n_bins=10):
    edges = np.linspace(0, 1, n_bins + 1)
    tot, n = 0.0, len(y)
    for i in range(n_bins):
        hi_ok = (p <= edges[i + 1]) if (closed and i == n_bins - 1) else (p < edges[i + 1])
        m = (p >= edges[i]) & hi_ok
        if m.any():
            tot += m.sum() / n * abs(y[m].mean() - p[m].mean())
    return tot


def logistic_fit(x, y, offset=None, slope=True, iters=100):
    """Unpenalised logistic regression by Newton-Raphson.
    slope=True : y ~ b0 + b1 x            -> returns (b0, b1)
    slope=False: y ~ b0 + offset(x)       -> returns (b0, 1.0)"""
    if slope:
        X = np.column_stack([np.ones_like(x), x])
        b = np.zeros(2)
        off = 0.0
    else:
        X = np.ones((len(x), 1))
        b = np.zeros(1)
        off = x
    for _ in range(iters):
        eta = X @ b + off
        mu = expit(eta)
        W = np.clip(mu * (1 - mu), 1e-12, None)
        g = X.T @ (y - mu)
        H = (X * W[:, None]).T @ X
        try:
            step = np.linalg.solve(H, g)
        except np.linalg.LinAlgError:
            break
        b = b + step
        if np.max(np.abs(step)) < 1e-10:
            break
    return (float(b[0]), float(b[1])) if slope else (float(b[0]), 1.0)


def metrics(y, p):
    y = np.asarray(y, float)
    p = np.asarray(p, float)
    prev = y.mean()
    lp = logit(np.clip(p, EPS, 1 - EPS))
    brier = np.mean((p - y) ** 2)
    citl, _ = logistic_fit(lp, y, slope=False)
    _, slope = logistic_fit(lp, y, slope=True)
    return dict(n=len(y), prevalence=prev, auroc=auroc(y, p), brier=brier,
                scaled_brier=1 - brier / (prev * (1 - prev)),
                ece_closed=ece(y, p, True), ece_pipeline=ece(y, p, False),
                n_p_eq_1=int((p >= 1.0).sum()), n_p_eq_0=int((p <= 0.0).sum()),
                citl=citl, slope=slope, oe_ratio=prev / p.mean(), mean_p=p.mean())


def boot(y, p, B, seed=42):
    rng = np.random.default_rng(seed)
    y, p = np.asarray(y, float), np.asarray(p, float)
    keys = ("auroc", "brier", "ece_closed", "citl", "slope")
    acc = {k: [] for k in keys}
    n = len(y)
    for _ in range(B):
        idx = rng.integers(0, n, n)
        if y[idx].min() == y[idx].max():
            continue
        m = metrics(y[idx], p[idx])
        for k in keys:
            acc[k].append(m[k])
    return {k: (float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))) for k, v in acc.items()}


sel_rows, all_rows, diag = [], [], []
for b in R["bases"]:
    if b["nome"] not in MAP:
        continue
    label, task = MAP[b["nome"]]
    sel = b["selecao_clinica"]
    for name, m in b["modelos"].items():
        y, p = np.array(m["oof"]["y"]), np.array(m["oof"]["prob"])
        r = metrics(y, p)
        r.update(dataset=label, benchmark_name=b["nome"], model=name, selected=(name == sel),
                 conventional=(name == b["selecao_convencional"]), task_note=task,
                 stored_mean_fold_auroc=m["auc"]["media"], stored_mean_fold_ece=m["ece"]["media"],
                 protocol=b["protocolo_cv"])
        all_rows.append(r)
        if name == sel:
            ci = boot(y, p, args.n_boot)
            for k, (lo, hi) in ci.items():
                r[f"{k}_lo"], r[f"{k}_hi"] = lo, hi
            sel_rows.append(r)
            diag.append((label, name, y, p, r))

# Parkinson's leakage study (same data, grouped vs record-level folds)
park_rows = []
for key, blk in R.get("estudo_vazamento_parkinsons", {}).items():
    if "modelos" not in blk:
        continue
    for sel_key in ("selecao_clinica", "selecao_convencional"):
        name = blk[sel_key]
        m = blk["modelos"][name]
        y, p = np.array(m["oof"]["y"]), np.array(m["oof"]["prob"])
        r = metrics(y, p)
        ci = boot(y, p, args.n_boot)
        r.update({f"{k}_lo": v[0] for k, v in ci.items()})
        r.update({f"{k}_hi": v[1] for k, v in ci.items()})
        r.update(protocol=blk["protocolo_cv"], grouping=key, rule=sel_key, model=name,
                 n_subjects=blk.get("n_sujeitos"),
                 stored_mean_fold_auroc=m["auc"]["media"], stored_mean_fold_mcc=m["mcc"]["media"],
                 stored_mean_fold_sens=m["sensibilidade"]["media"], stored_mean_fold_spec=m["especificidade"]["media"])
        park_rows.append(r)


def dump(rows, path):
    if not rows:
        return
    keys = list(dict.fromkeys(k for r in rows for k in r))
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for r in rows:
            w.writerow({k: (round(v, 6) if isinstance(v, float) else v) for k, v in r.items()})


dump(sel_rows, OUT / "03_calibration_selected.csv")
dump(all_rows, OUT / "03_calibration_all_models.csv")
dump(park_rows, OUT / "03_parkinsons_grouping.csv")

# ── Reliability diagrams ─────────────────────────────────────────────────────
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams.update({"pdf.fonttype": 42, "ps.fonttype": 42, "font.family": "serif",
                     "font.serif": ["Nimbus Roman", "Nimbus Roman No9 L", "TeX Gyre Termes", "Times New Roman", "DejaVu Serif"], "font.size": 7, "axes.linewidth": 0.6,
                     "xtick.major.width": 0.5, "ytick.major.width": 0.5})
fig, axes = plt.subplots(2, 4, figsize=(7.1, 3.9), sharex=True, sharey=True)
edges = np.linspace(0, 1, 11)
for ax, (label, name, y, p, r) in zip(axes.ravel(), diag):
    ax.plot([0, 1], [0, 1], ls="--", lw=0.6, color="0.55")
    xs, ys, ns = [], [], []
    for i in range(10):
        hi = (p <= edges[i + 1]) if i == 9 else (p < edges[i + 1])
        msk = (p >= edges[i]) & hi
        if msk.sum() >= 1:
            xs.append(p[msk].mean())
            ys.append(y[msk].mean())
            ns.append(msk.sum())
    ns = np.array(ns)
    ax.plot(xs, ys, color="#1f4e79", lw=0.9, zorder=2)
    ax.scatter(xs, ys, s=4 + 40 * ns / ns.max(), color="#1f4e79", zorder=3, linewidths=0)
    ax.set_title(f"{label} (benchmark)\n{name.replace('LogisticRegression','LR').replace('RandomForest','RF').replace('GradientBoosting','GB')}",
                 fontsize=6.5, pad=2)
    ax.text(0.97, 0.03, f"ECE {r['ece_closed']:.3f}\nslope {r['slope']:.2f}\nBrier {r['brier']:.3f}",
            transform=ax.transAxes, va="bottom", ha="right", fontsize=5.6,
            bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="0.8", lw=0.4))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.tick_params(labelsize=5.5, length=2)
for ax in axes[1]:
    ax.set_xlabel("Mean predicted probability", fontsize=6)
for ax in axes[:, 0]:
    ax.set_ylabel("Observed frequency", fontsize=6)
fig.tight_layout(pad=0.4, w_pad=0.3, h_pad=0.6)
fig.savefig(FIG / "fig_reliability.pdf")
fig.savefig(FIG / "fig_reliability.png", dpi=300)

print(f"{'dataset':20s} {'model':18s} {'AUROC':>6s} {'Brier':>6s} {'sBrier':>6s} {'ECEc':>6s} {'ECEp':>6s} {'n1':>4s} {'CITL':>6s} {'slope':>6s} {'O/E':>5s}")
for r in sel_rows:
    print(f"{r['dataset']:20s} {r['model']:18s} {r['auroc']:6.3f} {r['brier']:6.3f} {r['scaled_brier']:6.3f} "
          f"{r['ece_closed']:6.3f} {r['ece_pipeline']:6.3f} {r['n_p_eq_1']:4d} {r['citl']:6.2f} {r['slope']:6.2f} {r['oe_ratio']:5.2f}"
          f"  CI ECE[{r['ece_closed_lo']:.3f},{r['ece_closed_hi']:.3f}] slope[{r['slope_lo']:.2f},{r['slope_hi']:.2f}] citl[{r['citl_lo']:.2f},{r['citl_hi']:.2f}]")
print()
for r in park_rows:
    print(r["grouping"], r["rule"], r["model"], "AUROC %.3f [%.3f,%.3f]" % (r["auroc"], r["auroc_lo"], r["auroc_hi"]),
          "ECE %.3f slope %.2f" % (r["ece_closed"], r["slope"]), "stored fold-mean AUROC", r["stored_mean_fold_auroc"])
gap = max(abs(r["ece_closed"] - r["ece_pipeline"]) for r in all_rows)
worst = max(all_rows, key=lambda r: abs(r["ece_closed"] - r["ece_pipeline"]))
print(f"\nmax |ECE_closed - ECE_pipeline| across all models: {gap:.4f} ({worst['dataset']}, {worst['model']}, n_p=1: {worst['n_p_eq_1']})")

# ── Compact single-column version (3.5 in wide) ──────────────────────────────
short = {"LogisticRegression": "LR", "RandomForest": "RF", "GradientBoosting": "GB"}
fig, axes = plt.subplots(2, 4, figsize=(3.5, 2.25), sharex=True, sharey=True)
for ax, (label, name, y, p, r) in zip(axes.ravel(), diag):
    ax.plot([0, 1], [0, 1], ls="--", lw=0.4, color="0.6")
    xs, ys = [], []
    for i in range(10):
        hi = (p <= edges[i + 1]) if i == 9 else (p < edges[i + 1])
        msk = (p >= edges[i]) & hi
        if msk.any():
            xs.append(p[msk].mean())
            ys.append(y[msk].mean())
    ax.plot(xs, ys, color="#1f4e79", lw=0.7, marker="o", ms=1.6)
    ax.set_title(f"{label.split(' ', 1)[1]}\n{short.get(name, name)}, ECE {r['ece_closed']:.2f}",
                 fontsize=4.8, pad=1.5, linespacing=1.0)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.set_xticks([0, 0.5, 1]); ax.set_yticks([0, 0.5, 1])
    ax.tick_params(labelsize=4.5, length=1.5, pad=1)
fig.supxlabel("Mean predicted probability", fontsize=5.2, y=0.01)
fig.supylabel("Observed frequency", fontsize=5.2, x=0.01)
fig.tight_layout(pad=0.3, w_pad=0.2, h_pad=0.4)
fig.savefig(FIG / "fig_reliability_col.pdf")
fig.savefig(FIG / "fig_reliability_col.png", dpi=300)
