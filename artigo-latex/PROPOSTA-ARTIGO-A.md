# Proposta de Pesquisa — Artigo A

**Título de trabalho:** *A Modality-Agnostic Ingestion and Multi-Domain Feature Engineering Pipeline for Heterogeneous Biomedical Data*

**ID interno:** Paper A — Input-to-Features
**Formato:** IEEE Conference (`IEEEtran`, `conference`), 6–8 páginas
**Idioma do artigo:** inglês acadêmico (AGENTS.md §2)
**Sistema sob estudo:** BioStatusIA v3
**Artigo companheiro:** Paper B — AutoML, calibração e laudo assistido por IA

---

## 1. Problema

Pipelines de apoio à decisão clínica são, na prática, mono-modais. A ingestão e a extração de
features são escritas para uma modalidade específica — ECG, ou radiografia de tórax, ou registro
tabular — e precisam ser reescritas quando a modalidade muda. Uma instituição que detém sinais
fisiológicos, estudos DICOM 2D, volumes 3D e prontuários tabulares paga esse custo de engenharia
uma vez por família de dado, e não obtém representação compartilhada entre elas.

## 2. Lacuna

Não existe, na literatura consultada, uma arquitetura que:

1. infira automaticamente a **estrutura física** de uma entrada biomédica arbitrária;
2. normalize todas as modalidades suportadas em um **contrato de dados único**;
3. adapte pré-processamento e extração de features à modalidade detectada **sem reconfiguração
   manual**;
4. seja avaliada empiricamente em um conjunto amplo de bases reais e heterogêneas.

## 3. Pergunta de pesquisa

> Como um pipeline biomédico pode inferir a estrutura de uma entrada arbitrária e adaptar leitura,
> pré-processamento e extração de features a ela, sem reconfiguração manual e sem que a ramificação
> por modalidade vaze para o estágio de extração?

## 4. Objetivos

**Geral.** Projetar, implementar e avaliar empiricamente um pipeline de ingestão e engenharia de
features agnóstico à modalidade, que detecta automaticamente a estrutura de dados biomédicos
heterogêneos, normaliza-a em um contrato único e produz um vetor de features pronto para
classificação.

**Específicos.** SO-1 a SO-5, registrados em `doc-spec.md` §3.2 (imutáveis).

## 5. Contribuições reivindicadas

| # | Contribuição | Evidência no artigo |
|---|---|---|
| C1 | Mecanismo determinístico de detecção de estrutura em 9 modos | §3.B + Tabela de detecção (§4.B) |
| C2 | Contrato de dados `SinalNormalizado` desacoplando leitores de extratores | §3.D + constância dimensional por família (§4.C) |
| C3 | Pré-processamento adaptativo com justificativa gerada automaticamente | §3.F |
| C4 | Conjunto de features multi-domínio (tempo, frequência, textura, morfologia, radiômica 3D) | §3.G + §4.D |
| C5 | Avaliação de robustez de ingestão e cobertura de features em 30 bases reais | §4 |

## 6. Fronteira de escopo (imutável)

O artigo **termina no vetor de features**. Treino de classificadores, seleção de modelo,
calibração, interpretabilidade e laudo por IA pertencem ao Paper B. Nenhuma métrica de
classificação (AUC, sensibilidade, especificidade, MCC, Kappa, ECE, latência de inferência) pode
aparecer neste artigo — inclusive porque esses números já existem no repositório e a tentação de
usá-los é o principal risco de diluição da contribuição.

## 7. Método

Pesquisa de natureza **aplicada**, com abordagem de **engenharia de sistemas + avaliação
experimental descritiva**. O artefato (pipeline) é descrito formalmente e depois submetido a um
protocolo de estresse sobre bases reais.

Cadeia avaliada:

```
entrada bruta → detecção de estrutura (9 modos) → validação de esquema (Pydantic)
   → leitor por família → SinalNormalizado → pré-processamento adaptativo
   → extração multi-domínio → vetor de features ► (Paper B)
```

## 8. Base experimental

30 bases biomédicas reais, 6 por família (F1, F3, F4, tabular clínico, imagem 2D comum),
já executadas: `reports/relatorio_comparativo_30_bases.md`.

**Variáveis medidas (e somente estas):**

| Variável | Status |
|---|---|
| Modo estrutural detectado por base | ✅ disponível |
| Execução sem exceção não tratada | ✅ disponível |
| Dimensionalidade do vetor de features por base | ✅ disponível |
| Descritores efetivamente produzidos por família | ✅ disponível |
| Tempo de ingestão por família | ⚠️ `PENDENTE-T1` — exige instrumentação |
| Pico de memória em F4 | ⚠️ `PENDENTE-T2` — exige instrumentação |
| Nº de amostras processadas por base | ⚠️ `PENDENTE-T3` |
| Especificação de hardware | ⚠️ `PENDENTE-T4` |
| Versões exatas das bibliotecas | ⚠️ `PENDENTE-T5` |

