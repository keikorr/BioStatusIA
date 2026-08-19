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
```markdown
# Laudo Preliminar: Dataset de Predição de Cerebroacidente (Cerebroacidente vs Não Cerebroacidente)

## Resumo do Dataset
- **Nº de amostras**: 5110
- **Nº de features numéricas**: 6

## Features Mais Discriminativas

| Feature | Média (Média) | Média (Mediana) | Desvio | Min | Max |
|---|---|---|---|---|---|
| id | 36517.83 | 36932.0 | 21159.65 | 67.0 | 72940.0 |
| age | 43.23 | 45.0 | 22.61 | 0.08 | 82.0 |
| hypertension | 0.0975 | 0.0 | 0.2966 | 0.0 | 1.0 |
| heart_disease | 0.054 | 0.0 | 0.226 | 0.0 | 1.0 |
| avg_glucose_level | 106.15 | 91.89 | 45.28 | 55.12 | 271.74 |
| stroke | 0.0487 | 0.0 | 0.2153 | 0.0 | 1.0 |

### Observações
- A feature mais discriminativa é `avg_glucose_level` com uma média de 106.15 e um desvio padrão de 45.28, indicando uma grande variação entre os valores.
- A feature `age` também é discriminativa, com uma média de 43.23.
- A feature `heart_disease` tem uma média muito baixa (0.054), indicando que a maioria dos pacientes não tem doença cardíaca.
- A feature `hypertension` tem uma média de 0.0975, indicando que cerca de 10% dos pacientes têm hipertensão.
- A feature `stroke` tem uma média muito baixa (0.0487), indicando que a maioria dos pacientes não tem histórico de cerebroacidente.

## Interpretação Preliminar

- A feature `avg_glucose_level` é a mais discriminativa, indicando que a média de glicose no sangue pode ser um bom indicador para predição de cerebroacidente.
- A feature `age` também é importante, pois a idade pode ser um fator de risco para o desenvolvimento de cerebroacidente.
- A feature `heart_disease` e `hypertension` são fatores de risco conhecidos para cerebroacidente e devem ser considerados em qualquer análise.
- A feature `stroke` é muito baixa, indicando que a maioria dos pacientes não tem histórico de cerebroacidente.

## Conclusão

Os dados sugerem que a média de glicose no sangue (`avg_glucose_level`) e a idade (`age`) são os principais fatores de risco para o desenvolvimento de cerebroacidente. A presença de doença cardíaca (`heart_disease`) e hipertensão (`hypertension`) também é um fator de risco. No entanto, é importante notar que a presença de histórico de cerebroacidente (`stroke`) é muito baixa, indicando que a maioria dos pacientes não tem histórico de cerebroacidente.

### Aviso Ético
Este laudo preliminar não substitui a avaliação médica. As informações fornecidas devem ser consideradas em conjunto com a avaliação clínica e outros testes para uma decisão de tratamento adequada.
```

### Aviso Ético
Este laudo preliminar não substitui a avaliação médica. As informações fornecidas devem ser consideradas em conjunto com a avaliação clínica e outros testes para uma decisão de tratamento adequada.
