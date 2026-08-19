# Insight Clínico & Técnico — 16_IXI_Brain_MRI_3D

**Família:** F4  
**Descrição:** RM Encefálica 3D de controle saudável  
**Modo Detectado no BioStatusIA:** `volume_3d`  

---

## 📊 Engenharia de Features & Biomarcadores
* **Total de Features Extraídas:** 22
* **Principais Biomarcadores:** Volume de Lesão (mm³), Esfericidade 3D, GLCM Axial, GLCM Coronal, GLCM Sagital, Percentil P95 3D
* **Feature de Maior Relevância (SHAP/Tree):** Volume da Lesao mm³ (0.412)
* **Estratégia de Pré-Processamento:** Reconstrução Isométrica NIfTI/ITK, Bounding Box 3D, GLCM Tridirecional

---

## 🤖 Desempenho do AutoML (6 Modelos Concorrentes)
* **Modelo Vencedor:** `RandomForest`
* **AUC:** 0.5000
* **Sensibilidade (Recall):** 0.0000
* **Especificidade:** 0.6667
* **Acurácia:** 0.4000
* **F1-Score:** 0.0000
* **Coeficiente MCC:** -0.4082
* **Erro de Calibração (ECE):** 0.3940
* **Latência de Inferência:** 2.19 ms
* **Tempo de Treino:** 0.11 s

---

## 🩺 Síntese Diagnóstica da IA
**Laudo Volumétrico 3D (F4):** Processamento 3D do exame '16_IXI_Brain_MRI_3D'. Modelo **RandomForest** (AUC=0.50).
