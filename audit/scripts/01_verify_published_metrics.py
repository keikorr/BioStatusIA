#!/usr/bin/env python3
"""
01_verify_published_metrics.py
------------------------------------------------------------------------------
Tier B (numerical verification) and Tier C (secondary re-analysis) of the
BioStatusIA audit.

Recomputes every quantity in Tables I-V of the audit manuscript that can be
derived from the confusion matrices printed in the eight execution reports,
and compares it with the published value.

Inputs : data/published_values.json  (transcribed values; see "_source")
Outputs: outputs/01_verification.csv     one row per checked quantity
         outputs/01_verification.md      human-readable summary
         outputs/01_derived_measures.json  Wilson CIs, PPV/NPV, LRs, etc.

Usage  : python scripts/01_verify_published_metrics.py
Needs  : Python >= 3.10, numpy, scipy, scikit-learn (only for the split check)
Exit   : 0 always; mismatches are reported, not raised.
"""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import numpy as np
from scipy.stats import norm, pearsonr

ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / "data" / "published_values.json").read_text(encoding="utf-8"))
OUT = ROOT / "outputs"
OUT.mkdir(exist_ok=True)

Z = norm.ppf(0.975)
rows: list[dict] = []


def check(table: str, dataset: str, quantity: str, published, recomputed, tol: float,
          note: str = "") -> None:
    if published is None or recomputed is None:
        status = "NOT-COMPARABLE"
        diff = None
    else:
        diff = float(recomputed) - float(published)
        status = "PASS" if abs(diff) <= tol + 1e-12 else "MISMATCH"
    rows.append({
        "table": table, "dataset": dataset, "quantity": quantity,
        "published": published, "recomputed": None if recomputed is None else round(float(recomputed), 6),
        "abs_diff": None if diff is None else round(abs(diff), 6), "tolerance": tol,
        "status": status, "note": note,
    })


def wilson(k: int, n: int) -> tuple[float, float]:
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    den = 1 + Z**2 / n
    centre = (p + Z**2 / (2 * n)) / den
    half = Z * math.sqrt(p * (1 - p) / n + Z**2 / (4 * n**2)) / den
    return centre - half, centre + half


def mcc_binary(tp, tn, fp, fn) -> float:
    den = math.sqrt((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn))
    return (tp * tn - fp * fn) / den if den else 0.0


derived: dict = {"binary": {}, "multiclass": {}}

# ── Binary runs ───────────────────────────────────────────────────────────────
T1 = DATA["table1"]
for ds, c in DATA["binary"].items():
    N, P, FN, FP = c["N"], c["P"], c["FN"], c["FP"]
    Nn = N - P
    TP, TN = P - FN, Nn - FP
    sens, spec = TP / P, TN / Nn
    acc = (TP + TN) / N
    mcc = mcc_binary(TP, TN, FP, FN)
    ppv = TP / (TP + FP) if TP + FP else float("nan")
    npv = TN / (TN + FN) if TN + FN else float("nan")
    lrp = sens / (1 - spec) if spec < 1 else None
    lrn = (1 - sens) / spec
    s_lo, s_hi = wilson(TP, P)
    e_lo, e_hi = wilson(TN, Nn)
    ppv_lo, ppv_hi = wilson(TP, TP + FP)
    npv_lo, npv_hi = wilson(TN, TN + FN)
    derived["binary"][ds] = dict(TP=TP, TN=TN, FP=FP, FN=FN, N=N, prevalence=P / N,
                                 acc=acc, sens=sens, spec=spec, mcc=mcc, ppv=ppv, npv=npv,
                                 lr_pos=lrp, lr_neg=lrn, sens_ci=[s_lo, s_hi], spec_ci=[e_lo, e_hi],
                                 ppv_ci=[ppv_lo, ppv_hi], npv_ci=[npv_lo, npv_hi],
                                 balanced_acc=(sens + spec) / 2)
    pub = dict(zip(T1["columns"], T1[ds]))
    check("I", ds, "accuracy", pub["acc"], acc, 0.0005)
    check("I", ds, "sensitivity (test)", pub["sens_test"], sens, 0.0005)
    check("I", ds, "specificity", pub["spec"], spec, 0.0005)
    check("I", ds, "MCC", pub["mcc"], mcc, 0.0005)
    w = DATA["table2_wilson"][ds]
    check("II", ds, "Wilson sens lower", w[1], s_lo, 0.0005)
    check("II", ds, "Wilson sens upper", w[2], s_hi, 0.0005)
    check("II", ds, "Wilson spec lower", w[4], e_lo, 0.0005)
    check("II", ds, "Wilson spec upper", w[5], e_hi, 0.0005)
    t3 = dict(zip(DATA["table3"]["columns"], DATA["table3"][ds]))
    check("III", ds, "prevalence", t3["prev"], P / N, 0.0005)
    check("III", ds, "PPV", t3["ppv"], ppv, 0.0005)
    check("III", ds, "NPV", t3["npv"], npv, 0.0005)
    check("III", ds, "LR+", t3["lr_pos"], lrp, 0.005,
          "undefined when FP = 0" if lrp is None else "")
    check("III", ds, "LR-", t3["lr_neg"], lrn, 0.005)

