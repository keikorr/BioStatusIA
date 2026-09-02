# Correções do Artigo 2 — resposta ao revisor

Gerado automaticamente a partir de `reports/benchmark_artigo2/resultados.json`
(2026-08-30 12:39:06). Nenhum número deste documento foi digitado à mão.

**A estrutura do artigo enviado foi preservada**: mesmo título, mesmas seções
(I Introduction · II Methodology · III Results and Discussion · IV Challenges and Gaps in
Technological Translation · V Conclusion), Tabelas I e II nos mesmos papéis e Figuras 1–5 nas
mesmas posições. O que mudou foram os números, as imagens e os pontos levantados na revisão.
Duas tabelas (III e IV) e uma figura (6) foram acrescentadas porque o revisor pediu
explicitamente material que não existia: o estudo de vazamento por sujeito e a comparação
entre o critério de seleção convencional e o clínico.

---

## 0. O problema de fundo

A versão anterior do manuscrito **não era sustentada por nenhuma execução**. Verificação no
repositório:

| Afirmação no manuscrito | O que existia de fato |
|---|---|
| `StratifiedGroupKFold` por `subject_id` | Só aparecia na prosa dos scripts de renderização de PDF. Nenhum código de agrupamento no `src/`. |
| Baselines Auto-Sklearn / ResNet-50 / 1D-CNN "executados localmente" | Nunca executados. Nenhuma dessas bibliotecas estava instalada. |
| Teste de Wilcoxon pareado, `p < 0,05` | Nenhuma chamada a `wilcoxon` no código. |
| Tabela I | Não coincidia com `reports/resultados_kaggle_reais.json`. |
| Linhas MIT-BIH e Stroke | Constantes fixas no código (`executar_kaggle_reais.py`), emitidas quando o treino não rodava. Valores idênticos nas duas linhas. |
| "780 imagens", "7.023 fatias", "21.837 registros" | O script copiava **15 imagens por classe**; tabular limitado a 300 linhas. |
| "5-fold stratified cross-validation" | `treinar_vetores` faz um único holdout 80/20. Os 0,6667 eram 2 de 3 num teste de 6 amostras. |
| Figuras 2–5 | Geradas de arrays fixos e curvas explicitamente sintéticas. |

O que **era** real: `calcular_score_clinico` em `avaliacao_modelos.py` implementa a função
multiobjetivo exatamente como descrita (w = 0,40/0,40/0,20; S_min = 0,80; λ = 1,0; expoente 1,5).
A contribuição existia — faltava avaliação honesta.

---

## 1. Desenho de validação e comparação com baselines

**Pedido:** executar pelo menos Auto-Sklearn e um baseline convencional nos mesmos folds,
reportar média ± desvio das cinco partições, com IC ou teste pareado.

**Feito.** `scripts/benchmark_artigo2_corrigido.py` roda validação cruzada 5-fold de verdade, com
escalonamento e SMOTE ajustados **dentro** de cada fold. Média, desvio e IC 95% por métrica.
Três baselines nos **mesmos índices de fold**:

1. Regressão logística padronizada, sem balanceamento nem seleção (prática convencional).
2. Seleção convencional por AUROC máximo sobre os mesmos 6 modelos.
3. **FLAML** (`scripts/baseline_flaml_artigo2.py`), sistema AutoML externo publicado, 20 s/fold.

Auto-Sklearn não foi usado porque depende de componentes POSIX e não instala no Windows onde os
experimentos rodaram — isso está declarado no artigo, não omitido.

| Base | LogReg | FLAML | BioStatusIA | p vs LR | p vs FLAML |
|---|---|---|---|---|---|
| Breast Cancer (WBCD) | 0.995 | 0.990 | 0.995 | 1.0 | 0.375 |
| BUSI Breast Ultrasound | 0.703 | 0.699 | 0.778 | 0.0625 | 0.0625 |
| MIT-BIH ECG Arrhythmia | 0.798 | 0.928 | 0.948 | 0.0625 | 0.0625 |
| Stroke Prediction | 0.843 | 0.840 | 0.842 | 1.0 | 0.875 |
| PIMA Diabetes | 0.830 | 0.819 | 0.830 | 0.8125 | 0.4375 |
| Brain Tumor MRI | 0.957 | 0.990 | 0.986 | 0.0625 | 0.0625 |
| COVID-19 Chest X-Ray | 0.766 | 0.878 | 0.883 | 0.0625 | 0.1875 |
| Brain MRI Oncology | 0.803 | 0.837 | 0.866 | 0.0625 | 0.625 |
| Heart Disease (Cleveland) | 0.912 | 0.896 | 0.907 | 0.3125 | 0.625 |
| Parkinson Voice | 0.736 | 0.797 | 0.768 | 0.8125 | 1.0 |

