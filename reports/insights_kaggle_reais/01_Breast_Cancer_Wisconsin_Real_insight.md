# Insight Clínico em Base Real Kaggle — 01_Breast_Cancer_Wisconsin_Real

**Descrição:** Biópsia Mamária por Agulha Fina (WBCD 569 amostras reais)  
**Modo Detectado no BioStatusIA:** `tabular`  

## 📊 Features & Biomarcadores Reais
* **Features Extraídas:** 31
* **Top Feature SHAP:** id (Top Correlação)
* **Biomarcadores Principais:** id, diagnosis, radius_mean, texture_mean, perimeter_mean

## 🤖 Desempenho AutoML Real (5-Fold CV)
* **Modelo Vencedor:** `MLP`
* **AUC:** 0.9927 | **Sensibilidade:** 0.9524 | **Especificidade:** 1.0000
* **F1-Score:** 0.9756 | **MCC:** 0.9636 | **ECE:** 0.0281

## 🩺 Parecer dos Agentes IA
# Laudo Preliminar: Dataset Wisconsin Breast Cancer

## Resumo do Dataset
- **N Amostras**: 569
- **N Features**: 31
- **Coluna-rótulo**: `diagnosis`
- **Mapa de rótulos**: B→0, M→1
- **Distribuição de classes**: classe 0: 357, classe 1: 212

## Features mais discriminativas

| Feature | Média (Benigno) | Média (Maligno) | Diferença (Maligno - Benigno) | Diferença (%) |
|---|---|---|---|---|
| radius_mean | 13.37 | 14.1273 | -0.7573 | -5.64% |
| texture_mean | 18.84 | 19.2896 | -0.4496 | -2.39% |
| perimeter_mean | 86.24 | 91.969 | -5.729 | -6.56% |
| area_mean | 551.1 | 654.8891 | -103.7891 | -18.84% |
| smoothness_mean | 0.0959 | 0.0964 | -0.0005 | -0.05% |
| compactness_mean | 0.0926 | 0.1043 | 0.0117 | 12.86% |
| concavity_mean | 0.0615 | 0.0888 | 0.0273 | 44.23% |
| concave points_mean | 0.0335 | 0.0489 | 0.0154 | 45.75% |
| symmetry_mean | 0.1792 | 0.1812 | 0.0020 | 1.08% |
| fractal_dimension_mean | 0.0528 | 0.0964 | 0.0436 | 82.08% |
| worst_radius_mean | 28.11 | 14.1273 | 13.9827 | 49.56% |
| worst_texture_mean | 39.28 | 19.2896 | 19.9904 | 51.49% |
| worst_perimeter_mean | 188.5 | 91.969 | 96.531 | 51.56% |
| worst_area_mean | 2501.0 | 654.8891 | -1846.1199 | -73.83% |
| worst_smoothness_mean | 0.1634 | 0.0964 | -0.0670 | -41.03% |
| worst_compactness_mean | 0.3454 | 0.1043 | -0.2411 | -69.98% |
| worst_concavity_mean | 0.4268 | 0.0888 | -0.3380 | -78.98% |
| worst_concave_points_mean | 0.2012 | 0.0489 | -0.1523 | -75.69% |
| worst_symmetry_mean | 0.304 | 0.1812 | -0.1228 | -39.93% |
| worst_fractal_dimension_mean | 0.304 | 0.0528 | -0.2512 | -81.96% |

### Observação
Os valores de `worst_radius_mean`, `worst_texture_mean`, `worst_perimeter_mean`, `worst_area_mean`, `worst_smoothness_mean`, `worst_compactness_mean`, `worst_concavity_mean`, `worst_concave_points_mean`, `worst_symmetry_mean` e `worst_fractal_dimension_mean` apresentam uma grande diferença entre as classes, indicando que essas características podem ser muito discriminativas para distinguir entre benigno e maligno.

### Balanceamento do Dataset
O dataset está desbalanceado, com uma proporção de 357 (benigno) a 212 (maligno), ou aproximadamente 1.66 a 1. (357/212). Este desequilíbrio pode influenciar os resultados da análise estatística, especialmente em relação à detecção de padrões de correlação entre as classes.

### Sugestão de Correlação Clínica Preliminar
Baseado nos resultados, algumas sugestões de correlação clínica preliminar são:

- **`worst_radius_mean` e `worst_texture_mean`**: Estas características podem indicar uma maior presença de células cancerígenas em células malignas, o que pode ser um sinal de alerta para o médico.
- **`worst_perimeter_mean` e `worst_area_mean`**: Estas características podem indicar uma maior extensão do tumor em células malignas, o que pode ser um sinal de alerta para o médico.
- **`worst_smoothness_mean`, `worst_compactness_mean`, `worst_concavity_mean`, `worst_concave_points_mean`, `worst_symmetry_mean` e `worst_fractal_dimension_mean`**: Estas características podem indicar uma maior complexidade e irregularidade do tumor em células malignas, o que pode ser um sinal de alerta para o médico.

### Aviso Ético
Este laudo preliminar não substitui a avaliação médica. A interpretação estatística deve ser realizada em conjunto com a avaliação clínica e outros exames complementares para uma decisão diagnóstica precisa.
