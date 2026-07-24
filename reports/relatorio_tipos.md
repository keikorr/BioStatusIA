# Relatório — Pipeline por Tipo de Dado (sem LLM)

Valida leitura → extração de biomarcadores → AutoML (`treinar_vetores`) para cada família.

## 1. Imagem comum (radiômica) — Mini-BUSI
- Imagens rotuladas processadas: **100** (de 100)
- Exemplo de biomarcadores (1ª imagem): [('circularidade', 0.0101), ('solidez', 0.864)]
- AutoML OK — melhor: **MLP** | AUC=0.94 Sens=0.9 Espec=0.9 F1=0.9 MCC=0.8 Kappa=0.8

## 2. Tabular — WBCD-50
- Coluna-rótulo detectada: **diagnosis** | features: 30 | amostras: 50
- AutoML OK — melhor: **LogisticRegression** | AUC=1.0 Sens=1.0 Espec=1.0 F1=1.0 MCC=1.0 Kappa=1.0

## 3. F1 — Sinal Temporal (ECG sintético)
- Sinais processados: **14** | tipo detectado: Sinal/MATLAB
- Grupos de features: ['tempo', 'frequencia']
- Dimensão do vetor de features: 14
- AutoML OK — melhor: **LogisticRegression** | AUC=1.0 Sens=1.0 Espec=1.0 F1=1.0 MCC=1.0 Kappa=1.0

## 4. F3 — DICOM 2D (TC sintético)
- Sinais processados: **14** | tipo detectado: Tomografia Computadorizada
- Grupos de features: ['morfologia', 'textura_glcm', 'distribuicao_intensidade', 'radiomico_dicom']
- Dimensão do vetor de features: 15
- AutoML OK — melhor: **LogisticRegression** | AUC=1.0 Sens=1.0 Espec=1.0 F1=1.0 MCC=1.0 Kappa=1.0

## 5. F4 — Volume 3D (NIfTI sintético)
- Sinais processados: **14** | tipo detectado: RM/TC NIfTI
- Grupos de features: ['volumetrico_global', 'textura_3d', 'morfologia_3d']
- Dimensão do vetor de features: 13
- AutoML OK — melhor: **LogisticRegression** | AUC=1.0 Sens=1.0 Espec=1.0 F1=1.0 MCC=1.0 Kappa=1.0
