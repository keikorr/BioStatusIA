# SPEC — Referências Bibliográficas (Paper A)

> Define a lista de referências autorizadas (seed list) e o protocolo para inclusão de novas obras.
>
> **REGRA CRÍTICA (AGENTS.md §1):** nenhuma referência pode ser inventada. As entradas abaixo estão
> classificadas por status. Apenas entradas com status `CONFIRMADA` podem ser citadas no texto final.
> Entradas `A VERIFICAR` são **candidatas** indicadas pelo tema — o autor deve recuperar o BibTeX
> oficial (DOI, volume, páginas) antes de promovê-las.

## Status

| Status | Significado |
|---|---|
| `CONFIRMADA` | BibTeX completo recuperado da fonte oficial e conferido pelo autor |
| `A VERIFICAR` | Obra candidata pelo tema; metadados ainda não conferidos — **não citar** |
| `REJEITADA` | Descartada (fora de escopo ou não localizada) |

## Seed List — Candidatas por Eixo Temático

### Eixo 1 — Radiômica e features handcrafted em imagem médica

| Chave sugerida | Obra candidata | Uso previsto | Status |
|---|---|---|---|
| `haralick1973` | Haralick et al., "Textural Features for Image Classification", IEEE Trans. Syst. Man Cybern. | Base formal do GLCM (EQ-7 a EQ-10) | A VERIFICAR |
| `lambin2012` | Lambin et al., "Radiomics: extracting more information from medical images…", Eur. J. Cancer | Definição de radiômica | A VERIFICAR |
| `vangriethuysen2017` | van Griethuysen et al., "Computational Radiomics System to Decode the Radiographic Phenotype" (PyRadiomics), Cancer Research | Comparação com extrator de referência | A VERIFICAR |
| `zwanenburg2020` | Zwanenburg et al., "The Image Biomarker Standardisation Initiative (IBSI)", Radiology | Padronização de biomarcadores de imagem | A VERIFICAR |

### Eixo 2 — Processamento de sinais fisiológicos

| Chave sugerida | Obra candidata | Uso previsto | Status |
|---|---|---|---|
| `welch1967` | Welch, "The use of FFT for the estimation of power spectra", IEEE Trans. Audio Electroacoust. | Base do PSD (EQ-2) | A VERIFICAR |
| `goldberger2000` | Goldberger et al., "PhysioBank, PhysioToolkit, and PhysioNet", Circulation | Origem das bases F1 e do formato WFDB | A VERIFICAR |
| `gramfort2013` | Gramfort et al., "MEG and EEG data analysis with MNE-Python", Front. Neurosci. | Biblioteca de leitura F1 | A VERIFICAR |
| `taskforce1996hrv` | Task Force of the ESC/NASPE, "Heart rate variability: standards of measurement…", Circulation | Definição de RMSSD, SDNN, pNN50 (EQ-4 a EQ-6) | A VERIFICAR |

### Eixo 3 — Formatos, padrões e bibliotecas de ingestão

| Chave sugerida | Obra candidata | Uso previsto | Status |
|---|---|---|---|
| `mason2011pydicom` | Mason, "SU-E-T-33: Pydicom: An Open Source DICOM Library", Medical Physics | Leitura F3 | A VERIFICAR |
| `brett_nibabel` | Brett et al., "nipy/nibabel" (software, Zenodo) | Leitura F4 | A VERIFICAR |
| `lowekamp2013` | Lowekamp et al., "The Design of SimpleITK", Front. Neuroinform. | Leitura F4 (`.mha`) | A VERIFICAR |
| `vanderwalt2014skimage` | van der Walt et al., "scikit-image: image processing in Python", PeerJ | Extração de textura e morfologia 2D | A VERIFICAR |
| `virtanen2020scipy` | Virtanen et al., "SciPy 1.0: fundamental algorithms for scientific computing in Python", Nature Methods | Processamento de sinal | A VERIFICAR |
| `pedregosa2011sklearn` | Pedregosa et al., "Scikit-learn: Machine Learning in Python", JMLR | Escalonamento/consumo do vetor de features | A VERIFICAR |

### Eixo 4 — Arquiteturas de ingestão e interoperabilidade em saúde

| Chave sugerida | Obra candidata | Uso previsto | Status |
|---|---|---|---|
| `[definir]` | Norma DICOM (NEMA PS3) | Padrão de metadados F3 | A VERIFICAR |
| `[definir]` | Especificação HL7 FHIR | Contexto de interoperabilidade | A VERIFICAR |
| `[definir]` | Revisão recente (≥ 2023) sobre pipelines multimodais em CDSS | Posicionamento do estado da arte | A VERIFICAR |
| `[definir]` | Trabalho sobre validação de esquema / contratos de dados em ML | Justificativa da camada Pydantic | A VERIFICAR |

### Eixo 5 — Bases de dados utilizadas no benchmark

Cada uma das 30 bases citadas nominalmente na Seção 4 exige a citação de sua publicação-fonte.
Prioridade para as bases nomeadas explicitamente no texto:
PTB-XL, MIT-BIH Arrhythmia, CHB-MIT, CAP Sleep, NIH ChestXray14, CBIS-DDSM, CheXpert, RSNA
Pneumonia, INbreast, VinDr-CXR, BraTS, LIDC-IDRI, LiTS, IXI, OASIS-3, ProstateX, UCI Heart
Disease, Breast Cancer Wisconsin, PIMA Diabetes, Parkinson's, Chronic Kidney Disease, Stroke
Prediction, BUSI, HAM10000, BreakHis, DRIVE, BCCD, COVID-19 Radiography.

| Status geral do Eixo 5 | A VERIFICAR — nenhuma citação de base pode entrar no `.bib` sem o artigo-fonte oficial |

## Protocolo para Adição de Novas Referências

1. Recuperar o bloco BibTeX completo e válido na fonte oficial (editora, DOI, IEEE Xplore, PubMed).
2. Adicionar o bloco a `referencias/referencias.bib`.
3. Registrar a entrada na tabela do eixo correspondente e alterar o status para `CONFIRMADA`.
4. Só então usar `\cite{chave}` no texto.

## Meta de Volume

Artigo de conferência IEEE: **20–30 referências confirmadas**, com pelo menos 40% publicadas nos
últimos cinco anos.
