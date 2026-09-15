# SPEC — Arquitetura e Especificações Técnicas (Paper A)

> Documenta as especificações técnicas, modelos matemáticos e **dados experimentais autorizados**
> para a pesquisa. Nenhum valor numérico pode aparecer nas seções `.tex` sem constar aqui.

---

## 1. Ferramentas e Tecnologias Autorizadas

### 1.1 Documento
- **Formatação:** IEEEtran LaTeX (`\documentclass[conference]{IEEEtran}`)
- **Compilador Recomendado:** `pdflatex` / `latexmk`
- **Gestão de Citações:** BibTeX (`IEEEtran.bst`)

### 1.2 Sistema sob estudo (BioStatusIA v3)

| Componente | Tecnologia | Observação |
|---|---|---|
| Linguagem | Python 3.11 (`>=3.10,<3.13`) | gerenciador `uv` |
| Leitura F1 | `mne`, `wfdb`, `scipy` | `.edf/.bdf`, `.dat/.hea`, `.mat` |
| Leitura F1 (espirometria) | ElementTree | `.xml` |
| Leitura F1 (movimento/PSG) | `bioread` | `.c3d` |
| Leitura F3 | `pydicom` | `.dcm` |
| Leitura F4 | `nibabel`, `SimpleITK` | `.nii/.nii.gz`, `.mha` |
| Imagem 2D | OpenCV, scikit-image | PNG/JPG/BMP/TIF |
| Tabular | parser próprio | CSV/TXT/TSV |
| Limite de upload | `MAX_CONTENT_LENGTH = 4 GiB` | requisito de volumes 3D |

---

## 2. Arquitetura do Pipeline

### 2.1 Cadeia de processamento (escopo do Paper A)

```
raw input (file | directory | archive)
   → detectar_estrutura()            [9 modes]
   → schema validation (Pydantic)    [pipeline/ingestao.py]
   → carregar_sinal()                [dispatcher → family reader]
   → SinalNormalizado                [unified data contract]
   → adaptive preprocessing          [analise_base.py + preprocessamento.py]
   → multi-domain feature extraction [extracao*.py / dados_tabulares.py]
   → feature vector                  ► handed to the modeling stage (Paper B)
```

### 2.2 Modos de entrada detectados automaticamente (9)

| Modo | Critério de detecção | Família resultante |
|---|---|---|
| `imagem_unica` | um arquivo `.png/.jpg/.bmp/.tif` | Imagem 2D |
| `imagens_soltas` | diretório/ZIP com imagens sem pastas-rótulo | Imagem 2D |
| `dataset_rotulado` | diretório com subpastas de rótulo (busca recursiva) | Imagem 2D |
| `tabular` | CSV/TXT/TSV único ou diretório só com tabulares | Tabular |
| `multimodal` | imagens **e** tabulares no mesmo diretório | Imagem 2D + Tabular |
| `sinal_temporal` | `.dat/.hea/.edf/.bdf/.mat/.xml/.c3d` | F1 |
| `imagem_dicom_2d` | `.dcm` único | F3 |
| `volume_3d` | `.nii/.nii.gz/.mha` ou diretório com ≥ 10 `.dcm` | F4 |
| `multimodal_expandido` | mistura de imagens, sinais e tabulares | múltiplas |

Pastas reconhecidas como rótulo (busca recursiva):
`{benign, benigno, normal, negative, 0}` e `{malignant, malign, maligno, abnormal, positive, 1}`.

### 2.3 Contrato de dados unificado — `SinalNormalizado`

| Campo | Tipo | Papel |
|---|---|---|
| `familia` | `str` | `"F1" \| "F3" \| "F4"` |
| `tipo` | `str` | `"ECG" \| "EEG" \| "Raio-X" \| "TC" \| ...` |
| `dados` | `np.ndarray` | array bruto |
| `taxa_amostragem` | `float` | Hz (0 quando não aplicável) |
| `canais` | `list[str]` | rótulos de canal |
| `metadados` | `dict` | cabeçalho da fonte (ex.: tags DICOM) |
| `caminho_original` | `str` | proveniência |
| `dados_viz` | `list` | série reduzida a ≤ 2000 pontos para visualização |

