# Insight Clínico & Técnico — 24_Stroke_Prediction

**Família:** Tabular  
**Descrição:** Histórico Clínico e Fatores de Risco para AVC  
**Modo Detectado no BioStatusIA:** `tabular`  

---

## 📊 Engenharia de Features & Biomarcadores
* **Total de Features Extraídas:** 5
* **Principais Biomarcadores:** age, hypertension, heart_disease, avg_glucose_level, bmi
* **Feature de Maior Relevância (SHAP/Tree):** age (Top Correlation)
* **Estratégia de Pré-Processamento:** Escalamento: robust, Imputação: none

---

## 🤖 Desempenho do AutoML (6 Modelos Concorrentes)
* **Modelo Vencedor:** `RandomForest`
* **AUC:** 0.9333
* **Sensibilidade (Recall):** 0.3333
* **Especificidade:** 1.0000
* **Acurácia:** 0.7500
* **F1-Score:** 0.5000
* **Coeficiente MCC:** 0.4880
* **Erro de Calibração (ECE):** 0.1988
* **Latência de Inferência:** 0.69 ms
* **Tempo de Treino:** 0.10 s

---

## 🩺 Síntese Diagnóstica da IA
**Síntese Bioestatística:** O dataset tabular '24_Stroke_Prediction' apresentou 40 amostras e 5 atributos clínicos. O classificador **RandomForest** obteve AUC de 0.93 e Sensibilidade de 0.33, demonstrando alto valor preditivo com baixo ECE (0.199).
