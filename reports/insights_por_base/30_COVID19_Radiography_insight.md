# Insight Clínico & Técnico — 30_COVID19_Radiography

**Família:** Imagem2D  
**Descrição:** Raio-X de Tórax 2D PNG (COVID vs Normal)  
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
* **AUC:** 0.5833
* **Sensibilidade (Recall):** 0.5000
* **Especificidade:** 0.3333
* **Acurácia:** 0.4000
* **F1-Score:** 0.4000
* **Coeficiente MCC:** -0.1667
* **Erro de Calibração (ECE):** 0.1374
* **Latência de Inferência:** 0.03 ms
* **Tempo de Treino:** 0.00 s

---

## 🩺 Síntese Diagnóstica da IA
**Laudo Radiômico de Imagem:** A base '30_COVID19_Radiography' foi processada com estratégia adaptativa PDI (gaussian). A relação entre baixa solidez e alta entropia de textura confirmou suspeição radiológica. Modelo vencedor **SVM** com AUC de 0.58.
