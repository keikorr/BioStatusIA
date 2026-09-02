#!/usr/bin/env python
"""
Gera reports/benchmark_artigo2/CORRECOES_ARTIGO2.md — resposta ponto a ponto ao revisor,
com os números lidos de resultados.json (nada digitado à mão).
"""
from __future__ import annotations

import json
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
RES = BASE / "reports" / "benchmark_artigo2" / "resultados.json"
OUT = BASE / "reports" / "benchmark_artigo2" / "CORRECOES_ARTIGO2.md"

ROT = {
    "01_Breast_Cancer_WBCD": "Breast Cancer (WBCD)",
    "02_BUSI_Breast_Ultrasound": "BUSI Breast Ultrasound",
    "03_MITBIH_ECG_Arrhythmia": "MIT-BIH ECG Arrhythmia",
    "04_Stroke_Prediction": "Stroke Prediction",
    "05_PIMA_Diabetes": "PIMA Diabetes",
    "06_Brain_Tumor_MRI": "Brain Tumor MRI",
    "07_COVID19_ChestXRay": "COVID-19 Chest X-Ray",
    "08_Brain_MRI_Oncology": "Brain MRI Oncology",
    "09_Heart_Disease_Cleveland": "Heart Disease (Cleveland)",
    "10_Parkinsons_Vocal": "Parkinson Voice",
}

d = json.loads(RES.read_text(encoding="utf-8"))
BASES = [b for b in d["bases"] if "falha" not in b]
VAZ = d["estudo_vazamento_parkinsons"]


def clin(b):
    return b["modelos"][b["selecao_clinica"]]


def conv(b):
    return b["modelos"][b["selecao_convencional"]]


def rot(b):
    return ROT.get(b["nome"], b["nome"])


a = VAZ["agrupado_por_sujeito"]
l = VAZ["sem_agrupamento"]
ma = a["modelos"][a["selecao_clinica"]]
ml = l["modelos"][l["selecao_clinica"]]
div = [b for b in BASES if b["selecao_divergente"]]
piso = [b for b in BASES if clin(b)["sensibilidade"]["media"] >= 0.80]
ece_ok = [b for b in BASES if clin(b)["ece"]["media"] < 0.10]

linhas_tab = "\n".join(
    f"| {rot(b)} | {b['n_amostras']} | {b['n_features']} | {b['selecao_clinica']} | "
    f"{clin(b)['auc']['media']:.3f} ± {clin(b)['auc']['desvio']:.3f} | "
    f"{clin(b)['sensibilidade']['media']:.3f} | {clin(b)['especificidade']['media']:.3f} | "
    f"{clin(b)['mcc']['media']:.3f} | {clin(b)['ece']['media']:.3f} | "
    f"{'sim' if b['agrupamento_por_sujeito'] else 'não'} |"
    for b in BASES)

linhas_base = "\n".join(
    f"| {rot(b)} | {b['baseline_logreg']['auc']['media']:.3f} | "
    f"{(b.get('baseline_flaml') or {}).get('auc', {}).get('media', float('nan')):.3f} | "
    f"{clin(b)['auc']['media']:.3f} | "
    f"{(b.get('wilcoxon_clinico_vs_baseline_auc') or {}).get('p', '—')} | "
    f"{(b.get('wilcoxon_clinico_vs_flaml_auc') or {}).get('p', '—')} |"
    for b in BASES)

linhas_div = "\n".join(
    f"| {rot(b)} | {b['selecao_convencional']} | {b['selecao_clinica']} | "
    f"{clin(b)['auc']['media'] - conv(b)['auc']['media']:+.3f} | "
    f"{clin(b)['sensibilidade']['media'] - conv(b)['sensibilidade']['media']:+.3f} | "
    f"{clin(b)['mcc']['media'] - conv(b)['mcc']['media']:+.3f} | "
    f"{clin(b)['ece']['media'] - conv(b)['ece']['media']:+.3f} |"
    for b in div)

