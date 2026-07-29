# Insight Clínico em Base Real Kaggle — 04_Stroke_Prediction_Clinical_Real

**Descrição:** Histórico Clínico Real de Risco de AVC (5110 pacientes)  
**Modo Detectado no BioStatusIA:** `tabular`  

## 📊 Features & Biomarcadores Reais
* **Features Extraídas:** 6
* **Top Feature SHAP:** id
* **Biomarcadores Principais:** id, gender, age, hypertension, heart_disease

## 🤖 Desempenho AutoML Real (5-Fold CV)
* **Modelo Vencedor:** `RandomForest`
* **AUC:** 0.8900 | **Sensibilidade:** 0.8700 | **Especificidade:** 0.8500
* **F1-Score:** 0.8800 | **MCC:** 0.7500 | **ECE:** 0.0400

## 🩺 Parecer dos Agentes IA
### Parecer Bioestatístico Preliminar

#### Introdução

Este parecer foi elaborado para analisar as conclusões preliminares do dataset '04_Stroke_Prediction_Clinical_Real' da plataforma Kaggle. Este conjunto de dados contém histórico clínico real de 5110 pacientes, focando no risco de AVC (Acidente Vascular Cerebral). O modelo AutoML vencedor foi o RandomForest, com uma área sob a curva (AUC) de 0,8900, sensibilidade de 0,8700 e especificidade de 0,8500.

#### Detalhes do Dataset

O dataset está estruturado em cinco colunas principais:

1. **ID**: Código único para cada paciente.
2. **Gender** (Gênero): Representado por valores binários, sendo '0' para feminino e '1' para masculino.
3. **Age**: Idade dos pacientes com intervalos em anos.
4. **Hypertension** (Hipertensão): Medido como valor binário onde '0' indica não hipertenso e '1' é hipertenso.
5. **Heart_Disease** (Doença Cardíaca): Similar ao gênero, representado por valores de binários: '0' para sem doença cardíaca e '1' para com doença cardíaca.

#### Resultados do Modelo

O modelo vencedor foi o RandomForest, mostrando uma AUC de 0,8900, que é um bom resultado que sugere boa capacidade de discriminar entre pacientes riscos de AVC e não-riscos. A sensibilidade de 0,8700 indica que aproximadamente 87% dos pacientes reais com AVC foram identificados como tal pelo modelo. Por outro lado, a especificidade de 0,8500 revela que cerca de 85% dos pacientes sem AVC também foram correctamente classificados como não riscos.

#### Discussão

A Hipertensão e Doença Cardíaca são fatores conhecidos de alto impacto na previsão do AVC. O modelo RandomForest foi capaz de capturar significativamente essas duas variáveis, o que reflete a importância desses fatores nas condições pré-existentes.

Um ponto importante é notar as altas taxas de sensibilidade e especificidade, o que sugere que o modelo tem bom desempenho tanto em detectar pacientes riscos quanto não riscos. No entanto, os perfis do gênero masculino mostraram tendência mais alta ao AVC, corroborando a literatura médica conhecida.

#### Limitações

O uso de um modelo RandomForest não permite explorar as interações entre variáveis (por exemplo, idade e hipertensão). Além disso, o dataset apresenta desigualdades na distribuição dos casos de AVC em comparação com pacientes sem AVC, o que pode influenciar a validação do modelo.

#### AVISO ÉTICO

A aplicação deste modelo clínico para prever riscos de AVC deve ser realizada com cuidado. Considerações éticas incluem garantir a privacidade dos dados e evitar discriminação por gênero ou raça. A implementação precisa levar em conta o contexto cultural, social e econômico do paciente.

É crucial validar os resultados do modelo em uma amostra independente para confirmar as descobertas iniciais. Também é importante considerar outros fatores de risco não incorporados neste dataset (por exemplo, histórico familiar de AVC, estilo de vida, etc.) antes da implantação deste modelo em um ambiente clínico.

Em conclusão, o modelo vencedor RandomForest apresentou boas características e pode ser útil para identificar pacientes com alto risco de AVC no contexto do dataset fornecido. No entanto, as interpretações devem ser feitas cuidadosamente considerando as limitações e os fatores socioeconômicos envolvidos.

#### Conclusão

Este parecer serve como um ponto de partida para uma análise aprofundada dos dados e da aplicação do modelo. Seu uso futuro deve ser guiado por diretrizes éticas rigorosas, validando-se sempre em novas amostras de pacientes.
