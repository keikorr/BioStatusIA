# BioStatusIA

> Sistema de Apoio à Decisão Clínica (CDSS) para análise automatizada de imagens médicas e dados clínicos tabulares, com IA Multi-Agente local.

Pipeline completo orquestrado por agentes CrewAI rodando sobre LLM local (Ollama), com classificação ML clássica (SVM, Random Forest) e interface web Flask em duas telas.

Projeto acadêmico de mestrado em IA na Saúde — Fortaleza, CE.

---

## Princípio fundamental

**O sistema aceita qualquer tipo de dado.** Ao receber uma entrada, ele:

1. Detecta automaticamente a estrutura (imagem única, várias imagens, dataset rotulado, CSV tabular ou multimodal)
2. Analisa estatisticamente a base (intensidade, ruído, contraste, outliers, normalidade)
3. Decide a estratégia de pré-processamento (denoising, normalização, equalização)
4. Extrai biomarcadores radiômicos ou processa features tabulares
5. Treina classificadores (quando há rótulos)
6. Gera laudo preliminar via agentes IA

---

## Modos detectados automaticamente

| Modo | Entrada | O que o pipeline faz |
|---|---|---|
| `imagem_unica` | Uma imagem `.png/.jpg/.bmp/.tif` | Extrai biomarcadores + laudo IA |
| `imagens_soltas` | Pasta/ZIP com imagens sem rótulos | Estatísticas + boxplot + laudo IA |
| `dataset_rotulado` | Pasta com subpastas `benign/` + `malignant/` | Tudo + treina SVM/RF + ROC + matriz de confusão |
| `tabular` | CSV/TXT/TSV com features clínicas | Análise tabular + classificadores + laudo do bioestatístico |
| `multimodal` | Pasta/ZIP com imagens **e** CSV juntos | Pipeline de imagens + análise tabular adicional |

Sinônimos de pastas reconhecidos como rótulo:
- Benignas: `benign`, `benigno`, `normal`, `negative`, `0`
- Malignas: `malignant`, `malign`, `maligno`, `abnormal`, `positive`, `1`

---

## Arquitetura — pipeline 100% agentificado

Cada etapa do pipeline é executada por um agente CrewAI através de uma tool dedicada.

### Crew de Imagem — 4 agentes em sequência

```
engenheiro_pdi
   ↓ FerramentaAnaliseBase → analise_base.json
analista_tecnico
   ↓ FerramentaExtrairBiomarcadores → biomarcadores.json
cientista_dados
   ↓ FerramentaTreinarClassificador → metricas.json
radiologista_ia
   ↓ (sem tool — interpreta tudo) → laudo Markdown final
```

### Crew Tabular — 1 agente

```
bioestatistico
   ↓ FerramentaAnaliseTabular → laudo Markdown
```

Os agentes se comunicam via JSONs persistidos em `static/runs/<id>/`, o que evita que o LLM precise ingerir megabytes de dados numéricos.

---

## Biomarcadores extraídos

9 biomarcadores em 3 grupos:

| Grupo | Métrica | Sinal de Malignidade |
|---|---|---|
| **Morfologia** | Circularidade | Baixa (<0.7) |
|  | Solidez | Baixa (margens irregulares) |
| **Textura (GLCM)** | Contraste | Alto |
|  | Homogeneidade | Baixa |
|  | Energia | Baixa |
|  | Entropia | Alta (tecido heterogêneo) |
| **Distribuição** | SNR | Qualidade do sinal (não diagnóstico) |
|  | Assimetria (skewness) | Complementar |
|  | Curtose | Complementar |

**Regra clínica geral**: baixa solidez + alta entropia → suspeito de malignidade.

---

## Pré-processamento adaptativo

Antes da extração, o `engenheiro_pdi` analisa a base e escolhe a estratégia ótima:

