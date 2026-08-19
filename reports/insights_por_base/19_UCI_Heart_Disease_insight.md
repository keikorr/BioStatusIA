# Insight Clínico & Técnico — 19_UCI_Heart_Disease

**Família:** Tabular  
**Descrição:** 14 Indicadores Clínicos Cardíacos (UCI Cleveland)  
**Modo Detectado no BioStatusIA:** `tabular`  

---

## 📊 Engenharia de Features & Biomarcadores
* **Total de Features Extraídas:** 6
* **Principais Biomarcadores:** age, sex, cp, trestbps, chol
* **Feature de Maior Relevância (SHAP/Tree):** age (Top Correlation)
* **Estratégia de Pré-Processamento:** Escalamento: robust, Imputação: none

---

## 🤖 Desempenho do AutoML (6 Modelos Concorrentes)
* **Modelo Vencedor:** `LogisticRegression`
* **AUC:** 0.6875
* **Sensibilidade (Recall):** 1.0000
* **Especificidade:** 0.2500
* **Acurácia:** 0.6250
* **F1-Score:** 0.7273
* **Coeficiente MCC:** 0.3780
* **Erro de Calibração (ECE):** 0.2350
* **Latência de Inferência:** 0.02 ms
* **Tempo de Treino:** 0.00 s

---

## 🩺 Síntese Diagnóstica da IA
```markdown
# Laudo Preliminar - Dataset UCI Heart Disease

## Resumo do Dataset
- **Nº de amostras**: 40
- **Nº de features numéricas**: 6
- **Coluna-rótulo**: `target`
- **Mapa de rótulos**: 0→0, 1→1
- **Distribuição de classes**: 
    - Classe 0: 20 amostras
    - Classe 1: 20 amostras

## Features mais discriminativas (estatísticas)

| Feature | Média | Mediana | Desvio | Min | Max |
|---|---|---|---|---|---|
| age | 55.7 | 54.0 | 11.9461 | 37.0 | 74.0 |
| sex | 0.575 | 1.0 | 0.4943 | 0.0 | 1.0 |
| cp | 1.475 | 1.5 | 1.0952 | 0.0 | 3.0 |
| trestbps | 142.775 | 147.5 | 16.6756 | 111.0 | 169.0 |
| chol | 254.45 | 264.0 | 43.4281 | 180.0 | 314.0 |
| thalach | 150.9 | 147.5 | 26.8931 | 102.0 | 192.0 |

## Interpretação preliminar

### Observações:
- A coluna `age` tem uma média de aproximadamente 55 anos, o que pode indicar um possível aumento da probabilidade de doença cardiovascular com a idade.
- A coluna `sex`, representando sexo (1 para masculino e 0 para feminino), mostra uma distribuição equilibrada entre ambos os grupos. No entanto, é importante notar que as proporções podem variar dependendo do contexto específico da amostra.
- A coluna `cp` (percepção de dor no peito) tem valores concentrados em 1 e 3, sugerindo que a percepção de dor no peito pode ser um fator crítico na classificação entre as classes.
- A coluna `trestbps` (pressão arterial sistólica após o exercício), com uma média significativamente maior do que a mediana, indica possíveis desvios ou outliers. Isso pode indicar pressão arterial elevada, um fator de risco para doenças cardiovasculares.
- A coluna `chol` (cholesterol total) tem uma distribuição com valores altos e está muito acima da mediana, sugerindo que o colesterol alto é um fator crítico na classificação entre as classes.
- A coluna `thalach` (batimento cardíaco máximo durante exercício), também mostra desvios significativos, indicando batimentos cardíacos elevados, que pode ser um sinal de problemas cardiovasculares.

### Conclusão:
As features mais discriminativas identificadas são: `age`, `cp`, `trestbps`, `chol` e `thalach`. Essas características podem fornecer insights importantes para a classificação entre as classes (0 - não doença, 1 - doença). No entanto, é importante notar que estas observações devem ser interpretadas com cautela e em conjunto com outros fatores clínicos.

### Aviso Ético:
Este laudo preliminar não substitui uma avaliação médica. As informações fornecidas são baseadas apenas nos dados analisados e devem ser utilizadas como referência para a tomada de decisões médicas.
```

AVISO ÉTICO: Este laudo preliminar não substitui uma avaliação médica. As informações fornecidas são baseadas apenas nos dados analisados e devem ser utilizadas como referência para a tomada de decisões médicas.