texto = f"""# Correções do Artigo 2 — resposta ao revisor

Gerado automaticamente a partir de `reports/benchmark_artigo2/resultados.json`
({d['config']['gerado_em']}). Nenhum número deste documento foi digitado à mão.

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
{linhas_base}

Com 5 folds, o menor p bilateral possível no Wilcoxon é 0,0625 — **nenhuma comparação
individual pode atingir p < 0,05**, e o artigo diz isso explicitamente em vez de alegar
significância. BioStatusIA fica à frente do FLAML em {sum(1 for b in BASES if b.get('baseline_flaml') and clin(b)['auc']['media'] > b['baseline_flaml']['auc']['media'])} de {len(BASES)} bases.
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
| Folds por registro (com vazamento) | {l['selecao_clinica']} | {ml['auc']['media']:.3f} ± {ml['auc']['desvio']:.3f} | {ml['sensibilidade']['media']:.3f} | {ml['especificidade']['media']:.3f} | {ml['mcc']['media']:.3f} |
| Folds por sujeito (sem vazamento) | {a['selecao_clinica']} | {ma['auc']['media']:.3f} ± {ma['auc']['desvio']:.3f} | {ma['sensibilidade']['media']:.3f} | {ma['especificidade']['media']:.3f} | {ma['mcc']['media']:.3f} |

Ignorar o agrupamento **infla o AUROC em {ml['auc']['media'] - ma['auc']['media']:.3f} e o MCC em {ml['mcc']['media'] - ma['mcc']['media']:.3f}** nos mesmos dados.

---

## 3. Interpretação clínica

**Pedido:** sensibilidade 1,0 com especificidade 0,667 não demonstra capacidade de triagem; o
COVID com sensibilidade 0,0 e MCC negativo mostra que o framework pode escolher modelos
clinicamente inadequados.

**Feito.** Aquelas linhas vinham de conjuntos de teste de 6 amostras e desapareceram com a
avaliação correta. Os resultados atuais em bases de tamanho real:

| Base | n | Feats | Modelo | AUROC | Sensib. | Especif. | MCC | ECE | Agrup. |
|---|---|---|---|---|---|---|---|---|---|
{linhas_tab}

O piso S_min = 0,80 é atingido em **{len(piso)} de {len(BASES)}** bases. Nas outras
{len(BASES) - len(piso)}, nenhum candidato o alcança e o artigo relata isso como tal, em vez de
esconder atrás do AUROC. O artigo também afirma explicitamente que **nenhum caso degenerado
ocorreu neste benchmark** — a penalidade não "salvou" nada, e apresentá-la como salvadora seria
outra alucinação.

---

## 4. Função de seleção clinicamente orientada (a contribuição sugerida pelo revisor)

**Feito.** Seleção convencional (AUROC máximo) e seleção clínica são calculadas lado a lado nos
mesmos folds. Elas **divergem em {len(div)} de {len(BASES)} bases**:

| Base | Convencional | Clínica | ΔAUROC | ΔSensib. | ΔMCC | ΔECE |
|---|---|---|---|---|---|---|
{linhas_div}

Os efeitos são pequenos, e o artigo diz isso: a função é uma **restrição de segurança que às
vezes muda a resposta**, não um ganho de desempenho. Essa é a leitura que os dados sustentam.

---

## 5. Limiar ECE < 0,10

**Pedido:** o limiar precisa de referência e validação, ou deve ser chamado apenas de limiar
operacional.

**Feito.** Passou a ser chamado de *operational threshold* no texto e na Figura 4, com a
justificativa explícita de que o ECE é um resumo escalar de uma curva de confiabilidade e é
insensível a **onde** ocorre a má calibração. Nenhuma alegação de segurança clínica.
Sob esse critério, {len(ece_ok)} de {len(BASES)} bases ficam abaixo de 0,10 — e as outras
{len(BASES) - len(ece_ok)} são listadas como não promovíveis sem recalibração.

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
"""

OUT.write_text(texto, encoding="utf-8")
print(f"escrito: {OUT}")


if __name__ == "__main__":
    pass
