# Insight Clínico & Técnico — 08_CBIS_DDSM_Mammography

**Família:** F3  
**Descrição:** Mamografia digital DICOM 2D (Massas/Calcificações)  
**Modo Detectado no BioStatusIA:** `imagem_dicom_2d`  

---

## 📊 Engenharia de Features & Biomarcadores
* **Total de Features Extraídas:** 14
* **Principais Biomarcadores:** Hounsfield Units Range, Densidade Alta (%), Gradiente Médio, GLCM Contraste, Pixel Spacing
* **Feature de Maior Relevância (SHAP/Tree):** Densidade Alta % (HU > 100 - 0.310)
* **Estratégia de Pré-Processamento:** Janelamento HU Automático, Normalização de Intensidade [0,1]

---

## 🤖 Desempenho do AutoML (6 Modelos Concorrentes)
* **Modelo Vencedor:** `MLP`
* **AUC:** 0.6667
* **Sensibilidade (Recall):** 0.5000
* **Especificidade:** 0.3333
* **Acurácia:** 0.4000
* **F1-Score:** 0.4000
* **Coeficiente MCC:** -0.1667
* **Erro de Calibração (ECE):** 0.4386
* **Latência de Inferência:** 0.05 ms
* **Tempo de Treino:** 0.06 s

---

## 🩺 Síntese Diagnóstica da IA
**Laudo Radiológico DICOM 2D (F3):** Imagens do exame '08_CBIS_DDSM_Mammography' lidas via PyDicom. Modelo **MLP** (AUC=0.67).