| Condição detectada | Estratégia escolhida |
|---|---|
| Ruído médio > 0.05 (`estimate_sigma`) | Non-Local Means |
| Ruído ≤ 0.05 | Gaussian blur 5×5 (default) |
| Outliers > 10% das imagens (IQR) | Normalização por percentil 1–99% |
| Outliers ≤ 10% | Min-max [0, 1] (default) |
| Contraste médio < 30 | CLAHE |
| Contraste ≥ 30 | Sem equalização |
| Tamanhos heterogêneos | Resize obrigatório 256×256 |

Cada decisão é justificada na Tela 2 com o valor detectado e a regra aplicada.

---

## Stack tecnológica

| Camada | Tecnologia |
|---|---|
| Backend | Python 3.11, Flask 3.1 |
| LLM local | Ollama (`qwen2.5:3b`) |
| Agentes | CrewAI ≥0.203 |
| Visão computacional | OpenCV, scikit-image |
| ML clássico | scikit-learn (SVM RBF, Random Forest) |
| Banco de dados | SQLite |
| Gerenciador de pacotes | `uv` |
| Frontend | HTML5 + Tailwind CSS (CDN) |
| Gráficos | Plotly.js (CDN) |
| Dataset de imagem | BUSI (via KaggleHub) |
| Dataset tabular | Wisconsin Breast Cancer (via sklearn) |

---

## Instalação

### Pré-requisitos

