# Insight Clínico & Técnico — 18_ProstateX_MRI_3D

**Família:** F4  
**Descrição:** RM Multiparamétrica 3D de Próstata  
**Modo Detectado no BioStatusIA:** `volume_3d`  

---

## 📊 Engenharia de Features & Biomarcadores
* **Total de Features Extraídas:** 22
* **Principais Biomarcadores:** Volume de Lesão (mm³), Esfericidade 3D, GLCM Axial, GLCM Coronal, GLCM Sagital, Percentil P95 3D
* **Feature de Maior Relevância (SHAP/Tree):** Volume da Lesao mm³ (0.412)
* **Estratégia de Pré-Processamento:** Reconstrução Isométrica NIfTI/ITK, Bounding Box 3D, GLCM Tridirecional

---

## 🤖 Desempenho do AutoML (6 Modelos Concorrentes)
* **Modelo Vencedor:** `MLP`
* **AUC:** 1.0000
* **Sensibilidade (Recall):** 1.0000
* **Especificidade:** 0.6667
* **Acurácia:** 0.8000
* **F1-Score:** 0.8000
* **Coeficiente MCC:** 0.6667
* **Erro de Calibração (ECE):** 0.2555
* **Latência de Inferência:** 0.04 ms
* **Tempo de Treino:** 0.06 s

---

## 🩺 Síntese Diagnóstica da IA
**Laudo Volumétrico 3D (F4):** Processamento 3D do exame '18_ProstateX_MRI_3D'. Modelo **MLP** (AUC=1.00).
