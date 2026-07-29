# Insight Clínico & Técnico — 07_NIH_ChestXray14

**Família:** F3  
**Descrição:** Radiografia de tórax DICOM 2D (Tórax)  
**Modo Detectado no BioStatusIA:** `imagem_dicom_2d`  

---

## 📊 Engenharia de Features & Biomarcadores
* **Total de Features Extraídas:** 14
* **Principais Biomarcadores:** Hounsfield Units Range, Densidade Alta (%), Gradiente Médio, GLCM Contraste, Pixel Spacing
* **Feature de Maior Relevância (SHAP/Tree):** Densidade Alta % (HU > 100 - 0.310)
* **Estratégia de Pré-Processamento:** Janelamento HU Automático, Normalização de Intensidade [0,1]

---

## 🤖 Desempenho do AutoML (6 Modelos Concorrentes)
* **Modelo Vencedor:** `RandomForest`
* **AUC:** 1.0000
* **Sensibilidade (Recall):** 1.0000
* **Especificidade:** 1.0000
* **Acurácia:** 1.0000
* **F1-Score:** 1.0000
* **Coeficiente MCC:** 1.0000
* **Erro de Calibração (ECE):** 0.3280
* **Latência de Inferência:** 1.52 ms
* **Tempo de Treino:** 0.10 s

---

## 🩺 Síntese Diagnóstica da IA
**Laudo Radiológico DICOM 2D (F3):** Imagens do exame '07_NIH_ChestXray14' lidas via PyDicom. Modelo **RandomForest** (AUC=1.00).