- Python 3.10–3.12
- [uv](https://github.com/astral-sh/uv) — gerenciador de pacotes
- [Ollama](https://ollama.com) com o modelo `qwen2.5:3b` baixado:
  ```bash
  ollama pull qwen2.5:3b
  ```

### Setup do projeto

```bash
git clone https://github.com/JuniorSoares716/BioStatusIA.git
cd BioStatusIA
uv sync
```

### Configuração

Crie um arquivo `.env` na raiz:

```env
MODEL=ollama/qwen2.5:3b
API_BASE=http://localhost:11434
PYTHONUTF8=1
PYTHONIOENCODING=utf-8
```

---

## Como rodar

### Servidor web (modo principal)

```bash
uv run flask --app src/biostatusia/app.py run --port 5000
```

Abra `http://localhost:5000` — você verá a **Tela 1** com drag & drop para upload.

### Datasets de teste rápido

Após gerar via scripts, fica disponível:

- **Mini-BUSI** (40 imagens, ~3-5 min): use o caminho `dataset_teste/`
- **WBCD-50** (50 amostras tabulares, ~30s-1min): use `dataset_teste_csv/wbcd_50.csv`

### CLI retrocompatível (sem UI)

```bash
uv run biostatsia
```

Processa a primeira imagem benigna do BUSI e gera HTMLs estáticos.

---

## Interface

### Tela 1 — Upload

- Drag & drop para imagem, ZIP ou CSV
- Campo alternativo para caminho local
- Se vazio, usa o cache do KaggleHub
- Cards mostrando os 4 modos suportados
- Pipeline visual em 5 etapas

### Tela 2 — Resultados

Seções **sempre presentes**:
- Modo detectado + contagem de amostras
- Tabela de estatísticas descritivas
- Laudo IA em Markdown
- Histórico de análises do SQLite

Seções **condicionais**:

| Seção | Quando aparece |
|---|---|
| Badge do melhor classificador | Se treinou (rotulado/tabular com ≥10 amostras) |
| Análise da Base + Estratégia de Pré-processamento | Modos com imagem |
| Análise dos Dados Tabulares | Modos `tabular` e `multimodal` |
| Boxplot de biomarcadores | Modos com imagem e >1 imagem |
| Comparação SVM vs RF + Curva ROC + Matriz de Confusão | Apenas se treinado |

---

## Estrutura do projeto

```
BioStatusIA/
├── README.md
├── CLAUDE.md                          # Diretrizes do projeto para Claude Code
├── pyproject.toml
├── uv.lock
├── .env                               # MODEL e API_BASE do Ollama (não versionado)
├── biostatusia.db                     # SQLite (gerado em runtime, não versionado)
├── models/                            # Modelos .pkl treinados (não versionado)
├── dataset_teste/                     # Mini-BUSI para testes (não versionado)
├── dataset_teste_csv/                 # WBCD-50 tabular (versionado)
│
└── src/biostatusia/
    ├── app.py                         # Servidor Flask — roteia e dispara crews
    ├── main.py                        # CLI retrocompatível
    ├── crew.py                        # BioStatusIACrew + BioStatusIACrewTabular
    ├── database.py                    # SQLite: analises + resultados_pipeline
    │
    ├── pipeline/                      # Funções puras (chamadas pelas tools)
    │   ├── io_utils.py                # listar_imagens, criar_pasta_run
    │   ├── analise_base.py            # analisar_base + decidir_estrategia
    │   ├── preprocessamento.py        # preprocessar + preprocessar_adaptativo
    │   ├── segmentacao.py
    │   ├── extracao.py                # extrair_todos (com estratégia)
    │   ├── classificador.py           # treinar() + treinar_vetores()
    │   └── dados_tabulares.py         # CSV/TXT: carregar, schema, features, stats
    │
    ├── config/
    │   ├── agents.yaml                # 5 agentes
    │   └── tasks.yaml                 # 5 tasks
    │
    ├── tools/                         # CrewAI BaseTool — wrappers sobre pipeline/
    │   ├── analise_base_tool.py       # FerramentaAnaliseBase
    │   ├── extracao_tool.py           # FerramentaExtrairBiomarcadores (lote)
    │   ├── treino_tool.py             # FerramentaTreinarClassificador
    │   ├── tabular_tool.py            # FerramentaAnaliseTabular
    │   └── custom_tool.py             # FerramentaAnaliseImagem (single, legado)
    │
    ├── static/
    │   ├── uploads/                   # Arquivos enviados pelo usuário
    │   └── runs/                      # Workspaces dos kickoffs (JSONs)
    │
    └── templates/
        ├── tela1_upload.html
        └── tela2_resultados.html
```

---

## Banco de dados (SQLite)

### Tabela `analises`
| Coluna | Tipo |
|---|---|
| `id` | INTEGER PRIMARY KEY |
| `data_hora` | TEXT (ISO 8601) |
| `imagem` | TEXT (caminho) |
| `categoria` | TEXT (`BENIGNO` / `MALIGNO` / `INDEFINIDO` / `TABULAR`) |
| `laudo` | TEXT (Markdown) |

### Tabela `resultados_pipeline`
| Coluna | Tipo |
|---|---|
| `id` | INTEGER PRIMARY KEY |
| `data_hora` | TEXT |
| `dataset_path` | TEXT |
| `n_imagens` | INTEGER |
| `pipeline_json` | TEXT (JSON com todo o resultado) |
| `melhor_modelo` | TEXT |
| `analise_id` | INTEGER (FK → `analises.id`) |

---

## Trade-offs conhecidos

- **Lentidão do pipeline completo**: 4 agentes × ~30s por chamada LLM no Ollama local = ~2-5 min por análise de imagens. O modo tabular roda em ~30s-1min.
- **Non-Local Means** é ~10× mais lento que Gaussian. Em datasets >500 imagens, a extração ficará lenta se ruído alto for detectado.
- **Encoding no Windows**: o CrewAI emite emojis nos logs. Terminal com `charmap` (cp1252) gera `[EventBus Error]` — avisos cosméticos, não afetam execução. Mitigação no `.env`: `PYTHONUTF8=1` e `PYTHONIOENCODING=utf-8`.

---

## Aviso ético

Este sistema é uma **ferramenta de suporte à decisão clínica**. Os laudos gerados pelos agentes IA **não substituem a avaliação de um médico habilitado**. Esse aviso é mantido em toda saída visual e em todos os laudos.

---

## Licença

MIT
