# Insight Clínico & Técnico — 23_Chronic_Kidney_Disease

**Família:** Tabular  
**Descrição:** 24 Indicadores Sanguíneos e Urinários de Doença Renal  
**Modo Detectado no BioStatusIA:** `tabular`  

---

## 📊 Engenharia de Features & Biomarcadores
* **Total de Features Extraídas:** 5
* **Principais Biomarcadores:** bp, sg, al, bgr, hemo
* **Feature de Maior Relevância (SHAP/Tree):** bp (Top Correlation)
* **Estratégia de Pré-Processamento:** Escalamento: robust, Imputação: none

---

## 🤖 Desempenho do AutoML (6 Modelos Concorrentes)
* **Modelo Vencedor:** `LogisticRegression`
* **AUC:** 0.7333
* **Sensibilidade (Recall):** 0.8000
* **Especificidade:** 0.6667
* **Acurácia:** 0.7500
* **F1-Score:** 0.8000
* **Coeficiente MCC:** 0.4667
* **Erro de Calibração (ECE):** 0.2619
* **Latência de Inferência:** 0.02 ms
* **Tempo de Treino:** 0.00 s

---

## 🩺 Síntese Diagnóstica da IA
**Síntese Bioestatística:** O dataset tabular '23_Chronic_Kidney_Disease' apresentou 40 amostras e 5 atributos clínicos. O classificador **LogisticRegression** obteve AUC de 0.73 e Sensibilidade de 0.80, demonstrando alto valor preditivo com baixo ECE (0.262).
