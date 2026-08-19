# Insight Clínico & Técnico — 01_PTB_XL_ECG

**Família:** F1  
**Descrição:** ECG de 12 derivações para infarto e arritmia  
**Modo Detectado no BioStatusIA:** `sinal_temporal`  

---

## 📊 Engenharia de Features & Biomarcadores
* **Total de Features Extraídas:** 18
* **Principais Biomarcadores:** FC_bpm, RMSSD, SDNN, pNN50, Potência Espectral (Welch), Razão Alpha/Beta
* **Feature de Maior Relevância (SHAP/Tree):** RMSSD (Variabilidade Cardiaca - 0.298)
* **Estratégia de Pré-Processamento:** Filtro Passa-Banda 0.5-40Hz, Detecção de Picos R, FFT Welch

---

## 🤖 Desempenho do AutoML (6 Modelos Concorrentes)
* **Modelo Vencedor:** `MLP`
* **AUC:** 0.6667
* **Sensibilidade (Recall):** 0.5000
* **Especificidade:** 0.3333
* **Acurácia:** 0.4000
* **F1-Score:** 0.4000
* **Coeficiente MCC:** -0.1667
* **Erro de Calibração (ECE):** 0.5554
* **Latência de Inferência:** 0.04 ms
* **Tempo de Treino:** 0.05 s

---

## 🩺 Síntese Diagnóstica da IA
**Laudo de Sinais Fisiológicos (F1):** Gravações do dataset '01_PTB_XL_ECG' analisadas via MNE/WFDB. RMSSD=33ms. Modelo **MLP** (AUC=0.67).
