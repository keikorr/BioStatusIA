# Insight Clínico & Técnico — 27_BreakHis_Histopathology

**Família:** Imagem2D  
**Descrição:** Histopatologia Microscópica de Mama  
**Modo Detectado no BioStatusIA:** `dataset_rotulado`  

---

## 📊 Engenharia de Features & Biomarcadores
* **Total de Features Extraídas:** 12
* **Principais Biomarcadores:** Entropia GLCM, Contraste GLCM, Solidez, Circularidade, Homogeneidade
* **Feature de Maior Relevância (SHAP/Tree):** Entropia GLCM (0.342)
* **Estratégia de Pré-Processamento:** Filtro: gaussian, Norm: minmax, Equalização: none

---

## 🤖 Desempenho do AutoML (6 Modelos Concorrentes)
* **Modelo Vencedor:** `GradientBoosting`
* **AUC:** 1.0000
* **Sensibilidade (Recall):** 1.0000
* **Especificidade:** 1.0000
* **Acurácia:** 1.0000
* **F1-Score:** 1.0000
* **Coeficiente MCC:** 1.0000
* **Erro de Calibração (ECE):** 0.0327
* **Latência de Inferência:** 0.05 ms
* **Tempo de Treino:** 0.06 s

---

## 🩺 Síntese Diagnóstica da IA
**Laudo Radiômico de Imagem:** A base '27_BreakHis_Histopathology' foi processada com estratégia adaptativa PDI (gaussian). A relação entre baixa solidez e alta entropia de textura confirmou suspeição radiológica. Modelo vencedor **GradientBoosting** com AUC de 1.00.
