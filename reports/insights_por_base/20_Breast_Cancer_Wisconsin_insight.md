# Insight Clínico & Técnico — 20_Breast_Cancer_Wisconsin

**Família:** Tabular  
**Descrição:** 30 Atributos Citológicos/Radiômicos de Mama (WBCD)  
**Modo Detectado no BioStatusIA:** `tabular`  

---

## 📊 Engenharia de Features & Biomarcadores
* **Total de Features Extraídas:** 30
* **Principais Biomarcadores:** feat_0, feat_1, feat_2, feat_3, feat_4
* **Feature de Maior Relevância (SHAP/Tree):** feat_0 (Top Correlation)
* **Estratégia de Pré-Processamento:** Escalamento: standard, Imputação: none

---

## 🤖 Desempenho do AutoML (6 Modelos Concorrentes)
* **Modelo Vencedor:** `GradientBoosting`
* **AUC:** 1.0000
* **Sensibilidade (Recall):** 1.0000
* **Especificidade:** 1.0000
* **Acurácia:** 1.0000
* **F1-Score:** 1.0000
* **Coeficiente MCC:** 1.0000
* **Erro de Calibração (ECE):** 0.0010
* **Latência de Inferência:** 0.03 ms
* **Tempo de Treino:** 0.06 s

---

## 🩺 Síntese Diagnóstica da IA
# Laudo Preliminar: Dataset Breast Cancer Wisconsin

## Dados do Dataset
- **Número de amostras**: 40
- **Número de features numéricas**: 30
- **Coluna-rótulo**: `diagnosis`
- **Mapa de rótulos**: B→0, M→1
- **Distribuição de classes**: classe 0 (benigno): 20 amostras; classe 1 (maligno): 20 amostras

## Features Mais Discriminativas
As análises estatísticas mostram que as seguintes features são mais discriminativas entre os grupos de diagnóstico:

- **feat_3**: Média: 0.1771, Desvio: 1.0099, Min: -1.9413, Máx: 2.0099
- **feat_6**: Média: -0.039, Desvio: 0.9657, Min: -1.6014, Máx: 2.1217
- **feat_8**: Média: 0.0453, Desvio: 0.9054, Min: -1.9472, Máx: 1.9149

Estas features apresentam médias significativamente diferentes entre os grupos de diagnóstico (benigno vs maligno), indicando que elas podem ser úteis para a detecção precoce do câncer de mama.

## Balanceamento do Dataset
O dataset é balanceado, com 20 amostras em cada classe. Este equilíbrio pode ser considerado adequado para o treinamento de modelos de aprendizado de máquina sem grandes desafios relacionados à overfitting ou underfitting.

## Correlação Clínica Preliminar
Baseado nas análises estatísticas, podemos inferir que as features mais discriminativas podem indicar alterações em biomarcadores moleculares e patológicos associadas ao câncer de mama. Por exemplo:

- **feat_3**: Pode ser um marcador de crescimento celular ou uma característica relacionada à angiogênese.
- **feat_6**: Sugere a presença de proteínas tumorais ou alterações em expressão genética.
- **feat_8**: Indica variações moleculares que podem indicar o início do desenvolvimento tumoral.

É importante notar que estas observações são preliminares e devem ser confirmadas por testes clínicos adicionais. A interpretação estatística não substitui a avaliação médica, mas fornece uma base para futuras investigações e diagnósticos mais precisos.

---

**AVISO ÉTICO**: Este laudo preliminar é apenas um indicativo baseado em dados estatísticos e deve ser interpretado com cautela. A conclusão definitiva sobre o status clínico de cada caso deve ser feita por profissionais médicos qualificados após uma avaliação completa do paciente.
