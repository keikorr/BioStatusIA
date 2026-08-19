# Insight Clínico & Técnico — 17_OASIS3_Brain_PET_3D

**Família:** F4  
**Descrição:** PET 3D Encefálico para Alzheimer  
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
* **AUC:** 1.0000
* **Sensibilidade (Recall):** 1.0000
* **Especificidade:** 0.0000
* **Acurácia:** 0.4000
* **F1-Score:** 0.5714
* **Coeficiente MCC:** 0.0000
* **Erro de Calibração (ECE):** 0.4023
* **Latência de Inferência:** 0.02 ms
* **Tempo de Treino:** 0.00 s

---

## 🩺 Síntese Diagnóstica da IA
**Laudo Volumétrico 3D (F4):** Processamento 3D do exame '17_OASIS3_Brain_PET_3D'. Modelo **LogisticRegression** (AUC=1.00).
