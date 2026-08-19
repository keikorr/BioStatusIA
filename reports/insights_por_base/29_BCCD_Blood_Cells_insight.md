# Insight Clínico & Técnico — 29_BCCD_Blood_Cells

**Família:** Imagem2D  
**Descrição:** Fotomicrografia de Células Sanguíneas  
**Modo Detectado no BioStatusIA:** `dataset_rotulado`  

---

## 📊 Engenharia de Features & Biomarcadores
* **Total de Features Extraídas:** 12
* **Principais Biomarcadores:** Entropia GLCM, Contraste GLCM, Solidez, Circularidade, Homogeneidade
* **Feature de Maior Relevância (SHAP/Tree):** Entropia GLCM (0.342)
* **Estratégia de Pré-Processamento:** Filtro: gaussian, Norm: minmax, Equalização: none

---

## 🤖 Desempenho do AutoML (6 Modelos Concorrentes)
* **Modelo Vencedor:** `MLP`
* **AUC:** 0.6667
* **Sensibilidade (Recall):** 1.0000
* **Especificidade:** 0.6667
* **Acurácia:** 0.8000
* **F1-Score:** 0.8000
* **Coeficiente MCC:** 0.6667
* **Erro de Calibração (ECE):** 0.2971
* **Latência de Inferência:** 0.04 ms
* **Tempo de Treino:** 0.07 s

---

## 🩺 Síntese Diagnóstica da IA
**Laudo Radiômico de Imagem:** A base '29_BCCD_Blood_Cells' foi processada com estratégia adaptativa PDI (gaussian). A relação entre baixa solidez e alta entropia de textura confirmou suspeição radiológica. Modelo vencedor **MLP** com AUC de 0.67.
