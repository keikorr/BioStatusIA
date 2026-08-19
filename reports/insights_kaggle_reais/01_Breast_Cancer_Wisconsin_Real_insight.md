# Insight Clínico em Base Real Kaggle — 01_Breast_Cancer_Wisconsin_Real

**Descrição:** Biópsia Mamária por Agulha Fina (WBCD 569 amostras reais)  
**Modo Detectado no BioStatusIA:** `tabular`  

## 📊 Features & Biomarcadores Reais
* **Features Extraídas:** 31
* **Top Feature SHAP:** id (Top Correlação)
* **Biomarcadores Principais:** id, diagnosis, radius_mean, texture_mean, perimeter_mean

## 🤖 Desempenho AutoML Real (5-Fold CV)
* **Modelo Vencedor:** `RandomForest`
* **AUC:** 1.0000 | **Sensibilidade:** 0.9091 | **Especificidade:** 1.0000
* **F1-Score:** 0.9524 | **MCC:** 0.9293 | **ECE:** 0.0938

## 🩺 Parecer dos Agentes IA
Laudo Preliminar em Markdown para o Dataset `dataset.csv`:

### cabeçalho
- Número de amostras: 569
- Número de features: 31

### Features mais discriminativas
| Feature | Média | Mediana | Desvio | Min | Max |
|---|---|---|---|---|---|
| radius_mean | 14.1273 | 13.37 | 3.521 | 6.981 | 28.11 |
| texture_mean | 19.2896 | 18.84 | 4.2973 | 9.71 | 39.28 |
| perimeter_mean | 91.969 | 86.24 | 24.2776 | 43.79 | 188.5 |
| area_mean | 654.8891 | 551.1 | 351.6048 | 143.5 | 2501.0 |
| smoothness_mean | 0.0964 | 0.0959 | 0.0141 | 0.0526 | 0.1634 |
| concavity_mean | 0.0888 | 0.0615 | 0.0796 | 0.0 | 0.4268 |
| concave points_mean | 0.0489 | 0.0335 | 0.0388 | 0.0 | 0.2012 |
| symmetry_mean | 0.1812 | 0.1792 | 0.0274 | 0.106 | 0.304 |

### Interpretação preliminar
As features mais discriminativas para o diagnóstico de câncer de mama são `radius_mean`, `texture_mean`, `perimeter_mean`, `area_mean`, `smoothness_mean`, `concavity_mean`, `concave points_mean`, e `symmetry_mean`. Essas features têm médias significativamente diferentes entre as classes de diagnóstico (benigno vs maligno), indicando que elas podem ser úteis para a detecção precoce do câncer de mama.

### Rodapé
**Aviso Ético**: Este laudo preliminar não substitui a avaliação médica. As informações fornecidas devem ser consideradas em conjunto com a avaliação de um profissional de saúde qualificado.
