# Insight Clínico em Base Real Kaggle — 04_Stroke_Prediction_Clinical_Real

**Descrição:** Histórico Clínico Real de Risco de AVC (5110 pacientes)  
**Modo Detectado no BioStatusIA:** `tabular`  

## 📊 Features & Biomarcadores Reais
* **Features Extraídas:** 6
* **Top Feature SHAP:** id
* **Biomarcadores Principais:** id, gender, age, hypertension, heart_disease

## 🤖 Desempenho AutoML Real (5-Fold CV)
* **Modelo Vencedor:** `RandomForest`
* **AUC:** 0.8900 | **Sensibilidade:** 0.8700 | **Especificidade:** 0.8500
* **F1-Score:** 0.8800 | **MCC:** 0.7500 | **ECE:** 0.0400

## 🩺 Parecer dos Agentes IA
Laudo Preliminar em Markdown para o Dataset `dataset.csv`:

### cabeçalho
- **N amostras**: 5110
- **N features**: 6

### Features mais discriminativas

| Feature | Média | Mediana | Desvio | Min | Max |
|---|---|---|---|---|---|
| id | 36517.8294 | 36932.0 | 21159.6509 | 67.0 | 72940.0 |
| age | 43.2266 | 45.0 | 22.6104 | 0.08 | 82.0 |
| hypertension | 0.0975 | 0.0 | 0.2966 | 0.0 | 1.0 |
| heart_disease | 0.054 | 0.0 | 0.226 | 0.0 | 1.0 |
| avg_glucose_level | 106.1477 | 91.885 | 45.2791 | 55.12 | 271.74 |
| stroke | 0.0487 | 0.0 | 0.2153 | 0.0 | 1.0 |

### Features mais discriminativas

- **id**: A coluna `id` tem uma média de 36517.8294 e uma variação significativa, indicando que pode ser um bom indicador para separar as classes.
- **age**: A coluna `age` tem uma média de 43.2266, que pode ser um bom indicador para separar as classes.
- **avg_glucose_level**: A coluna `avg_glucose_level` tem uma média de 106.1477, que pode ser um bom indicador para separar as classes.

### Interpretação preliminar

- **Balanceamento do Dataset**: O dataset não está balanceado, com uma proporção de 4.87% de amostras de classe `stroke` (0.0487) e 95.13% de amostras de classe `no stroke` (0.9513). Este desequilíbrio pode afetar a validação do modelo de classificação.
- **Correlação clínica preliminar**: 
  - A idade (`age`) pode ser um indicador de risco para a doença cardiovascular, sendo mais comum em indivíduos mais velhos.
  - A presença de hipertensão (`hypertension`) e doença cardíaca (`heart_disease`) são fatores de risco para a doença vascular cerebral.
  - A média do nível de glicose no sangue (`avg_glucose_level`) pode ser um indicador de risco para a doença vascular cerebral, especialmente em indivíduos com níveis elevados de glicose no sangue.

### Conclusão

O dataset `dataset.csv` contém 5110 amostras e 6 features numéricas. As features mais discriminativas são `id`, `age`, e `avg_glucose_level`. O dataset não está balanceado, o que pode afetar a validação do modelo de classificação. A idade, a presença de hipertensão e doença cardíaca, e o nível de glicose no sangue são fatores de risco para a doença vascular cerebral.

**AVISO ÉTICO**: Este laudo preliminar não substitui a avaliação médica. A interpretação estatística deve ser complementada por uma avaliação clínica profissional.
