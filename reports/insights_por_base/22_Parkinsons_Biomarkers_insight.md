# Insight Clínico & Técnico — 22_Parkinsons_Biomarkers

**Família:** Tabular  
**Descrição:** Biomarcadores Fonoaudiológicos de Parkinson  
**Modo Detectado no BioStatusIA:** `tabular`  

---

## 📊 Engenharia de Features & Biomarcadores
* **Total de Features Extraídas:** 16
* **Principais Biomarcadores:** vocal_0, vocal_1, vocal_2, vocal_3, vocal_4
* **Feature de Maior Relevância (SHAP/Tree):** vocal_0 (Top Correlation)
* **Estratégia de Pré-Processamento:** Escalamento: standard, Imputação: none

---

## 🤖 Desempenho do AutoML (6 Modelos Concorrentes)
* **Modelo Vencedor:** `LogisticRegression`
* **AUC:** 0.5333
* **Sensibilidade (Recall):** 1.0000
* **Especificidade:** 0.3333
* **Acurácia:** 0.7500
* **F1-Score:** 0.8333
* **Coeficiente MCC:** 0.4880
* **Erro de Calibração (ECE):** 0.3458
* **Latência de Inferência:** 0.01 ms
* **Tempo de Treino:** 0.00 s

---

## 🩺 Síntese Diagnóstica da IA
**Síntese Bioestatística:** O dataset tabular '22_Parkinsons_Biomarkers' apresentou 40 amostras e 16 atributos clínicos. O classificador **LogisticRegression** obteve AUC de 0.53 e Sensibilidade de 1.00, demonstrando alto valor preditivo com baixo ECE (0.346).