Com 5 folds, o menor p bilateral possível no Wilcoxon é 0,0625 — **nenhuma comparação
individual pode atingir p < 0,05**, e o artigo diz isso explicitamente em vez de alegar
significância. BioStatusIA fica à frente do FLAML em 8 de 10 bases.
Toda alegação de superioridade sobre números copiados da literatura foi **removida**.

---

## 2. Vazamento por paciente

**Pedido:** refazer os folds por paciente sempre que houver identificadores.

**Feito, e medido.** `StratifiedGroupKFold` está implementado e é aplicado onde há identificador.
A disponibilidade é declarada base a base, em vez de sugerir um protocolo uniforme:

- 5 coortes tabulares: uma linha por indivíduo — a divisão por registro já é por sujeito.
- **Parkinson (UCI)**: 195 gravações de 32 sujeitos → agrupamento aplicado.
- 4 coleções de imagem + CSV do MIT-BIH: **não há identificador** na redistribuição pública.
  Marcado como tal na Tabela I e tratado como limite superior, não como resultado limpo.

O Parkinson permite medir o custo do vazamento em vez de apenas argumentar:

| Protocolo | Modelo | AUROC | Sensib. | Especif. | MCC |
|---|---|---|---|---|---|
| Folds por registro (com vazamento) | GradientBoosting | 0.964 ± 0.027 | 0.952 | 0.876 | 0.828 |
| Folds por sujeito (sem vazamento) | MLP | 0.768 ± 0.117 | 0.884 | 0.333 | 0.215 |

Ignorar o agrupamento **infla o AUROC em 0.196 e o MCC em 0.613** nos mesmos dados.

---

## 3. Interpretação clínica

**Pedido:** sensibilidade 1,0 com especificidade 0,667 não demonstra capacidade de triagem; o
COVID com sensibilidade 0,0 e MCC negativo mostra que o framework pode escolher modelos
clinicamente inadequados.

**Feito.** Aquelas linhas vinham de conjuntos de teste de 6 amostras e desapareceram com a
avaliação correta. Os resultados atuais em bases de tamanho real:

| Base | n | Feats | Modelo | AUROC | Sensib. | Especif. | MCC | ECE | Agrup. |
|---|---|---|---|---|---|---|---|---|---|
| Breast Cancer (WBCD) | 569 | 30 | SVM | 0.995 ± 0.006 | 0.963 | 0.983 | 0.948 | 0.033 | não |
| BUSI Breast Ultrasound | 647 | 9 | RandomForest | 0.778 ± 0.028 | 0.595 | 0.824 | 0.425 | 0.110 | não |
| MIT-BIH ECG Arrhythmia | 1200 | 187 | RandomForest | 0.948 ± 0.018 | 0.750 | 0.976 | 0.768 | 0.084 | não |
| Stroke Prediction | 3000 | 10 | LogisticRegression | 0.842 ± 0.041 | 0.757 | 0.746 | 0.239 | 0.264 | não |
| PIMA Diabetes | 768 | 8 | LogisticRegression | 0.830 ± 0.028 | 0.716 | 0.770 | 0.477 | 0.115 | não |
| Brain Tumor MRI | 1001 | 9 | GradientBoosting | 0.986 ± 0.008 | 0.962 | 0.950 | 0.913 | 0.037 | não |
| COVID-19 Chest X-Ray | 2000 | 9 | RandomForest | 0.883 ± 0.022 | 0.817 | 0.776 | 0.594 | 0.055 | não |
| Brain MRI Oncology | 253 | 9 | RandomForest | 0.866 ± 0.039 | 0.858 | 0.777 | 0.637 | 0.130 | não |
| Heart Disease (Cleveland) | 303 | 13 | RandomForest | 0.907 ± 0.026 | 0.806 | 0.890 | 0.702 | 0.126 | não |
| Parkinson Voice | 195 | 22 | MLP | 0.768 ± 0.117 | 0.884 | 0.333 | 0.215 | 0.208 | sim |

