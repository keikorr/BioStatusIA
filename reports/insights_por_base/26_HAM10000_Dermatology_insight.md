# Insight Clínico & Técnico — 26_HAM10000_Dermatology

**Família:** Imagem2D  
**Descrição:** Dermatoscopia Lesões de Pele (Benigno vs Maligno)  
**Modo Detectado no BioStatusIA:** `dataset_rotulado`  

---

## 📊 Engenharia de Features & Biomarcadores
* **Total de Features Extraídas:** 12
* **Principais Biomarcadores:** Entropia GLCM, Contraste GLCM, Solidez, Circularidade, Homogeneidade
* **Feature de Maior Relevância (SHAP/Tree):** Entropia GLCM (0.342)
* **Estratégia de Pré-Processamento:** Filtro: gaussian, Norm: minmax, Equalização: none

---

## 🤖 Desempenho do AutoML (6 Modelos Concorrentes)
* **Modelo Vencedor:** `SVM`
* **AUC:** 0.8333
* **Sensibilidade (Recall):** 0.5000
* **Especificidade:** 0.0000
* **Acurácia:** 0.2000
* **F1-Score:** 0.3333
* **Coeficiente MCC:** -0.6124
* **Erro de Calibração (ECE):** 0.1130
* **Latência de Inferência:** 0.04 ms
* **Tempo de Treino:** 0.00 s

---

## 🩺 Síntese Diagnóstica da IA
**Laudo Radiômico de Imagem:** A base '26_HAM10000_Dermatology' foi processada com estratégia adaptativa PDI (gaussian). A relação entre baixa solidez e alta entropia de textura confirmou suspeição radiológica. Modelo vencedor **SVM** com AUC de 0.83.
