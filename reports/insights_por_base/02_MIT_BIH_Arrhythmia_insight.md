# Insight Clínico & Técnico — 02_MIT_BIH_Arrhythmia

**Família:** F1  
**Descrição:** ECG de 2 canais com arritmias ectópicas  
**Modo Detectado no BioStatusIA:** `sinal_temporal`  

---

## 📊 Engenharia de Features & Biomarcadores
* **Total de Features Extraídas:** 18
* **Principais Biomarcadores:** FC_bpm, RMSSD, SDNN, pNN50, Potência Espectral (Welch), Razão Alpha/Beta
* **Feature de Maior Relevância (SHAP/Tree):** RMSSD (Variabilidade Cardiaca - 0.298)
* **Estratégia de Pré-Processamento:** Filtro Passa-Banda 0.5-40Hz, Detecção de Picos R, FFT Welch

---

## 🤖 Desempenho do AutoML (6 Modelos Concorrentes)
* **Modelo Vencedor:** `KNN`
* **AUC:** 0.6667
* **Sensibilidade (Recall):** 0.5000
* **Especificidade:** 0.6667
* **Acurácia:** 0.6000
* **F1-Score:** 0.5000
* **Coeficiente MCC:** 0.1667
* **Erro de Calibração (ECE):** 0.1200
* **Latência de Inferência:** 1.04 ms
* **Tempo de Treino:** 0.00 s

---

## 🩺 Síntese Diagnóstica da IA
**Laudo de Sinais Fisiológicos (F1):** Gravações do dataset '02_MIT_BIH_Arrhythmia' analisadas via MNE/WFDB. RMSSD=25ms. Modelo **KNN** (AUC=0.67).
