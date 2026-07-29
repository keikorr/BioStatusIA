# Insight Clínico & Técnico — 21_PIMA_Diabetes

**Família:** Tabular  
**Descrição:** 8 Atributos Metabólicos e Risco de Diabetes  
**Modo Detectado no BioStatusIA:** `tabular`  

---

## 📊 Engenharia de Features & Biomarcadores
* **Total de Features Extraídas:** 6
* **Principais Biomarcadores:** Glucose, BloodPressure, SkinThickness, Insulin, BMI
* **Feature de Maior Relevância (SHAP/Tree):** Glucose (Top Correlation)
* **Estratégia de Pré-Processamento:** Escalamento: robust, Imputação: none

---

## 🤖 Desempenho do AutoML (6 Modelos Concorrentes)
* **Modelo Vencedor:** `KNN`
* **AUC:** 0.5312
* **Sensibilidade (Recall):** 0.5000
* **Especificidade:** 0.5000
* **Acurácia:** 0.5000
* **F1-Score:** 0.5000
* **Coeficiente MCC:** 0.0000
* **Erro de Calibração (ECE):** 0.1750
* **Latência de Inferência:** 0.13 ms
* **Tempo de Treino:** 0.00 s

---

## 🩺 Síntese Diagnóstica da IA
## Laudo Preliminar: Dataset PIMA Diabetes

### Dados do Dataset
- **Número de amostras**: 40
- **Número de features numéricas**: 6
- **Coluna-rótulo**: `Outcome`
- **Distribuição de classes**:
    - Classe 0 (diabetes negativa): 21 amostras
    - Classe 1 (diabetes positiva): 19 amostras

### Features Mais Discriminativas

| Feature | Média | Mediana | Desvio |
|---|---|---|---|
| Glucose | 142.13 | 140.5 | 37.36 |
| BloodPressure | 80.35 | 84.5 | 12.88 |
| SkinThickness | 28.52 | 26.5 | 12.64 |
| Insulin | 178.25 | 175.5 | 79.23 |
| BMI | 30.12 | 28.12 | 6.94 |

### Interpretação Preliminar

#### Glucose
A média de Glucose para as amostras com diabetes positiva (classe 1) é significativamente maior que a média da população geral, indicando uma possível correlação entre baixas taxas de Glucose e o risco de diabetes. A diferença relativa ao desvio padrão também sugere que esta variável pode ser um bom discriminador.

#### BloodPressure
A BloodPressure para as amostras com diabetes positiva é ligeiramente mais alta, sugerindo uma possível relação entre pressão arterial elevada e a presença de diabetes. No entanto, o desvio padrão é relativamente alto, indicando que esta variável pode não ser tão discriminativa quanto Glucose.

#### SkinThickness
A SkinThickness para as amostras com diabetes positiva é significativamente menor, sugerindo uma possível relação entre baixas taxas de glicemia e a presença de diabetes. A diferença relativa ao desvio padrão também sugere que esta variável pode ser um bom discriminador.

#### Insulin
A Insulin para as amostras com diabetes positiva é significativamente maior, indicando uma possível relação entre altas taxas de insulina e o risco de diabetes. A diferença relativa ao desvio padrão também sugere que esta variável pode ser um bom discriminador.

#### BMI
O BMI para as amostras com diabetes positiva é ligeiramente mais alto, sugerindo uma possível relação entre altos níveis de gordura corporal e o risco de diabetes. No entanto, o desvio padrão é relativamente alto, indicando que esta variável pode não ser tão discriminativa quanto Glucose.

### Conclusão

As features mais discriminativas para a presença de diabetes são Glucose, SkinThickness e Insulin. Estas variáveis sugerem uma possível relação entre baixas taxas de glicemia, baixas taxas de insulina e altos níveis de gordura corporal com o risco de diabetes.

### Aviso Ético

Este laudo preliminar não substitui a avaliação médica. As conclusões são baseadas em evidências estatísticas e devem ser interpretadas cuidadosamente, levando em consideração fatores clínicos adicionais.
