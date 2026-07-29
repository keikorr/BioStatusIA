# Insight Clínico & Técnico — 14_LIDC_IDRI_Lung_CT_3D

**Família:** F4  
**Descrição:** Série DICOM 3D de Tomografia Computadorizada Pulmonar  
**Modo Detectado no BioStatusIA:** `volume_3d`  

---

## 📊 Engenharia de Features & Biomarcadores
* **Total de Features Extraídas:** 22
* **Principais Biomarcadores:** Volume de Lesão (mm³), Esfericidade 3D, GLCM Axial, GLCM Coronal, GLCM Sagital, Percentil P95 3D
* **Feature de Maior Relevância (SHAP/Tree):** Volume da Lesao mm³ (0.412)
* **Estratégia de Pré-Processamento:** Reconstrução Isométrica NIfTI/ITK, Bounding Box 3D, GLCM Tridirecional

---

## 🤖 Desempenho do AutoML (6 Modelos Concorrentes)
* **Modelo Vencedor:** `LogisticRegression`
* **AUC:** 0.8333
* **Sensibilidade (Recall):** 1.0000
* **Especificidade:** 0.3333
* **Acurácia:** 0.6000
* **F1-Score:** 0.6667
* **Coeficiente MCC:** 0.4082
* **Erro de Calibração (ECE):** 0.3661
* **Latência de Inferência:** 0.02 ms
* **Tempo de Treino:** 0.00 s

---

## 🩺 Síntese Diagnóstica da IA
**Laudo Volumétrico 3D (F4):** Processamento 3D do exame '14_LIDC_IDRI_Lung_CT_3D'. Modelo **LogisticRegression** (AUC=0.83).
