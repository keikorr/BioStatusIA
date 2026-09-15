# MASTER SPECIFICATION INDEX (Master Spec)

> **NOTICE:** This document is the master source of truth for the author and AI co-authors.
> Any technical or academic information not recorded in this file or inside the `specs/` directory must be treated as unverified and requires explicit confirmation from the author.

---

## 1. DOCUMENT IDENTIFICATION

| Field | Value |
|---|---|
| **Title** | A Modality-Agnostic Ingestion and Multi-Domain Feature Engineering Pipeline for Heterogeneous Biomedical Data |
| **Short Title / Internal ID** | Paper A — Input-to-Features |
| **Author(s)** | [Insert Author Name(s)] |
| **Advisor / Co-author** | [Insert Advisor / Co-author Name] |
| **Institution** | [Insert Institution / University Name] |
| **Department** | [Insert Department / Center] |
| **Year / Date** | 2026 |
| **Format & Language** | IEEE Conference / Article Format — **Language: English** |
| **Companion Paper** | Paper B — AutoML evaluation and AI-assisted reporting (out of scope here) |

---

## 2. CONTEXT AND MOTIVATION

Clinical Decision Support Systems (CDSS) for biomedical data are typically built around a single
modality: a pipeline is designed for electrocardiography, or for chest radiography, or for tabular
clinical records, and its ingestion and feature-extraction stages are hard-coded to that modality.
When an institution holds heterogeneous data — physiological time series, 2D DICOM studies, 3D
volumes and tabular clinical variables — each modality demands a separate engineering effort, and
no shared representation exists across them.

This work addresses the stage that precedes any modeling: **how raw, arbitrarily structured
biomedical input is detected, validated, read, preprocessed and converted into a feature vector**.
The proposed system, BioStatusIA v3, automatically infers the structure of an arbitrary input
directory or file, dispatches it to a family-specific reader, normalizes every modality into a single
data contract (`SinalNormalizado`), applies modality-aware preprocessing, and extracts a
multi-domain feature set.

Three signal families plus tabular data are in scope:

| Family | Types | Reading libraries |
|---|---|---|
| **F1 — Temporal signals** | ECG, EEG, EMG, EOG, PPG, blood pressure, spirometry | `mne`, `wfdb`, `scipy` |
| **F3 — 2D DICOM imaging** | Radiography, mammography, static ultrasound | `pydicom` |
| **F4 — 3D volumes** | CT, MRI, PET/SPECT | `nibabel`, `SimpleITK` |
| **Tabular** | Multimodal clinical variables | Custom schema parser |
| **Plain 2D imaging** | Non-DICOM images (PNG/JPG/BMP/TIF) | OpenCV, scikit-image |

**Scope boundary (immutable):** this paper ends when the feature vector is ready. Classifier
training, model selection, calibration and AI-generated reporting belong to the companion paper
(Paper B) and MUST NOT be developed here beyond a forward reference.

---

## 3. OBJECTIVES (IMMUTABLE)

### 3.1 General Objective
To design, implement and empirically evaluate a modality-agnostic ingestion and feature-engineering
pipeline that automatically detects the structure of heterogeneous biomedical input, normalizes it
into a single data contract, and produces a classifier-ready multi-domain feature vector without
manual reconfiguration.

### 3.2 Specific Objectives
- **SO-1:** Formalize an automatic input-structure detection mechanism covering nine input modes
  (single image, loose images, labeled dataset, tabular, multimodal, temporal signal, 2D DICOM,
  3D volume, expanded multimodal) and validate it through schema-level input validation.
- **SO-2:** Define a unified data contract (`SinalNormalizado`) that decouples family-specific
  readers from family-specific extractors, and demonstrate that it supports F1, F3, F4, tabular and
  plain 2D imaging without contract changes.
- **SO-3:** Specify an adaptive preprocessing stage whose operations and justifications are selected
  from measurable properties of the input rather than from a fixed, modality-specific configuration.
- **SO-4:** Characterize the multi-domain feature set produced per family — time domain, frequency
  domain, GLCM texture, morphology, 3D radiomics and DICOM-specific descriptors — and report
  feature-vector dimensionality per family.
- **SO-5:** Empirically evaluate ingestion robustness and feature coverage over 30 real biomedical
  benchmark datasets spanning all families in scope, reporting detection outcome and feature count
  per dataset.

---

## 4. SPECIFICATION MODULE INDEX (`specs/` directory)

| Module | File | Main Content | When to read |
|---|---|---|---|
| **Sections & Scope** | `specs/secoes.md` | `.tex` structure and section scope boundaries | When writing or revising sections |
| **References** | `specs/referencias.md` | Authorized seed list and BibTeX addition rules | When citing or adding sources |
| **Architecture & Parameters** | `specs/arquitetura.md` | Technical specifications, formulas, diagrams, and empirical metrics | When drafting methodology & results |

---

## 5. VALIDATION CHECKLIST

Before approving text changes or generating paragraphs, verify:
- [ ] Is the generated content strictly within the scope defined in `specs/secoes.md`?
- [ ] Are all cited sources listed in `specs/referencias.md`?
- [ ] Are all numerical values backed by real experimental data (no invented numbers)?
- [ ] Is the text written in formal, academic English?
- [ ] Does the content stay **before** the modeling stage (no AutoML results, no model ranking, no
      AUC/sensitivity/specificity/ECE values, no AI-generated report content — those belong to Paper B)?
- [ ] Is every empirical value traceable to `specs/arquitetura.md`, Section 4 (Authorized Empirical Data)?