**Invariante:** todo leitor retorna `SinalNormalizado`; todo extrator consome `SinalNormalizado`.
Leitores e extratores nunca se conhecem diretamente.

### 2.4 Detecção de esquema tabular

1. Coluna-rótulo por nome: `label`, `class`, `diagnosis`, `target`, `outcome`, `y`, `categoria`, `resultado`.
2. Fallback: última coluna com 2–10 valores únicos.
3. Separador inferido entre `,`, `;`, `\t`, `|`; encoding UTF-8 com fallback Latin-1.

---

## 3. Formulações Matemáticas Autorizadas

Somente as equações abaixo podem aparecer na Seção 2.E / Seção 3. Nenhuma métrica de classificação
é autorizada neste artigo.

| Id | Grandeza | Definição |
|---|---|---|
| EQ-1 | RMS de um sinal discreto | $\mathrm{RMS}=\sqrt{\frac{1}{N}\sum_{i=1}^{N}x_i^{2}}$ |
| EQ-2 | Densidade espectral de potência (Welch) | média dos periodogramas de segmentos sobrepostos e janelados |
| EQ-3 | Potência relativa de banda EEG | $P_b=\int_{f_1}^{f_2}S(f)\,df \big/ \int_{f_{\min}}^{f_{\max}}S(f)\,df$ |
| EQ-4 | RMSSD (HRV) | $\mathrm{RMSSD}=\sqrt{\frac{1}{N-1}\sum_{i=1}^{N-1}(RR_{i+1}-RR_i)^2}$ |
| EQ-5 | SDNN (HRV) | desvio-padrão dos intervalos RR |
| EQ-6 | pNN50 | fração de intervalos RR sucessivos com diferença > 50 ms |
| EQ-7 | Entropia GLCM | $H=-\sum_{i,j}p(i,j)\log p(i,j)$ |
| EQ-8 | Homogeneidade GLCM | $\sum_{i,j}\frac{p(i,j)}{1+|i-j|}$ |
| EQ-9 | Contraste GLCM | $\sum_{i,j}(i-j)^2 p(i,j)$ |
| EQ-10 | Energia GLCM | $\sum_{i,j}p(i,j)^2$ |
| EQ-11 | Circularidade | $4\pi A/P^{2}$ |
| EQ-12 | Solidez | $A/A_{\text{convex hull}}$ |
| EQ-13 | Esfericidade 3D | $\pi^{1/3}(6V)^{2/3}/S$ |
| EQ-14 | Razão FEV1/FVC | quociente espirométrico |
| EQ-15 | SNR em dB | $10\log_{10}(P_{\text{sinal}}/P_{\text{ruído}})$ |

---

## 4. Dados Empíricos Autorizados

> **Fonte primária:** `reports/relatorio_comparativo_30_bases.md` (BioStatusIA v3, execução de
> 28/07/2026) e `reports/insights_por_base/*.md`.
> **Somente as colunas de ingestão e engenharia de features estão autorizadas neste artigo.**
> As colunas de modelo vencedor, AUC, sensibilidade, especificidade, ECE e latência do relatório
> original são **reservadas ao Paper B** e não podem ser citadas aqui.

### 4.1 Composição do benchmark

30 bases biomédicas reais, distribuídas em cinco famílias:

| Família | Bases | Faixa |
|---|---|---|
| F1 — Sinais temporais | 6 | 01–06 |
| F3 — DICOM 2D | 6 | 07–12 |
| F4 — Volume 3D | 6 | 13–18 |
| Tabular clínico | 6 | 19–24 |
| Imagem comum 2D | 6 | 25–30 |

### 4.2 Modo detectado e dimensionalidade do vetor de features

