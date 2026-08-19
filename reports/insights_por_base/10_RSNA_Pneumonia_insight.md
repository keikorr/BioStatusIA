# Insight Clínico & Técnico — 10_RSNA_Pneumonia

**Família:** F3  
**Descrição:** Radiografia DICOM 2D com opacidade pulmonar  
**Modo Detectado no BioStatusIA:** `imagem_dicom_2d`  

---

## 📊 Engenharia de Features & Biomarcadores
* **Total de Features Extraídas:** 14
* **Principais Biomarcadores:** Hounsfield Units Range, Densidade Alta (%), Gradiente Médio, GLCM Contraste, Pixel Spacing
* **Feature de Maior Relevância (SHAP/Tree):** Densidade Alta % (HU > 100 - 0.310)
* **Estratégia de Pré-Processamento:** Janelamento HU Automático, Normalização de Intensidade [0,1]

---

## 🤖 Desempenho do AutoML (6 Modelos Concorrentes)
* **Modelo Vencedor:** `LogisticRegression`
* **AUC:** 1.0000
* **Sensibilidade (Recall):** 1.0000
* **Especificidade:** 0.6667
* **Acurácia:** 0.8000
* **F1-Score:** 0.8000
* **Coeficiente MCC:** 0.6667
* **Erro de Calibração (ECE):** 0.3046
* **Latência de Inferência:** 0.02 ms
* **Tempo de Treino:** 0.00 s

---

## 🩺 Síntese Diagnóstica da IA
**Laudo Radiológico DICOM 2D (F3):** Imagens do exame '10_RSNA_Pneumonia' lidas via PyDicom. Modelo **LogisticRegression** (AUC=1.00).
