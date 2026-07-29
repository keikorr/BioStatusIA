# Insight Clínico & Técnico — 04_EMG_Physical_Action

**Família:** F1  
**Descrição:** EMG de superfície para contração muscular  
**Modo Detectado no BioStatusIA:** `tabular`  

---

## 📊 Engenharia de Features & Biomarcadores
* **Total de Features Extraídas:** 18
* **Principais Biomarcadores:** FC_bpm, RMSSD, SDNN, pNN50, Potência Espectral (Welch), Razão Alpha/Beta
* **Feature de Maior Relevância (SHAP/Tree):** RMSSD (Variabilidade Cardiaca - 0.298)
* **Estratégia de Pré-Processamento:** Filtro Passa-Banda 0.5-40Hz, Detecção de Picos R, FFT Welch

---

## 🤖 Desempenho do AutoML (6 Modelos Concorrentes)
* **Modelo Vencedor:** `LogisticRegression`
* **AUC:** 1.0000
* **Sensibilidade (Recall):** 1.0000
* **Especificidade:** 1.0000
* **Acurácia:** 1.0000
* **F1-Score:** 1.0000
* **Coeficiente MCC:** 1.0000
* **Erro de Calibração (ECE):** 0.1994
* **Latência de Inferência:** 0.03 ms
* **Tempo de Treino:** 0.01 s

---

## 🩺 Síntese Diagnóstica da IA
**Laudo de Sinais Fisiológicos (F1):** Gravações do dataset '04_EMG_Physical_Action' analisadas via MNE/WFDB. RMSSD=48ms. Modelo **LogisticRegression** (AUC=1.00).