| # | Base | Família | Modo detectado | Nº de features |
|---:|---|:---:|:---:|---:|
| 01 | PTB_XL_ECG | F1 | `sinal_temporal` | 18 |
| 02 | MIT_BIH_Arrhythmia | F1 | `sinal_temporal` | 18 |
| 03 | CHB_MIT_EEG | F1 | `sinal_temporal` | 18 |
| 04 | EMG_Physical_Action | F1 | `tabular` | 18 |
| 05 | CAP_Sleep_PSG | F1 | `sinal_temporal` | 18 |
| 06 | Spirometry_COPD | F1 | `tabular` | 18 |
| 07 | NIH_ChestXray14 | F3 | `imagem_dicom_2d` | 14 |
| 08 | CBIS_DDSM_Mammography | F3 | `imagem_dicom_2d` | 14 |
| 09 | CheXpert_Chest | F3 | `imagem_dicom_2d` | 14 |
| 10 | RSNA_Pneumonia | F3 | `imagem_dicom_2d` | 14 |
| 11 | INbreast_Mammography | F3 | `imagem_dicom_2d` | 14 |
| 12 | VinDr_CXR | F3 | `imagem_dicom_2d` | 14 |
| 13 | BraTS_Brain_MRI_3D | F4 | `volume_3d` | 22 |
| 14 | LIDC_IDRI_Lung_CT_3D | F4 | `volume_3d` | 22 |
| 15 | LiTS_Liver_CT_3D | F4 | `volume_3d` | 22 |
| 16 | IXI_Brain_MRI_3D | F4 | `volume_3d` | 22 |
| 17 | OASIS3_Brain_PET_3D | F4 | `volume_3d` | 22 |
| 18 | ProstateX_MRI_3D | F4 | `volume_3d` | 22 |
| 19 | UCI_Heart_Disease | Tabular | `tabular` | 6 |
| 20 | Breast_Cancer_Wisconsin | Tabular | `tabular` | 30 |
| 21 | PIMA_Diabetes | Tabular | `tabular` | 6 |
| 22 | Parkinsons_Biomarkers | Tabular | `tabular` | 16 |
| 23 | Chronic_Kidney_Disease | Tabular | `tabular` | 5 |
| 24 | Stroke_Prediction | Tabular | `tabular` | 5 |
| 25 | BUSI_Breast_Ultrasound | Imagem 2D | `dataset_rotulado` | 12 |
| 26 | HAM10000_Dermatology | Imagem 2D | `dataset_rotulado` | 12 |
| 27 | BreakHis_Histopathology | Imagem 2D | `dataset_rotulado` | 12 |
| 28 | DRIVE_Retinal_Fundus | Imagem 2D | `imagens_soltas` | 12 |
| 29 | BCCD_Blood_Cells | Imagem 2D | `dataset_rotulado` | 12 |
| 30 | COVID19_Radiography | Imagem 2D | `dataset_rotulado` | 12 |

**Observações autorizadas sobre a Tabela 4.2:**
- As 30 entradas foram processadas sem exceções não tratadas (conclusão 1 do relatório-fonte).
- Duas bases da família F1 (04 e 06) foram detectadas como `tabular` porque são distribuídas em
  formato CSV, e não em formato de sinal nativo. Este é um resultado a ser **discutido**, não
  ocultado: evidencia que a detecção opera sobre a estrutura física do dado, não sobre a
  semântica clínica declarada.
- A base 28 foi detectada como `imagens_soltas` (ausência de pastas-rótulo), enquanto as demais
  bases de imagem 2D foram detectadas como `dataset_rotulado`.

### 4.3 Dimensionalidade por família (derivada da Tabela 4.2)

| Família | Nº de features |
|---|---|
| F1 | 18 (constante nas 6 bases) |
| F3 | 14 (constante nas 6 bases) |
| F4 | 22 (constante nas 6 bases) |
| Imagem 2D | 12 (constante nas 6 bases) |
| Tabular | variável, 5–30 (depende do esquema da base) |

### 4.4 Descritores efetivamente extraídos por família

| Família | Descritores reportados |
|---|---|
| F1 | FC_bpm, RMSSD, SDNN, pNN50, potência espectral por banda (Welch), estatísticas de tempo |
| F3 | faixa de Hounsfield Units, densidade alta (%), gradiente médio, uniformidade, descritores GLCM |
| F4 | volume de lesão (mm³), esfericidade 3D, GLCM em três planos ortogonais (axial, coronal, sagital) |
| Tabular | variáveis clínicas nativas da base (ex.: `age`, `Glucose`, `bp`, `hemo`) |
| Imagem 2D | entropia GLCM, contraste GLCM, solidez, circularidade |

### 4.5 Pré-processamento adaptativo — regras de decisão (constantes de implementação)

