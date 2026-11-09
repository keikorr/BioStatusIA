#!/usr/bin/env python3
"""
02_code_protocol_checklist.py
------------------------------------------------------------------------------
Tier A (code audit) of the BioStatusIA audit: a reproducible checklist of
code/protocol statements, each verified by a static check against a pinned
commit of the source code.

Every item prints the file and line numbers it relies on, so a reader can
open the same lines at the same commit. No code from the audited repository
is imported or executed.

Usage
  git clone https://github.com/JuniorSoares716/BioStatusIA_MultiModal mm
  git -C mm checkout 2d89637b752e12460954f1d449586e8ec88cf469
  git clone -b atualizacao_features https://github.com/keikorr/BioStatusIA bs
  git -C bs checkout 6960fd60c426e0b2728e0226311ae99399e14c31
  python scripts/02_code_protocol_checklist.py --audited mm --lineage bs

Outputs
  outputs/02_checklist.csv   one row per item (id, status, evidence, ...)
  outputs/02_checklist.md    same content as a Markdown table

Status vocabulary
  CONFIRMED   code matches the statement in manuscript v1
  DISCREPANT  code contradicts a statement in manuscript v1 or the companion study
  OMITTED     material implementation detail absent from manuscript v1
  LATENT      defect present in code, no effect expected on the eight runs
  UNRESOLVED  cannot be settled from code; needs run artifacts or source data
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("--audited", required=True, help="checkout of BioStatusIA_MultiModal @ 2d89637")
ap.add_argument("--lineage", required=False, help="checkout of keikorr/BioStatusIA @ atualizacao_features")
args = ap.parse_args()

A = Path(args.audited)
L = Path(args.lineage) if args.lineage else None
PIPE = "src/biostatusia/pipeline"
OUT = Path(__file__).resolve().parents[1] / "outputs"
OUT.mkdir(exist_ok=True)


def head(repo: Path | None) -> str:
    if repo is None:
        return "n/a"
    try:
        return subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        return "unknown (not a git checkout)"


def lines(repo: Path, rel: str) -> list[str]:
    p = repo / rel
    return p.read_text(encoding="utf-8", errors="replace").splitlines() if p.exists() else []


def grep(repo: Path, rel: str, pattern: str) -> list[int]:
    rx = re.compile(pattern)
    return [i + 1 for i, s in enumerate(lines(repo, rel)) if rx.search(s)]


def ev(rel: str, nums: list[int]) -> str:
    return f"{rel}:{','.join(map(str, nums))}" if nums else f"{rel}: (no match)"


def first(repo, rel, pat):
    n = grep(repo, rel, pat)
    return n[0] if n else None


items: list[dict] = []


def add(iid, area, status, statement, observed, evidence, impact, action):
    items.append(dict(id=iid, area=area, status=status, manuscript_v1_or_companion=statement,
                      observed_in_code=observed, evidence=evidence, impact_on_eight_runs=impact,
                      resolution_needed=action))


C = f"{PIPE}/classificador.py"
AV = f"{PIPE}/avaliacao_modelos.py"
DT = f"{PIPE}/dados_tabulares.py"
EX = f"{PIPE}/extracao.py"
PR = f"{PIPE}/preprocessamento.py"
AB = f"{PIPE}/analise_base.py"
IO = f"{PIPE}/io_utils.py"
APP = "src/biostatusia/app.py"
CREW = "src/biostatusia/crew.py"

# ── Protocol ──────────────────────────────────────────────────────────────────
split = grep(A, C, r"train_test_split\(")
rskf = grep(A, C, r"RepeatedStratifiedKFold\(n_splits=n_splits, n_repeats=3")
nspl = grep(A, C, r"n_splits = max\(2, min\(5, n_min\)\)")
add("C01", "protocol", "CONFIRMED" if split and rskf and nspl else "DISCREPANT",
    "Outer stratified 80/20 split (seed 42); inner RepeatedStratifiedKFold, n_splits=max(2,min(5,n_min)), 3 repeats",
    "As stated", ev(C, split + nspl + rskf), "none", "none")

shap_call = first(A, C, r"selecionar_features_shap\(")
loop = first(A, C, r"for fold_train, fold_val in rskf\.split")
imp_fold = first(A, C, r"imputar_treino_teste\(Xf_tr_raw")
bal_fold = first(A, C, r"Xf_tr, yf_tr, _ = balancear")
outside = shap_call is not None and loop is not None and shap_call < loop
add("D01", "protocol", "DISCREPANT" if outside else "CONFIRMED",
    "Protocol described as nested; Fig. 1 lists imputation, scaling and oversampling as refitted in each inner fold",
    "Imputation, scaling and SMOTE are refitted per inner fold, but SHAP feature selection is fitted ONCE on the whole "
    "outer-training partition before the inner loop; the inner-CV metrics that drive model selection therefore use "
    "features chosen with the inner validation rows (selection bias in the internal estimate; held-out set unaffected)",
    ev(C, [x for x in (shap_call, loop, imp_fold, bal_fold) if x]),
    "Affects runs where selection removed features (p > n_keep): Wisconsin (31 -> 20); possibly Stroke. Inflates "
    "internal (CV) metrics, including the CV sensitivity used by the hard floor",
    "Move selection inside each inner fold, or report CV metrics as optimistic")

score = grep(A, AV, r"def calcular_score_clinico|w_auc: float = 0\.40|deficit_sens \*\* 1\.5|mcc_norm = ")
floor = grep(A, AV, r"elegiveis = \[n for n in nomes if metricas\[n\]\.get\(\"sensibilidade\"")
add("C02", "selection", "CONFIRMED" if score and floor else "DISCREPANT",
    "Score S = 0.4 A + 0.4 (M+1)/2 - 0.2 clip(E) - max(0, 0.80 - sigma)^1.5 on inner-CV means; hard floor on CV "
    "mean sensitivity; fallback to highest score with piso_sensibilidade_atingido=False",
    "As stated", ev(AV, score + floor), "none", "none")

# ── Feature pipeline ─────────────────────────────────────────────────────────
num30 = grep(A, DT, r"for row in data\[:30\]")
add("D02", "tabular schema", "DISCREPANT" if num30 else "CONFIRMED",
    "Schema detection 'admits every numeric column that is not the label'",
    "A column is numeric only if every non-empty value in the FIRST 30 ROWS parses as float; a column with a "
    "non-numeric missing-value token (e.g. 'N/A') in those rows is treated as categorical and, with >20 distinct "
    "values, silently discarded",
    ev(DT, num30 + grep(A, DT, r"LIMITE_CARDINALIDADE_ONEHOT = 20")),
    "Stroke: bmi is the only column with missing values and encodes them as 'N/A'; the reported 'imputation: none' is "
    "consistent with bmi having been excluded",
    "Publish the per-run schema (retained feature names)")

idf = grep(A, DT, r"\b(ID_COLS|id_cols|identificador)\b")
add("D03", "tabular schema", "DISCREPANT" if not idf else "CONFIRMED",
    "Wisconsin listed with 31 inputs 'i.e. the 30 measurements plus the id column'; no ID handling described",
    "No identifier filtering in detectar_schema: any numeric ID column (Wisconsin 'id', Stroke 'id') enters X. In "
    "the lineage branch, earlier outputs ranked 'id' as the top feature for Wisconsin and Stroke",
    ev(DT, grep(A, DT, r"def detectar_schema")) + (
        "; lineage: reports/resultados_kaggle_reais.json ('feature_importante': 'id')" if L else ""),
    "Wisconsin and Stroke models may use a row identifier; any signal it carries is an artefact of file ordering",
    "Drop identifier columns; report whether 'id' survived SHAP selection")

rule = grep(A, DT, r"pct_outliers > 0\.08 or tamanho_insuficiente|< 0\.5$|\) < 0\.5")
treinar_default = grep(A, C, r"return treinar_vetores\(X, y\)")
add("D04", "tabular scaling", "OMITTED",
    "Scaling chosen per dataset 'by an agent rule'",
    "Deterministic rule (no LLM involved): RobustScaler if the pooled IQR-outlier share > 0.08 OR fewer than 50 % of "
    "features pass Shapiro-Wilk (p > 0.05); else StandardScaler. Image runs always use StandardScaler "
    "(treinar() calls treinar_vetores with defaults)",
    ev(DT, rule) + "; " + ev(C, treinar_default),
    "Shapiro-Wilk rejects normality for almost any feature at n in the thousands, so large tables default to RobustScaler",
    "State thresholds; record chosen scaler per run")

glcm = grep(A, EX, r"graycomatrix\(gray_u8, \[1\], \[0\], 256")
ent = grep(A, EX, r"calcHist|entropia = float\(-np\.sum")
add("D05", "image features", "DISCREPANT" if ent else "CONFIRMED",
    "Descriptors include 'GLCM contrast, homogeneity, energy and entropy'",
    "Entropy is first-order (grey-level histogram) entropy, not a GLCM property; GLCM uses a single offset "
    "(distance 1, angle 0 rad), 256 levels, symmetric, normalised",
    ev(EX, glcm + ent), "Texture description is direction-specific; 'GLCM entropy' is mislabelled",
    "Relabel; specify GLCM offsets")

norm255 = grep(A, PR, r"normalizada = img\.astype\(np\.float32\) / 255\.0")
add("D06", "image preprocessing", "DISCREPANT" if norm255 else "CONFIRMED",
    "'percentile (1-99) normalization in place of min-max'",
    "The default (non-percentile) branch of the adaptive path divides by 255; no per-image min-max is applied. "
    "Resizing to 256x256 ignores aspect ratio (cv2.resize)",
    ev(PR, norm255 + grep(A, PR, r"img = cv2\.resize\(img, tamanho\)")), "Descriptive only",
    "Correct wording")

nlm = grep(A, PR, r"denoise_nl_means\(|h=0\.1|createCLAHE\(clipLimit=2\.0, tileGridSize=\(8, 8\)\)|np\.percentile\(img, \[1, 99\]\)")
rules_img = grep(A, AB, r"ruido > 0\.05|outliers > max\(1, n \* 0\.1\)|contraste < 30")
add("C03", "image preprocessing", "CONFIRMED",
    "CLAHE (2.0, 8x8), NL-means (h=0.1) instead of Gaussian, percentile 1-99; chosen per run by rule",
    "As stated; rule thresholds: noise sigma > 0.05 -> NL-means; >10 % intensity outliers -> percentile; mean "
    "contrast < 30 -> CLAHE (NL-means also uses patch 5, distance 6, fast mode)",
    ev(PR, nlm) + "; " + ev(AB, rules_img), "none", "Report thresholds")

subs = grep(A, DT, r"max_amostras_shap: int = 200")
add("D07", "feature selection", "OMITTED",
    "SHAP selector: RF probe on training fold, top n = max(2, min(p, n_train/3, 20)) by mean |SHAP|",
    "As stated, but SHAP values are computed on a random subsample of at most 200 training rows",
    ev(DT, subs), "Minor", "Report subsample size")

silent_bal = grep(A, AV, r"except Exception as e:")
silent_shap = grep(A, DT, r"except Exception as e:")
req = lines(A, "requirements.txt")
missing = [p for p in ("scikit-learn", "shap", "imbalanced-learn") if not any(p in r for r in req)]
add("D08", "dependencies", "DISCREPANT" if missing else "CONFIRMED",
    "SMOTE and SHAP selection 'enabled by default'; their runtime status is not in the reports",
    "balancear() and selecionar_features_shap() catch every exception (including ImportError) and return the data "
    f"unchanged. requirements.txt omits {', '.join(missing)}, which pyproject.toml/uv.lock declare; the two install "
    "routes can therefore yield different pipelines without any error",
    ev(AV, silent_bal[:1]) + "; " + ev(DT, silent_shap[-1:]) + "; requirements.txt",
    "Whether oversampling and feature selection ran in the eight runs is unknown",
    "Log info_balanceamento / selecao_features_shap per run; pin environment")

# ── Timing and report generation ─────────────────────────────────────────────
kick_img = first(A, APP, r"crew_out, llm_timing = medir_llm_kickoff\(lambda: BioStatusIACrew\(\)\.crew\(\)")
tools = grep(A, CREW, r"tools=\[FerramentaAnaliseBase\(\)\]|tools=\[FerramentaExtrairBiomarcadores\(\)\]|tools=\[FerramentaTreinarClassificador\(\)\]")
add("D09", "timing", "DISCREPANT" if kick_img and tools else "UNRESOLVED",
    "Table V 'LLM (s)': 'Local language-model generation ... accounts for 789.2 of the 809.5 s' (Brain Tumor)",
    "For image runs the timed interval wraps the whole CrewAI kickoff, whose agents call tools that run base "
    "analysis, preprocessing + feature extraction of every image, and the full AutoML protocol. The column is "
    "crew wall time, not generation time",
    ev(APP, [kick_img] if kick_img else []) + "; " + ev(CREW, tools),
    "Runs 02, 05, 06: LLM generation time is not identifiable; runs 01, 03, 04, 07, 08 (tabular): crew call precedes "
    "AutoML, so the remainder of end-to-end time is mostly AutoML",
    "Instrument tool calls separately")

kick_tab = first(A, APP, r"BioStatusIACrewTabular\(\)\.crew\(\)\.kickoff")
train_tab = first(A, APP, r"res_clf = treinar_vetores\(")
add("D10", "report generation", "DISCREPANT" if kick_tab and train_tab and kick_tab < train_tab else "CONFIRMED",
    "Narrative reports generated from the run's results (companion study)",
    "In tabular mode the LLM narrative is produced BEFORE classifier training, so it cannot reflect the classifier "
    "results shown in the same report",
    ev(APP, [kick_tab, train_tab]), "Narratives of runs 01, 03, 04, 07, 08 are independent of their AutoML output",
    "Generate narrative after training or label it as descriptive statistics only")

stale = grep(A, "src/biostatusia/config/tasks.yaml", r"maior AUC") + grep(A, "src/biostatusia/config/agents.yaml", r"SVM, Random Forest")
stale_tool = grep(A, "src/biostatusia/tools/treino_tool.py", r"selecionado por maior AUC-ROC|Treina SVM \(RBF\) e RandomForest")
add("D11", "report generation", "DISCREPANT" if stale or stale_tool else "CONFIRMED",
    "Selection by clinical score with sensitivity floor among six candidates",
    "Agent/task prompts and the training tool's returned text describe two models (SVM, RF) and 'best model = "
    "highest AUC'; the image-mode narrative is prompted with a selection rule the code does not use",
    "src/biostatusia/config/tasks.yaml:" + ",".join(map(str, grep(A, "src/biostatusia/config/tasks.yaml", r"maior AUC"))) +
    "; src/biostatusia/config/agents.yaml:" + ",".join(map(str, grep(A, "src/biostatusia/config/agents.yaml", r"SVM, Random Forest"))) +
    "; " + ev("src/biostatusia/tools/treino_tool.py", stale_tool),
    "Image narratives (runs 02, 05, 06) may misstate how the model was selected", "Update prompts")

tt = grep(A, C, r"t_treino = time\.perf_counter\(\) - t0|latencia_ms = round\(\(time\.perf_counter\(\) - t0\) \* 1000 / max\(1, len\(X_test\)\), 4\)")
ui = grep(A, "src/biostatusia/templates/tela2_resultados.html", r"5-fold CV")
add("D12", "timing", "OMITTED",
    "'Training takes 0.035-1.959 s'",
    "tempo_treino_s is one final fit of the selected model on the balanced training set; it excludes the 6x15 "
    "inner-CV fits and the SHAP probe. Inference latency times predict() only (not predict_proba) and is divided "
    "by test size. The UI labels the training time '5-fold CV'",
    ev(C, tt) + "; " + ev("src/biostatusia/templates/tela2_resultados.html", ui),
    "Table V training times understate the cost of the AutoML step", "Report full AutoML wall time")

# ── Implementation divergence ────────────────────────────────────────────────
av_models = grep(A, AV, r'"LogisticRegression": LogisticRegression\(random_state=42, max_iter=2000\)')
c_models = grep(A, C, r'class_weight="balanced"')
callers = []
for t in ("dicom_tool.py", "sinais_temporais_tool.py", "volumetrico_tool.py"):
    callers += [f"tools/{t}:{n}" for n in grep(A, f"src/biostatusia/tools/{t}", r"avaliar_modelos\(")]
add("D13", "implementation", "OMITTED",
    "Six classifiers with balanced class weights (LR, SVM, RF)",
    "Two divergent trainers exist: classificador.treinar_vetores (used by the eight runs: tabular and image "
    "folders; class weights, imputation, SHAP selection, rule-based scaler) and avaliacao_modelos.avaliar_modelos "
    "(used for DICOM, signal and volume modes; no class weights, no imputation, no SHAP selection, StandardScaler "
    "only, latency per batch)",
    ev(C, c_models) + "; " + ev(AV, av_models) + "; callers: " + "; ".join(callers),
    "None for these runs; results do not transfer to other modalities", "Unify trainers or document per modality")

knn = grep(A, C, r'"KNN": KNeighborsClassifier\(n_neighbors=5\)')
add("D14", "implementation", "DISCREPANT" if knn else "CONFIRMED",
    "'All use random_state=42'", "KNN has no random_state (deterministic); GradientBoosting and MLP have no class weights",
    ev(C, knn), "none", "Correct wording")

vocab = grep(A, IO, r"PASTAS_BENIGNAS = |PASTAS_MALIGNAS = |PASTAS_SPLIT_INDICADOR = ")
mask = grep(A, IO, r"mask")
add("D15", "image labels", "OMITTED",
    "Vocabulary {benign, normal, negative, no, 0} -> 0; {malignant, abnormal, positive, yes, 1} -> 1",
    "Vocabulary also contains benigno / malign / maligno; Training/Testing folders are pooled before the 80/20 "
    "split (source partitions ignored); no exclusion of segmentation-mask files" + (
        "" if mask else " (no 'mask' filter in io_utils.py)"),
    ev(IO, vocab), "BUSI: 780 images implies masks were absent from the copy used; must be documented",
    "Document source copy; filter *_mask files")

ece = grep(A, AV, r"mask = \(y_prob >= bins\[i\]\) & \(y_prob < bins\[i \+ 1\]\)|mask = \(confianca >= bins\[i\]\) & \(confianca < bins\[i \+ 1\]\)")
add("D16", "metrics", "LATENT",
    "ECE: ten equal-width half-open bins; p = 1.0 excluded",
    "Confirmed; excluded samples still count in the denominator n, i.e. they are treated as perfectly calibrated. "
    "Effect quantified on available out-of-fold probabilities by script 03",
    ev(AV, ece), "Biases ECE downward for models emitting p = 1.0 (RF, KNN, GB)", "Close the last bin")

bc = grep(A, C, r"n_min = int\(np\.min\(np\.bincount\(y_train\)\)\)")
add("D17", "protocol", "LATENT",
    "n_splits = max(2, min(5, n_min,class))",
    "n_min is computed with np.bincount, which counts absent integer labels as 0; with non-contiguous labels "
    "n_splits silently becomes 2. Labels are re-encoded contiguously in the paths used, so no effect here",
    ev(C, bc), "none", "Use np.unique counts")

sd = grep(A, C, r'"desvio": round\(float\(np\.std\(v\)\), 4\)')
add("D18", "metrics", "LATENT",
    "(not stated)", "Fold-level SD stored with ddof=0 (population SD)", ev(C, sd), "none", "Use ddof=1")

llm = grep(A, CREW, r'model=os\.getenv\("MODEL", "ollama/qwen2\.5:3b"\)|temperature=0\.1')
add("C04", "LLM", "CONFIRMED",
    "CrewAI + Ollama, default qwen2.5:3b, overridable by environment variable; model not recorded in reports",
    "As stated; variable is MODEL (and API_BASE); temperature 0.1", ev(CREW, llm), "none",
    "Record MODEL and Ollama model digest per run")

# ── Reporting / provenance (needs artefacts) ─────────────────────────────────
add("D19", "reporting", "DISCREPANT",
    "Sec. II-F: macro recall from confusion matrices 0.2226 (Heart), 0.9008 (Brain Tumor); Table I Parkinson's "
    "sensitivity 0.965 vs Table II 0.966",
    "Exact values from counts: 0.2225 and 0.9007 (v1 averaged per-class recalls already rounded to 3 d.p.); "
    "28/29 = 0.9655 (double rounding: code rounds to 4 d.p., tables to 3 d.p.)",
    "scripts/01_verify_published_metrics.py -> outputs/01_verification.md", "Rounding only (<= 0.0006)",
    "Round once from counts")

add("D20", "provenance", "UNRESOLVED",
    "Brain Tumor MRI: 7,200 images and a perfectly balanced test set are 'not explained'",
    "A stratified 20 % split of the 7,023-image composition (1621/1645/2000/1757) gives 324/329/400/352; 360 per "
    "class follows deterministically from a balanced input of ~1,800 per class (7,200 total). The question is the "
    "source version, not the split. The lineage data-sync script points to Kaggle 'versions/2'",
    "scripts/01_verify_published_metrics.py (split check)" + (
        "; lineage: scripts/copiar_bases_completas.py, scripts/auditar_integridade.py" if L else ""),
    "Dataset provenance", "Record Kaggle dataset version and file hashes")

add("D21", "provenance", "UNRESOLVED",
    "Dataset URLs in footnotes 1-8",
    "Lineage data scripts use different Kaggle sources for Wisconsin (uciml/breast-cancer-wisconsin-data) and BUSI "
    "(aryashah2k/breast-ultrasound-images-dataset, 'Dataset_BUSI_with_GT', which contains mask files)",
    ("lineage: scripts/auditar_integridade.py, scripts/copiar_bases_completas.py" if L else "lineage not supplied"),
    "Which copy fed each run is undocumented", "Publish per-run input manifest with hashes")

add("D22", "provenance", "UNRESOLVED",
    "Parkinson's: 195 recordings from 31 subjects; subject identifier 'unavailable for inspection'",
    "The UCI file carries a 'name' field (phon_R01_Sxx_k); the lineage benchmark parsed it into 32 subject codes "
    "(n_sujeitos = 32) versus 31 in the documentation",
    "lineage: scripts/benchmark_artigo2_corrigido.py (grupo_fn), reports/benchmark_artigo2/resultados.json",
    "Subject overlap in the 80/20 split is likely but unquantified", "Reconcile 31 vs 32; group by subject")

hashenc = grep(L, "scripts/benchmark_artigo2_corrigido.py", r"abs\(hash\(v\)\) % 1000") if L else []
add("D23", "lineage benchmark", "LATENT" if hashenc else "UNRESOLVED",
    "(lineage benchmark used in Sec. III-F of the revision)",
    "Categorical strings encoded as abs(hash(v)) % 1000; Python salts str hashes per process unless PYTHONHASHSEED "
    "is fixed, so codes are not reproducible across executions (affects tabular sets with string columns, e.g. Stroke)",
    ("scripts/benchmark_artigo2_corrigido.py:" + ",".join(map(str, hashenc))) if L else "lineage not supplied",
    "None on the eight runs; limits re-execution of the benchmark", "Use an explicit encoder")

if L:
    missing_fns = [f for f in ("imputar_treino_teste", "selecionar_features_shap", "selecionar_melhor_modelo",
                               "calcular_metricas_classificacao")
                   if not any(grep(L, f"{PIPE}/{m}", rf"def {f}\(") for m in
                              ("classificador.py", "avaliacao_modelos.py", "dados_tabulares.py"))]
    add("D24", "lineage", "DISCREPANT" if missing_fns else "CONFIRMED",
        "Code audit 'refers to repository commit 2d89637'; companion repository cited as BioStatusIA_MultiModal",
        "The project's main repository (keikorr/BioStatusIA, branch atualizacao_features, HEAD 6960fd6, 10 Sep 2026) "
        f"predates 2d89637 (12 Sep 2026, separate repository) and lacks: {', '.join(missing_fns)}. Results produced "
        "with that branch are not results of the audited code",
        f"lineage HEAD {head(L)}", "Statements must cite the exact repository and commit",
        "Cite both repositories with full hashes")

# ── Write ────────────────────────────────────────────────────────────────────
meta = {"audited_repo": str(A), "audited_head": head(A), "lineage_repo": str(L) if L else None,
        "lineage_head": head(L)}
with open(OUT / "02_checklist.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(items[0].keys()))
    w.writeheader()
    w.writerows(items)
(OUT / "02_checklist_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

count = {}
for it in items:
    count[it["status"]] = count.get(it["status"], 0) + 1
md = ["# 02 - Code/protocol checklist", "",
      f"Audited HEAD: `{meta['audited_head']}`  ", f"Lineage HEAD: `{meta['lineage_head']}`", "",
      "Counts: " + ", ".join(f"{k}={v}" for k, v in sorted(count.items())), "",
      "| ID | Area | Status | Manuscript v1 / companion | Observed in code | Evidence (file:lines) | Impact | Resolution |",
      "|---|---|---|---|---|---|---|---|"]
for it in items:
    md.append("| " + " | ".join(str(it[k]).replace("|", "/") for k in it) + " |")
(OUT / "02_checklist.md").write_text("\n".join(md) + "\n", encoding="utf-8")
print("\n".join(md[:8]))
for it in items:
    print(f"{it['id']:4s} {it['status']:11s} {it['evidence'][:110]}")
