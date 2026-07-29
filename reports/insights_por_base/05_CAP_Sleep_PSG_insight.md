# Insight Clínico & Técnico — 05_CAP_Sleep_PSG

**Família:** F1  
**Descrição:** Polissonografia multicanal para distúrbios do sono  
**Modo Detectado no BioStatusIA:** `sinal_temporal`  

---

## 📊 Engenharia de Features & Biomarcadores
* **Total de Features Extraídas:** 18
* **Principais Biomarcadores:** FC_bpm, RMSSD, SDNN, pNN50, Potência Espectral (Welch), Razão Alpha/Beta
* **Feature de Maior Relevância (SHAP/Tree):** RMSSD (Variabilidade Cardiaca - 0.298)
* **Estratégia de Pré-Processamento:** Filtro Passa-Banda 0.5-40Hz, Detecção de Picos R, FFT Welch

---

## 🤖 Desempenho do AutoML (6 Modelos Concorrentes)
* **Modelo Vencedor:** `GradientBoosting`
* **AUC:** 1.0000
* **Sensibilidade (Recall):** 1.0000
* **Especificidade:** 1.0000
* **Acurácia:** 1.0000
* **F1-Score:** 1.0000
* **Coeficiente MCC:** 1.0000
* **Erro de Calibração (ECE):** 0.0028
* **Latência de Inferência:** 0.05 ms
* **Tempo de Treino:** 0.06 s

---

## 🩺 Síntese Diagnóstica da IA
**Laudo de Sinais Fisiológicos (F1):** Gravações do dataset '05_CAP_Sleep_PSG' analisadas via MNE/WFDB. RMSSD=20ms. Modelo **GradientBoosting** (AUC=1.00).
