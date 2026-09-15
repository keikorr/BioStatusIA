# SPEC — Mapa de Seções (Paper A — Input-to-Features)

> Define a estrutura de arquivos e o escopo de cada seção do artigo.
> **Fronteira imutável do Paper A:** o artigo termina quando o vetor de features está pronto.
> Treino de classificadores, seleção de modelos, calibração e laudo por IA são do **Paper B**.

## Estrutura de Arquivos

```
artigo-latex/
├── main.tex                       # Documento raiz (NÃO editar)
├── doc-spec.md                    # Especificação Mestre
├── AGENTS.md                      # Regras do Agente (NÃO editar)
├── PROPOSTA-ARTIGO-A.md           # Proposta de pesquisa (documento de trabalho, fora do PDF)
├── IEEEtran.cls                   # Classe LaTeX IEEE
├── config/
│   ├── preambulo.tex              # Pacotes e comandos
│   └── dados.tex                  # Título, autores, abstract e keywords
├── secoes/
│   ├── 01-introducao.tex          # Seção 1 — Introduction
│   ├── 02-fundamentacao.tex       # Seção 2 — Background and Related Work
│   ├── 03-metodologia.tex         # Seção 3 — Methodology (arquitetura do pipeline)
│   ├── 04-resultados.tex          # Seção 4 — Results and Discussion (benchmark de 30 bases)
│   └── 05-conclusao.tex           # Seção 5 — Conclusion
├── referencias/
│   └── referencias.bib            # Banco de dados BibTeX
├── figuras/                       # Imagens e gráficos
└── specs/                         # Módulos de especificação
    ├── secoes.md
    ├── referencias.md
    └── arquitetura.md
```

## Escopo por Seção

### Seção 1 — Introduction (`01-introducao.tex`)

| Subseção | Conteúdo | Fora de escopo |
|---|---|---|
| 1.A Context and Problem Statement | CDSS mono-modais; custo de reengenharia por modalidade; ausência de representação compartilhada | Discussão de desempenho de classificadores |
| 1.B Objectives | Objetivo geral + SO-1..SO-5 do `doc-spec.md` | Objetivos do Paper B |
| 1.C Contributions | (i) detecção automática de 9 modos; (ii) contrato `SinalNormalizado`; (iii) pré-processamento adaptativo; (iv) feature set multi-domínio; (v) avaliação em 30 bases reais | Contribuições de modelagem |
| 1.D Paper Organization | Mapa das seções | — |

### Seção 2 — Background and Related Work (`02-fundamentacao.tex`)

| Subseção | Conteúdo | Fora de escopo |
|---|---|---|
| 2.A Biomedical Signal Families | Definição formal de F1/F3/F4/tabular/imagem 2D e seus formatos (`.dat/.hea`, `.edf/.bdf`, `.mat`, `.xml`, `.c3d`, `.dcm`, `.nii/.nii.gz`, `.mha`, CSV/TSV) | Fisiopatologia clínica detalhada |
| 2.B Radiomics and Handcrafted Feature Extraction | GLCM, morfologia, descritores de intensidade; radiômica 2D e 3D | Deep features / CNN (apenas citado como extensão) |
| 2.C Physiological Signal Processing | PSD por Welch, bandas EEG, detecção de picos R, HRV (RMSSD, SDNN, pNN50), espirometria (FVC, FEV1, PEF) | Interpretação diagnóstica |
| 2.D Data Ingestion Architectures in Health IT | Padrões de ingestão heterogênea, validação de esquema, contratos de dados | Arquitetura de agentes / LLM |
| 2.E Mathematical Formulations | Equações autorizadas em `specs/arquitetura.md` §3 | Equações de métricas de classificação |

### Seção 3 — Methodology (`03-metodologia.tex`)

| Subseção | Conteúdo | Artefato de código de referência |
|---|---|---|
| 3.A Pipeline Overview | Diagrama de blocos input → detecção → validação → leitura → pré-processamento → extração → vetor de features | `Fig. 1` |
| 3.B Automatic Input-Structure Detection | Regras de decisão dos 9 modos; predicados de extensão; busca recursiva de pastas-rótulo | `app.py::detectar_estrutura`, `pipeline/io_utils.py` |
| 3.C Schema Validation | Validação Pydantic e leitura de cabeçalho | `pipeline/ingestao.py` |
| 3.D Unified Data Contract | Dataclass `SinalNormalizado` (campos, invariantes, downsampling de visualização) | `pipeline/io_sinais.py` |
| 3.E Family-Specific Readers | Despacho por família e bibliotecas correspondentes | `leitura_temporal.py`, `leitura_dicom.py`, `leitura_volumetrica.py` |
| 3.F Adaptive Preprocessing | Análise da base, decisão de estratégia e justificativa automática | `analise_base.py`, `preprocessamento.py` |
| 3.G Multi-Domain Feature Extraction | Features por família (F1 tempo/frequência/específicas; F3 GLCM + DICOM; F4 radiômica 3D; tabular; imagem 2D) | `extracao*.py`, `dados_tabulares.py` |
| 3.H Feature Vector Consolidation | Convergência para vetor comum; dimensionalidade por família | — |
| 3.I Evaluation Protocol for the Pipeline | O que é medido: modo detectado vs. esperado, execução sem exceção, nº de features por base | `specs/arquitetura.md` §4 |

> **Regra:** a Seção 3 descreve **apenas** o caminho até o vetor de features. Menções a classificadores
> limitam-se a "the resulting feature vector is consumed by the downstream modeling stage".

### Seção 4 — Results and Discussion (`04-resultados.tex`)

| Subseção | Conteúdo | Fonte dos números |
|---|---|---|
| 4.A Benchmark Composition | 30 bases reais, distribuição por família | `specs/arquitetura.md` §4.1 |
| 4.B Detection Robustness | Modo detectado por base; execuções sem exceção; casos de divergência (ex.: bases F1 distribuídas como CSV detectadas como `tabular`) | `specs/arquitetura.md` §4.2 |
| 4.C Feature Coverage per Family | Dimensionalidade do vetor por família (F1, F3, F4, tabular, imagem 2D) | `specs/arquitetura.md` §4.3 |
| 4.D Extracted Biomarkers per Family | Descritores efetivamente produzidos por família | `specs/arquitetura.md` §4.4 |
| 4.E Discussion | Flexibilidade vs. especialização; limites da detecção por extensão; efeito da dimensionalidade | — |

> **Proibido nesta seção:** AUC, sensibilidade, especificidade, MCC, Kappa, ECE, latência de
> inferência, ranking de modelos e conteúdo de laudo. Esses resultados existem no repositório mas
> pertencem ao Paper B.

### Seção 5 — Conclusion (`05-conclusao.tex`)

| Subseção | Conteúdo |
|---|---|
| 5.A Contributions | Síntese dos SO-1..SO-5 atendidos |
| 5.B Limitations | Detecção baseada em extensão/estrutura de diretório; custo de memória em F4; famílias F2 (áudio) e F5 (vídeo) fora de escopo |
| 5.C Future Work | Extensão do dispatcher a novas famílias; features aprendidas (CNN) como alternativa às handcrafted; encaminhamento explícito para o Paper B |
