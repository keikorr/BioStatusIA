# Insight Clínico & Técnico — 03_CHB_MIT_EEG

**Família:** F1  
**Descrição:** EEG multicanal para epilepsia pediátrica  
**Modo Detectado no BioStatusIA:** `sinal_temporal`  

---

## 📊 Engenharia de Features & Biomarcadores
* **Total de Features Extraídas:** 18
* **Principais Biomarcadores:** FC_bpm, RMSSD, SDNN, pNN50, Potência Espectral (Welch), Razão Alpha/Beta
* **Feature de Maior Relevância (SHAP/Tree):** RMSSD (Variabilidade Cardiaca - 0.298)
* **Estratégia de Pré-Processamento:** Filtro Passa-Banda 0.5-40Hz, Detecção de Picos R, FFT Welch

---

## 🤖 Desempenho do AutoML (6 Modelos Concorrentes)
* **Modelo Vencedor:** `RandomForest`
* **AUC:** 0.8333
* **Sensibilidade (Recall):** 1.0000
* **Especificidade:** 0.3333
* **Acurácia:** 0.6000
* **F1-Score:** 0.6667
* **Coeficiente MCC:** 0.4082
* **Erro de Calibração (ECE):** 0.1820
* **Latência de Inferência:** 1.84 ms
* **Tempo de Treino:** 0.09 s

---

## 🩺 Síntese Diagnóstica da IA
**Laudo de Sinais Fisiológicos (F1):** Gravações do dataset '03_CHB_MIT_EEG' analisadas via MNE/WFDB. RMSSD=48ms. Modelo **RandomForest** (AUC=0.83).