# ── Multiclass runs ───────────────────────────────────────────────────────────
for ds, c in DATA["multiclass"].items():
    sup = np.array(c["support"])
    cor = np.array(c["correct"])
    rec = cor / sup
    acc = cor.sum() / sup.sum()
    macro = rec.mean()
    macro_from_rounded = np.round(rec, 3).mean()
    derived["multiclass"][ds] = dict(per_class_recall=rec.tolist(), acc=float(acc),
                                     macro_recall=float(macro), errors=int(sup.sum() - cor.sum()),
                                     macro_recall_from_rounded=float(macro_from_rounded))
    pub = dict(zip(T1["columns"], T1[ds]))
    txt = DATA["multiclass_text"][ds]
    check("I", ds, "accuracy", pub["acc"], acc, 0.0005)
    check("I", ds, "macro recall (3 d.p., report)", txt["macro_recall_reported"], macro, 0.0005)
    check("text II-F", ds, "macro recall (4 d.p., v1 text)", txt["macro_recall_v1_text"], macro, 0.00005,
          f"v1 value equals the mean of per-class recalls rounded to 3 d.p. ({macro_from_rounded:.4f}); "
          f"exact value from counts is {macro:.4f}")
    if "errors_v1_text" in txt:
        check("text III-C", ds, "number of errors", txt["errors_v1_text"], sup.sum() - cor.sum(), 0)
    if "balanced_acc_v1_text" in txt:
        check("text III-C", ds, "balanced accuracy", txt["balanced_acc_v1_text"], macro, 0.0005)

# ── Summary rows of Table I ───────────────────────────────────────────────────
order = [k for k in T1 if k not in ("columns", "mean_row", "sd_row")]
for j, col in enumerate(T1["columns"][1:8], start=1):
    vals = np.array([T1[k][j] for k in order], dtype=float)
    check("I", "summary", f"unweighted mean {col}", T1["mean_row"][j], vals.mean(), 0.0005)
    check("I", "summary", f"sample SD {col}", T1["sd_row"][j], vals.std(ddof=1), 0.0005)

# ── Internal (CV) vs held-out sensitivity ─────────────────────────────────────
cv = np.array([T1[k][4] for k in order])
te = np.array([T1[k][3] for k in order])
d = cv - te
txt = DATA["cv_vs_test_text"]
check("text III-E", "all", "Pearson r (CV vs test sensitivity)", txt["r"], pearsonr(cv, te)[0], 0.0005)
check("text III-E", "all", "mean signed difference (CV - test)", txt["mean_signed_cv_minus_test"], d.mean(), 0.0005)
check("text III-E", "all", "mean absolute difference", txt["mean_abs"], np.abs(d).mean(), 0.0005)
check("text III-E", "all", "min difference (CV - test)", txt["min"], d.min(), 0.0005)
check("text III-E", "all", "max difference (CV - test)", txt["max"], d.max(), 0.0005)

# ── Table IV deltas ───────────────────────────────────────────────────────────
for ds, r in DATA["table4"].items():
    if ds == "columns":
        continue
    sel, a_sel, best, a_best, dA, dS = r
    if dA is not None:
        check("IV", ds, "delta AUROC (best - selected)", dA, a_best - a_sel, 0.0005)

# ── Table V: share of the end-to-end interval inside the LLM/crew call ────────
t5 = DATA["table5"]
share = {k: v[2] / v[3] for k, v in t5.items() if k != "columns"}
derived["timing_share_inside_crew_call"] = share
derived["timing_note"] = (
    "For image runs (02, 05, 06) the timed crew kickoff contains the tool calls that run "
    "image preprocessing, feature extraction and the full AutoML protocol (app.py; "
    "tools/analise_base_tool.py, tools/extracao_tool.py, tools/treino_tool.py at 2d89637). "
    "For tabular runs the AutoML protocol runs after the crew call."
)

# ── Split composition sanity check (stratified 20 %, seed 42) ─────────────────
try:
    from sklearn.model_selection import train_test_split
    comp = {}
    for ds, c in DATA["multiclass"].items():
        tot = c["class_totals_source"]
        y = np.repeat(np.arange(len(tot)), tot)
        _, _, _, yt = train_test_split(np.zeros((len(y), 1)), y, test_size=0.2, random_state=42, stratify=y)
        comp[ds] = np.bincount(yt).tolist()
        check("split", ds, "test support reproduced by stratified split",
              "|".join(map(str, c["support"])), None, 0, f"recomputed {comp[ds]}")
        rows[-1]["status"] = "PASS" if comp[ds] == c["support"] else "MISMATCH"
    # 7,023-image composition of the public description (Nickparvar), for contrast
    y = np.repeat(np.arange(4), [1621, 1645, 2000, 1757])
    _, _, _, yt = train_test_split(np.zeros((len(y), 1)), y, test_size=0.2, random_state=42, stratify=y)
    derived["brain_tumor_test_support_if_7023_images"] = np.bincount(yt).tolist()
except ImportError:
    pass

# ── Write outputs ─────────────────────────────────────────────────────────────
with open(OUT / "01_verification.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)
(OUT / "01_derived_measures.json").write_text(json.dumps(derived, indent=2), encoding="utf-8")

n_pass = sum(r["status"] == "PASS" for r in rows)
n_mis = [r for r in rows if r["status"] == "MISMATCH"]
lines = ["# 01 - Numerical verification of published values", "",
         f"Checked quantities: {len(rows)} | PASS: {n_pass} | MISMATCH: {len(n_mis)} | "
         f"not comparable: {sum(r['status']=='NOT-COMPARABLE' for r in rows)}", ""]
if n_mis:
    lines += ["## Mismatches", "", "| table | dataset | quantity | published | recomputed | note |",
              "|---|---|---|---|---|---|"]
    for r in n_mis:
        lines.append(f"| {r['table']} | {r['dataset']} | {r['quantity']} | {r['published']} | "
                     f"{r['recomputed']} | {r['note']} |")
lines += ["", "## Share of end-to-end time inside the timed crew call", ""]
for k, v in share.items():
    lines.append(f"- run {k} ({t5[k][4]}): {v:.3f}")
(OUT / "01_verification.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
print("\n".join(lines))