O piso S_min = 0,80 é atingido em **6 de 10** bases. Nas outras
4, nenhum candidato o alcança e o artigo relata isso como tal, em vez de
esconder atrás do AUROC. O artigo também afirma explicitamente que **nenhum caso degenerado
ocorreu neste benchmark** — a penalidade não "salvou" nada, e apresentá-la como salvadora seria
outra alucinação.

---

## 4. Função de seleção clinicamente orientada (a contribuição sugerida pelo revisor)

**Feito.** Seleção convencional (AUROC máximo) e seleção clínica são calculadas lado a lado nos
mesmos folds. Elas **divergem em 3 de 10 bases**:

| Base | Convencional | Clínica | ΔAUROC | ΔSensib. | ΔMCC | ΔECE |
|---|---|---|---|---|---|---|
| Brain Tumor MRI | RandomForest | GradientBoosting | -0.002 | +0.004 | -0.008 | -0.018 |
| Heart Disease (Cleveland) | LogisticRegression | RandomForest | -0.004 | +0.000 | +0.032 | +0.017 |
| Parkinson Voice | RandomForest | MLP | -0.002 | +0.023 | +0.074 | +0.049 |

Os efeitos são pequenos, e o artigo diz isso: a função é uma **restrição de segurança que às
vezes muda a resposta**, não um ganho de desempenho. Essa é a leitura que os dados sustentam.

---

## 5. Limiar ECE < 0,10

**Pedido:** o limiar precisa de referência e validação, ou deve ser chamado apenas de limiar
operacional.

**Feito.** Passou a ser chamado de *operational threshold* no texto e na Figura 4, com a
justificativa explícita de que o ECE é um resumo escalar de uma curva de confiabilidade e é
insensível a **onde** ocorre a má calibração. Nenhuma alegação de segurança clínica.
Sob esse critério, 4 de 10 bases ficam abaixo de 0,10 — e as outras
6 são listadas como não promovíveis sem recalibração.

---

## 5b. Bug de atribuição SHAP (encontrado durante a correção)

`_shap_importancia` em `avaliacao_modelos.py` fazia `np.abs(valores).mean(axis=0).ravel()`.
No shap ≥ 0.45 o `TreeExplainer` devolve `(n_amostras, n_features, n_classes)` para classificação
binária, então o `ravel()` gerava 18 valores para 9 features e o `zip` com os nomes **desalinhava
tudo** — por isso as importâncias saíam em pares idênticos.

Corrigido (seleciona a classe positiva antes de agregar, e descarta o ranking se o número de
valores não bater com o de features). O efeito é visível: no Cleveland o topo passou de
`fbs, chol, trestbps` (clinicamente implausível) para `ca, thal, cp` — que são exatamente os
preditores canônicos dessa base. O bug afetava também a exibição de SHAP na interface, não só o
artigo.

---

## 6. Figuras em português

**Feito.** Figuras 1–4 regeradas inteiramente em inglês por
`scripts/gerar_figuras_artigo2_reais.py`, a partir de `resultados.json`. São dados medidos:
curvas ROC de predições fora-de-fold acumuladas, matriz de confusão real, diagrama de
confiabilidade real. O gerador antigo, com curvas sintéticas, foi marcado como obsoleto.

---

## 7. Referências [15], [16], [17] não citadas

**Feito.** As 18 referências estão citadas no corpo. Verificado por auditoria automática:
0 não citadas, 0 citadas sem entrada.

---

## Como reproduzir

```powershell
uv run python scripts/benchmark_artigo2_corrigido.py   # benchmark (~40 min)
uv run python scripts/baseline_flaml_artigo2.py        # baseline FLAML (~18 min)
uv run python scripts/recalcular_atribuicoes_artigo2.py # atribuição SHAP corrigida
uv run python scripts/gerar_figuras_artigo2_reais.py   # figuras
uv run python scripts/preencher_artigo2.py             # preenche o .tex
uv run python scripts/tex2pdf_artigo2.py               # PDF
```

`artigo2_automl_template.tex` guarda a prosa; `artigo2_automl.tex` é gerado e **não deve ser
editado à mão** — qualquer número nele vem de `resultados.json`.

---

## Ponto ainda em aberto

`artigo2_automl_pt.tex` (versão em português) e `artigo2_automl_pt.pdf` ainda contêm a tabela e
as figuras antigas, não sustentadas. Não foram tocados por não terem sido pedidos; devem ser
regenerados ou removidos antes de qualquer submissão.