Os pendentes estão registrados em `specs/arquitetura.md` §5 e **não podem ser estimados**
(AGENTS.md §1).

## 9. Resultados já em mãos (e como são lidos)

- **Robustez:** as 30 entradas foram processadas sem exceções não tratadas.
- **Constância dimensional:** F1 → 18 features, F3 → 14, F4 → 22, imagem 2D → 12, em todas as seis
  bases de cada família. Tabular varia (5–30) por depender do esquema da base. Este é o achado que
  sustenta C2: a dimensionalidade é função da **família**, não da base.
- **Divergências informativas (não são falhas a esconder):**
  - bases 04 (EMG) e 06 (Espirometria) são F1 por semântica clínica mas distribuídas em CSV, e
    foram detectadas como `tabular`;
  - base 28 (DRIVE) foi detectada como `imagens_soltas` por ausência de pastas-rótulo.

  A leitura analítica: **a detecção opera sobre a organização física do dado, não sobre a semântica
  clínica declarada.** Isso vira simultaneamente uma limitação declarada (§5.B) e a principal linha
  de trabalho futuro (detecção por conteúdo, e não por extensão).

## 10. Estrutura do artigo

| Seção | Conteúdo | Páginas-alvo |
|---|---|---|
| 1 Introduction | contexto, lacuna, objetivos, contribuições, fronteira de escopo | 1,0 |
| 2 Background | famílias e codificações, radiômica, processamento de sinais, contratos de dados | 1,5 |
| 3 Methodology | pipeline, detecção, validação, contrato, leitores, pré-processamento, extração, protocolo | 2,5 |
| 4 Results | benchmark, detecção, cobertura, descritores, discussão | 1,5 |
| 5 Conclusion | contribuições, limitações, trabalhos futuros | 0,5 |

## 11. Figuras e tabelas planejadas

| Artefato | Descrição | Status |
|---|---|---|
| Fig. 1 | Diagrama de blocos do pipeline, com fronteira tracejada do escopo | ❌ a produzir (`figuras/fig1_pipeline.pdf`) |
| Tab. I | Famílias em escopo e bibliotecas de leitura | ✅ no esqueleto |
| Tab. II | 9 modos de entrada e critérios de detecção | ✅ no esqueleto |
| Tab. III | Campos do contrato `SinalNormalizado` | ✅ no esqueleto |
| Tab. IV | Modo detectado e dimensionalidade por base (30 linhas, `table*`) | ✅ preenchida com dados reais |
| Tab. V | Dimensionalidade por família | ✅ preenchida |
| Tab. VI | Descritores por família | ✅ preenchida |

Opcional, se houver espaço: figura com exemplo de sinal normalizado por família (F1/F3/F4) a partir
do mesmo contrato — reforça visualmente C2.

## 12. Riscos e mitigação

| Risco | Mitigação |
|---|---|
| Revisor pedir desempenho preditivo | Declarar a fronteira de escopo já na Introdução (§1.D) e referenciar o Paper B |
| Contribuição soar como "engenharia de software, não pesquisa" | Ancorar C2 no achado empírico da constância dimensional; posicionar contra toolkits de radiômica que assumem modalidade conhecida a priori |
| Bases sem citação-fonte | Eixo 5 de `specs/referencias.md` exige a publicação-fonte de cada base nomeada |
| Números não instrumentados | `PENDENTE-T1..T5` explícitos; medir antes da submissão ou remover a alegação |

## 13. Plano de execução

| Etapa | Entregável | Dependência |
|---|---|---|
| E1 | Confirmar 20–30 referências (`specs/referencias.md` → status `CONFIRMADA`) | — |
| E2 | Instrumentar `PENDENTE-T1..T3` e registrar `T4`/`T5` | acesso ao ambiente de execução |
| E3 | Produzir `figuras/fig1_pipeline.pdf` | — |
| E4 | Redigir §3 (Methodology) — seção de maior peso | E3 |
| E5 | Redigir §4 (Results) sobre as tabelas já preenchidas | E2 |
| E6 | Redigir §2 (Background) | E1 |
| E7 | Redigir §1 e §5 | E4, E5 |
| E8 | Abstract final + keywords | E7 |
| E9 | Revisão contra o checklist do `doc-spec.md` §5 e compilação final | todas |

## 14. Veículos-alvo candidatos

- Conferências IEEE de engenharia biomédica e informática em saúde (EMBC, BHI, CBMS)
- Congressos brasileiros de engenharia biomédica / informática em saúde (CBEB, SBCAS)
- Periódicos de métodos e software em saúde, caso o artigo evolua para versão estendida

A verificar antes da submissão: datas de chamada, limite de páginas e política de anonimato do
veículo escolhido.

---

> **Checklist antes de qualquer redação final** (`doc-spec.md` §5): escopo respeitado, referências
> confirmadas, nenhum número inventado, texto em inglês acadêmico formal, nada de conteúdo do
> Paper B.
