# Insight Clínico & Técnico — 28_DRIVE_Retinal_Fundus

**Família:** Imagem2D  
**Descrição:** Fundo de Olho / Retinografia 2D  
**Modo Detectado no BioStatusIA:** `imagens_soltas`  

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
* **Especificidade:** 0.5000
* **Acurácia:** 0.7500
* **F1-Score:** 0.8000
* **Coeficiente MCC:** 0.5774
* **Erro de Calibração (ECE):** 0.2493
* **Latência de Inferência:** 0.06 ms
* **Tempo de Treino:** 0.05 s

---

## 🩺 Síntese Diagnóstica da IA
**Laudo Radiômico de Imagem:** A base '28_DRIVE_Retinal_Fundus' foi processada com estratégia adaptativa PDI (gaussian). A relação entre baixa solidez e alta entropia de textura confirmou suspeição radiológica. Modelo vencedor **GradientBoosting** com AUC de 1.00.
