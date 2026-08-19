# Insight Clínico & Técnico — 12_VinDr_CXR

**Família:** F3  
**Descrição:** Radiografia de tórax DICOM 2D anotada  
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
* **AUC:** 0.5000
* **Sensibilidade (Recall):** 0.5000
* **Especificidade:** 0.0000
* **Acurácia:** 0.2000
* **F1-Score:** 0.3333
* **Coeficiente MCC:** -0.6124
* **Erro de Calibração (ECE):** 0.6323
* **Latência de Inferência:** 0.02 ms
* **Tempo de Treino:** 0.00 s

---

## 🩺 Síntese Diagnóstica da IA
**Laudo Radiológico DICOM 2D (F3):** Imagens do exame '12_VinDr_CXR' lidas via PyDicom. Modelo **LogisticRegression** (AUC=0.50).
