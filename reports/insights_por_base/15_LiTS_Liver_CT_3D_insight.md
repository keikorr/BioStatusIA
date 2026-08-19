# Insight Clínico & Técnico — 15_LiTS_Liver_CT_3D

**Família:** F4  
**Descrição:** TC Abdominal 3D para lesões hepáticas  
**Modo Detectado no BioStatusIA:** `volume_3d`  

---

## 📊 Engenharia de Features & Biomarcadores
* **Total de Features Extraídas:** 22
* **Principais Biomarcadores:** Volume de Lesão (mm³), Esfericidade 3D, GLCM Axial, GLCM Coronal, GLCM Sagital, Percentil P95 3D
* **Feature de Maior Relevância (SHAP/Tree):** Volume da Lesao mm³ (0.412)
* **Estratégia de Pré-Processamento:** Reconstrução Isométrica NIfTI/ITK, Bounding Box 3D, GLCM Tridirecional

---

## 🤖 Desempenho do AutoML (6 Modelos Concorrentes)
* **Modelo Vencedor:** `KNN`
* **AUC:** 0.9167
* **Sensibilidade (Recall):** 1.0000
* **Especificidade:** 0.6667
* **Acurácia:** 0.8000
* **F1-Score:** 0.8000
* **Coeficiente MCC:** 0.6667
* **Erro de Calibração (ECE):** 0.2800
* **Latência de Inferência:** 1.28 ms
* **Tempo de Treino:** 0.00 s

---

## 🩺 Síntese Diagnóstica da IA
**Laudo Volumétrico 3D (F4):** Processamento 3D do exame '15_LiTS_Liver_CT_3D'. Modelo **KNN** (AUC=0.92).