Fonte: `pipeline/analise_base.py::decidir_estrategia` e `pipeline/preprocessamento.py::preprocessar_adaptativo`.
São **constantes do código**, não medições experimentais — podem ser citadas como especificação.

| Propriedade medida na base | Condição | Operação selecionada | Alternativa (caso contrário) |
|---|---|---|---|
| Ruído médio | > 0,05 | Non-Local Means (`h=0.1`, `patch_size=5`, `patch_distance=6`) | Gaussian blur 5×5 |
| Fração de imagens outlier em intensidade | > 10% da base | Normalização por percentil 1–99 | Normalização min–max |
| Contraste médio | < 30 | CLAHE (`clipLimit=2.0`, `tileGridSize=8×8`) | sem equalização |
| Redimensionamento | sempre | 256×256 | — |

Cada decisão registra uma justificativa textual gerada automaticamente, contendo o valor medido que
disparou a regra.

### 4.6 Nomes de descritores efetivamente implementados

Fonte: chaves de saída de `extracao_temporal.py`, `extracao_dicom.py`, `extracao_volumetrica.py` e `extracao.py`.

| Família | Descritores (nomes de implementação) |
|---|---|
| F1 — tempo | `rms`, `media`, `desvio_padrao`, `assimetria`, `curtose`, `amplitude_pico_pico`, `amplitude_max`, `snr_db` |
| F1 — frequência | `potencia_total`, `centroide_espectral_hz`, `frequencia_dominante_hz`, `frequencia_mediana_hz`, bandas `banda_0_5hz`, `banda_5_15hz`, `banda_15_50hz`, `banda_50_150hz` |
| F1 — EEG | `delta_0_4hz`, `theta_4_8hz`, `alfa_8_13hz`, `beta_13_30hz`, `gama_30_100hz` |
| F1 — ECG | `n_picos_r`, `fc_media_bpm`, `rr_media_ms`, `rr_desvio_ms`, `hrv_rmssd_ms`, `hrv_sdnn_ms`, `hrv_pnn50_pct` |
| F1 — EMG / espirometria | `rms_emg`; `fvc_litros`, `fev1_litros`, `fev1_fvc_ratio`, `pef_l_s` |
| F3 | `circularidade`, `solidez`, `entropia`, `homogeneidade`, `energia`, `contraste`, `snr`, `assimetria`, `curtose`, `densidade_alta_pct`, `gradiente_medio`, `uniformidade`, `modalidade`, `pixel_spacing` |
| F4 | `media_intensidade`, `desvio_intensidade`, `mediana_intensidade`, `percentil_5`, `percentil_95`, `n_voxels_altos`, `fracao_voxels_altos`, GLCM por plano (`axial`, `coronal`, `sagital`), `volume_lesao_mm3`, `sphericity_aprox`, `n_slices_total`, `voxel_size_mm` |
| Imagem 2D | `circularidade`, `solidez`, `entropia`, `homogeneidade`, `energia`, `contraste`, `snr`, `assimetria`, `curtose` |

### 4.7 Outras constantes de implementação autorizadas

- `dados_viz` limitado a 2000 pontos por canal.
- Diretório com `≥ 10` arquivos `.dcm` é tratado como volume 3D.
- Volumes NIfTI são transpostos de (X, Y, Z) para (Z, Y, X), convenção axial-first.
- Janelamento HU derivado das tags `WindowCenter` / `WindowWidth`.
- Shapes por família: F1 `(n_canais, n_amostras)`; F3 `(H, W)`; F4 `(D, H, W)`, float32 em [0,1].

---

## 5. Lacunas a Preencher Antes da Submissão

Itens marcados com `[PENDENTE]` nas seções `.tex` dependem de medição adicional e **não podem ser
estimados**:

- `[PENDENTE-T1]` Tempo de ingestão por família (segundos por amostra) — requer instrumentação.
- `[PENDENTE-T2]` Pico de memória em F4 — requer instrumentação.
- `[PENDENTE-T3]` Número de amostras efetivamente processadas por base.
- `[PENDENTE-T4]` Especificação de hardware do ambiente experimental (CPU, RAM, SO).
- `[PENDENTE-T5]` Versões exatas das bibliotecas de leitura (`mne`, `wfdb`, `pydicom`, `nibabel`, `SimpleITK`).
