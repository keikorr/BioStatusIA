# BioStatusIA audit scripts

Scripts and data that reproduce every audit result in the revised manuscript
"Auditing an AutoML Pipeline for Biomedical Classification: Code-Level
Verification and Re-Analysis of Eight Biomedical Datasets".

None of these scripts trains a model on patient data. They (1) recompute
published numbers from published confusion matrices, (2) check statements
against pinned source code, and (3) analyse calibration of probability
outputs already stored in the project repository.

## Evidence tiers

| Tier | What it is | Script | Inputs |
|---|---|---|---|
| A | Code audit: static checks at a pinned commit | `scripts/02_code_protocol_checklist.py` | BioStatusIA_MultiModal @ `2d89637b`; keikorr/BioStatusIA @ `6960fd60` (lineage) |
| B | Numerical verification of the eight execution reports | `scripts/01_verify_published_metrics.py` | `data/published_values.json` |
| C | Secondary re-analysis (Wilson CIs, PPV/NPV, LRs, per-class recall) | `scripts/01_verify_published_metrics.py` | same |
| D | Calibration of stored out-of-fold probabilities (a different execution) | `scripts/03_calibration_oof.py` | `reports/benchmark_artigo2/resultados.json` @ `6960fd60` (SHA-256 `699cb605…4c48`) |
| E | External validation | **not performed** | — |

## Run

```bash
pip install -r requirements-audit.txt
bash run_all.sh            # clones both repositories at the pinned commits
```

Outputs:

- `outputs/01_verification.{csv,md}`, `outputs/01_derived_measures.json`
- `outputs/02_checklist.{csv,md}`, `outputs/02_checklist_meta.json`
- `outputs/03_calibration_selected.csv`, `outputs/03_calibration_all_models.csv`,
  `outputs/03_parkinsons_grouping.csv`, `figures/fig_reliability.{pdf,png}`

## Pinned sources

| Item | Repository | Commit | Date |
|---|---|---|---|
| Audited code | github.com/JuniorSoares716/BioStatusIA_MultiModal | `2d89637b752e12460954f1d449586e8ec88cf469` | 2026-09-12 |
| Lineage branch | github.com/keikorr/BioStatusIA, `atualizacao_features` | `6960fd60c426e0b2728e0226311ae99399e14c31` | 2026-09-10 |
| Benchmark outputs (OOF) | same, introduced in | `d38e0e4ed3aabc607b9209fbba51595c22ad5c01` | 2026-09-02 (generated 2026-08-30) |

## Limits

- `data/published_values.json` is transcribed from the manuscript tables. Binary
  confusion matrices are reconstructed from N, prevalence, FN and FP; they are
  exact because these four numbers determine the 2x2 table.
- The eight runs stored no per-sample probabilities, partition indices or
  per-run environment. Their calibration therefore cannot be re-estimated
  here; script 03 analyses the only probability outputs that exist, from a
  different execution with different task definitions (see its docstring).
- Script 02 performs static checks only; it does not import or run the
  audited code.
