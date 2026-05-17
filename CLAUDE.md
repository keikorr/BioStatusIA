# BioStatusIA — Diretrizes do Projeto para Claude

## O que é este projeto

Sistema de Apoio à Decisão Clínica (CDSS) para análise automatizada de imagens médicas (ultrassom mamário). O pipeline é **flexível e detecta automaticamente o tipo de entrada**: aceita uma imagem única, várias imagens soltas, ou um dataset rotulado. Combina **radiômica** (OpenCV/scikit-image), **classificadores ML clássicos** (SVM, Random Forest), **IA Multi-Agente** (CrewAI + Ollama) e uma **interface web Flask** com duas telas.

Contexto acadêmico: projeto de mestrado em IA na Saúde — Fortaleza, CE.

---

## Princípio fundamental — entrada flexível

> **O sistema aceita QUALQUER tipo de dado.** Sempre executa a análise estatística sobre o que receber, e depois adapta o pipeline ao que é viável.

Existem 5 modos detectados automaticamente em `app.py::detectar_estrutura()`:

| Modo | O que é | O que o pipeline faz |
|---|---|---|
| `imagem_unica` | Um único arquivo de imagem | Extrai biomarcadores + laudo IA |
| `imagens_soltas` | Pasta/ZIP com imagens sem rótulos | Estatísticas + boxplot + laudo IA na primeira imagem |
| `dataset_rotulado` | Pasta com subpastas `benign/` e `malignant/` | Estatísticas + treino de SVM/RandomForest + ROC + matriz de confusão + laudo IA |
| `tabular` | Arquivo único `.csv`/`.txt`/`.tsv` ou pasta só com tabulares | Schema + análise descritiva + classificadores. **Sem laudo IA** (sem imagem) |
| `multimodal` | Pasta/ZIP com imagens **e** CSV/TXT juntos | Pipeline de imagens completo + análise tabular adicional + classificador tabular separado |

A análise estatística sempre roda. O treino de classificadores só ocorre quando há rótulos e ≥10 amostras com 2 classes. O laudo IA roda apenas quando há imagem disponível.

### Nomes de pastas reconhecidos como rótulo

Constantes em `app.py`:
```python
PASTAS_BENIGNAS = {"benign", "benigno", "normal", "negative", "0"}
PASTAS_MALIGNAS = {"malignant", "malign", "maligno", "abnormal", "positive", "1"}
```

A busca é **recursiva** — funciona mesmo se as subpastas estiverem aninhadas dentro de uma estrutura como `Dataset_BUSI_with_GT/benign/`.

### Detecção de coluna-rótulo em CSV/TXT

`pipeline/dados_tabulares.py::detectar_schema()` identifica:
1. Coluna-rótulo por nome (`label`, `class`, `diagnosis`, `target`, `outcome`, `y`, `categoria`, `resultado`)
2. Se não achar por nome, usa a última coluna se tiver entre 2 e 10 valores únicos
3. Para rótulos binários, mapeia para 0/1 usando `MALIGNANT_KEYWORDS` (`m`, `malignant`, `positive`, `1`, `yes`...)

Separador do CSV é detectado automaticamente (`,`, `;`, `\t`, `|`). Encoding tenta UTF-8 com fallback para Latin-1.

---

## Estado atual do projeto

| Componente | Status |
|---|---|
| Motor de radiômica (`pipeline/extracao.py`) | Feito |
| Pipeline em 5 etapas (`pipeline/`) | Feito |
| Classificadores SVM + RandomForest | Feito |
| Dois agentes CrewAI + Ollama | Feito |
| Banco SQLite (`database.py`) com 2 tabelas | Feito |
| Servidor Flask (`app.py`) com 2 rotas | Feito |
| Tela 1 — upload com detecção automática | Feito |
| Tela 2 — gráficos condicionais por modo | Feito |
| Dashboard HTML estático CLI (`main.py`) | Mantido para retrocompatibilidade |

---

## Fluxo completo

```
[Tela 1 — Upload]
  Usuário envia: imagem, ZIP, ou caminho local
        │
        ▼
[detectar_estrutura()]
  Identifica modo: imagem_unica | imagens_soltas | dataset_rotulado
        │
        ▼
[1. Pré-processamento]  ←─ pipeline/preprocessamento.py
[2. Segmentação]        ←─ pipeline/segmentacao.py
[3. Extração]           ←─ pipeline/extracao.py (todas as imagens)
        │
        ▼
[Estatísticas descritivas]  ←─ app.py::computar_estatisticas()
  Média, mediana, desvio, min, max por biomarcador e categoria
        │
        ▼
[4. Classificador]  ←─ pipeline/classificador.py
  SÓ se modo == dataset_rotulado e >=10 imagens com 2 classes
  Treina SVM + RandomForest → métricas, ROC, matriz de confusão
        │
        ▼
[5. Laudo IA]
  CrewAI roda na primeira imagem (sempre)
  Saída: Markdown gerado por radiologista_ia
        │
        ▼
[Persistência]  ←─ database.py
  Tabela `analises` (laudo)
  Tabela `resultados_pipeline` (JSON com tudo)
        │
        ▼
[Tela 2 — Resultados]
  Sempre: modo detectado, estatísticas, distribuição, laudo, histórico
  Condicional (só rotulado): comparação de classificadores, ROC, matriz de confusão
```

---

## Stack

| Componente | Tecnologia | Versão |
|---|---|---|
| Python | 3.11 | `>=3.10,<3.13` |
| Gerenciador de pacotes | `uv` | Sempre `uv sync` / `uv add` |
| LLM | Ollama `qwen2.5:3b` | Configurado em `.env` |
| Agentes | CrewAI | `>=0.203.1,<1.0.0` |
| Servidor web | Flask | `>=3.0.0` |
| Banco de dados | SQLite (built-in) | `biostatusia.db` na raiz |
| Visão Computacional | OpenCV, scikit-image | — |
| Classificadores ML | scikit-learn | `>=1.3.0` |
| Gráficos | Plotly.js (via CDN) | 2.32 |
| Frontend | Tailwind CSS (via CDN) | latest |

Ao adicionar dependências: `uv add <pacote>` — nunca `pip install`.

---

## Estrutura de arquivos

```
BioStatusIA/
├── CLAUDE.md
├── .env                              # MODEL e API_BASE do Ollama — não commitar
├── pyproject.toml
├── biostatusia.db                    # SQLite — não versionar
├── models/                           # SVM e RF treinados (.pkl) — não versionar
├── dataset_teste/                    # Mini-dataset para testes rápidos
│
└── src/biostatusia/
    ├── app.py                        # Flask: detectar_estrutura, computar_estatisticas, rotas
    ├── main.py                       # Pipeline CLI (mantido para uso sem UI)
    ├── crew.py                       # Agentes CrewAI
    ├── database.py                   # SQLite: analises + resultados_pipeline
    │
    ├── pipeline/                     # Funções puras (chamadas pelas tools)
    │   ├── __init__.py
    │   ├── io_utils.py               # listar_imagens, eh_imagem, eh_tabular, criar_pasta_run
    │   ├── analise_base.py           # analisar_base + decidir_estrategia
    │   ├── preprocessamento.py       # preprocessar + preprocessar_adaptativo
    │   ├── segmentacao.py
    │   ├── extracao.py               # extrair_todos(caminho, estrategia)
    │   ├── classificador.py          # treinar() + treinar_vetores()
    │   └── dados_tabulares.py        # CSV/TXT: carregar, schema, features, estatísticas
    │
    ├── config/
    │   ├── agents.yaml               # 5 agentes
    │   └── tasks.yaml                # 5 tasks
    │
    ├── tools/                        # CrewAI BaseTool — wrappers sobre pipeline/
    │   ├── analise_base_tool.py      # FerramentaAnaliseBase
    │   ├── extracao_tool.py          # FerramentaExtrairBiomarcadores (lote)
    │   ├── treino_tool.py            # FerramentaTreinarClassificador
    │   ├── tabular_tool.py           # FerramentaAnaliseTabular
    │   └── custom_tool.py            # FerramentaAnaliseImagem (single image, legado)
    │
    ├── static/
    │   ├── uploads/                  # Arquivos enviados pelo usuário — não versionar
    │   └── runs/                     # Workspaces dos kickoffs (JSON intermediários) — não versionar
    │
    │   # Datasets de teste rápido (na raiz do projeto, não em src/):
    │   # dataset_teste/        → mini-BUSI (40 imagens)
    │   # dataset_teste_csv/    → WBCD-50 (50 amostras tabulares)
    │
    └── templates/
        ├── tela1_upload.html         # Upload com drag & drop
        └── tela2_resultados.html     # Gráficos condicionais por modo
```

---

## Como rodar

### Servidor web (modo principal)
```powershell
uv run flask --app src/biostatusia/app.py run --port 5000
```
Abrir `http://localhost:5000`.

### CLI (modo retrocompatível, sem UI)
```powershell
uv run biostatsia
```

---

## Tela 1 — Upload

**Rota**: `GET /` e `POST /analisar` — `src/biostatusia/templates/tela1_upload.html`

Aceita três formas de entrada:
1. **Upload de arquivo** (drag & drop ou seletor): imagem única ou ZIP
2. **Caminho manual** (texto): qualquer pasta no disco
3. **Vazio**: tenta usar o cache do KaggleHub (dataset BUSI)

Regras:
- Arquivos enviados vão para `src/biostatusia/static/uploads/`
- ZIPs são extraídos automaticamente para uma subpasta com o nome do arquivo
- Tamanho máximo: 500 MB (`MAX_CONTENT_LENGTH`)

---

## Tela 2 — Resultados (seções condicionais)

**Rota**: `GET /resultados/<int:resultado_id>` — `src/biostatusia/templates/tela2_resultados.html`

| Seção | Quando aparece |
|---|---|
| Modo detectado + nº de imagens/amostras | Sempre |
| Badge do melhor classificador | Apenas se `pipeline.metricas` existe |
| Aviso "classificador não treinado" | Se rotulado/tabular mas <10 amostras ou 1 só classe |
| **Análise dos Dados Tabulares (schema + stats)** | Se modo = `tabular` ou `multimodal` |
| **Análise da Base + Estratégia de Pré-processamento** | Modos com imagem (Etapa 0) |
| Tabela de estatísticas de biomarcadores | Modos com imagem |
| Boxplot de distribuição | Se modo com imagem + `n_imagens > 1` |
| Gráfico comparação de classificadores | Apenas se treinado |
| Curva ROC | Apenas se treinado |
| Matriz de confusão | Apenas se treinado |
| Laudo IA do `radiologista_ia` | Modos com imagem |
| Relatório textual da análise tabular | Modo `tabular` puro |
| Histórico de análises (SQLite) | Sempre |

Gráficos: **Plotly.js via CDN**. Os scripts checam `if (Object.keys(metricas).length)` antes de renderizar — se faltar dado, a seção simplesmente não aparece.

---

## Pipeline adaptativo em 6 etapas

Cada módulo em `src/biostatusia/pipeline/` é uma **função pura** (entrada → saída), sem I/O.

### Etapa 0 — Análise da Base (`analise_base.py::analisar_base` + `decidir_estrategia`)
- Executa **uma vez** sobre todas as imagens do dataset, antes da extração
- Computa: intensidade média/desvio, outliers (IQR), normalidade (Shapiro-Wilk), contraste médio, ruído estimado (`skimage.restoration.estimate_sigma`), consistência de tamanhos
- `decidir_estrategia()` retorna dict com `{denoising, normalizacao, equalizacao, tamanho_alvo, justificativas[]}`
- A estratégia é passada para `extrair_todos(caminho, estrategia=...)` para cada imagem

**Regras determinísticas de decisão:**

| Condição detectada | Estratégia escolhida |
|---|---|
| Ruído médio > 0.05 | Denoising = Non-Local Means |
| Ruído médio ≤ 0.05 | Denoising = Gaussian 5×5 (default) |
| Outliers > 10% das imagens | Normalização = percentil 1–99% |
| Outliers ≤ 10% | Normalização = min-max (default) |
| Contraste médio < 30 | Equalização = CLAHE |
| Contraste ≥ 30 | Equalização = nenhuma |
| Tamanhos heterogêneos | Resize obrigatório 256×256 |
| Shapiro p < 0.05 | Distribuição não-normal — apenas reportado |

Trade-off conhecido: Non-Local Means é ~10× mais lento que Gaussian. Em datasets grandes (>500 imagens) a extração fica notavelmente mais lenta quando ruído alto for detectado.

### Etapa 1 — Pré-processamento (`preprocessamento.py`)
Duas funções:
- `preprocessar(caminho, tamanho)` — versão padrão (Gaussian 5×5 + min-max), usada pelo `main.py` CLI
- `preprocessar_adaptativo(caminho, estrategia)` — aplica a config da Etapa 0:
  - Redimensiona conforme `tamanho_alvo`
  - CLAHE se `equalizacao == "clahe"`
  - Non-Local Means se `denoising == "nlmeans"`, senão Gaussian 5×5
  - Normalização por percentil 1–99% se `normalizacao == "percentil"`, senão min-max
- Entrada: caminho da imagem (+ estratégia para adaptativo) | Saída: `np.ndarray` float32 [0,1] ou `None`

### Etapa 2 — Segmentação (`segmentacao.py::segmentar`)
- Thresholding adaptativo Gaussiano
- Detecção de contornos, seleciona o de maior área
- Entrada: `np.ndarray` normalizado | Saída: `(máscara, img_u8)`

### Etapa 3 — Extração de Atributos (`extracao.py::extrair_todos`)
- 9 biomarcadores em 3 grupos: morfologia, textura GLCM, distribuição
- Assinatura: `extrair_todos(caminho, estrategia: dict | None = None)`
  - **Com estratégia** (rota Flask): chama `preprocessar_adaptativo` internamente
  - **Sem estratégia** (CrewAI tool, CLI): caminho PIL → RGB → grayscale (legado, preserva compatibilidade)
- Entrada: caminho da imagem (local ou URL) + estratégia opcional | Saída: `dict` ou `None`

### Etapa 4 — Classificador (`classificador.py::treinar`)
- Treina SVM (RBF) e RandomForest (100 árvores)
- Split estratificado 80/20, `random_state=42`
- StandardScaler aplicado antes
- Salva ambos em `models/modelo_*.pkl`
- Métricas: acurácia, precisão, recall, F1, AUC-ROC
- Inclui dados para gráficos: `roc_data` (FPR/TPR) e `confusion_matrix`
- Melhor modelo = maior AUC-ROC

### Etapa 5 — Relatório Final (`app.py::analisar`)
- Laudo via `BioStatusIACrew().crew().kickoff(...)`
- Persistência em `database.py::salvar` + `salvar_resultado`

---

## Agentes CrewAI — TODO o pipeline é agentificado

**Princípio fundamental**: cada etapa do pipeline é executada por um agente CrewAI através de uma tool. O Flask apenas roteia, cria o workspace (`static/runs/<id>/`), dispara a crew e consolida os JSONs persistidos pelos agentes.

### Crew 1: `BioStatusIACrew` — fluxo completo de imagem
Disparado para modos `imagem_unica`, `imagens_soltas`, `dataset_rotulado`, `multimodal`.
Processo: `sequential` — 4 agentes em sequência, comunicando via JSONs no workspace.

| Ordem | Agente | Tool | Output persistido |
|---|---|---|---|
| 1 | `engenheiro_pdi` | `FerramentaAnaliseBase` | `analise_base.json` |
| 2 | `analista_tecnico` | `FerramentaExtrairBiomarcadores` | `biomarcadores.json` |
| 3 | `cientista_dados` | `FerramentaTreinarClassificador` | `metricas.json` |
| 4 | `radiologista_ia` | — (sem tool) | Laudo Markdown final |

### Crew 2: `BioStatusIACrewTabular` — fluxo tabular
Disparado para modo `tabular`. Processo: `sequential` (1 agente).

| Agente | Tool |
|---|---|
| `bioestatistico` | `FerramentaAnaliseTabular` |

### Tools (todas em `tools/` seguindo CrewAI BaseTool + Pydantic args_schema)

| Tool | Wrapper sobre | Usado por |
|---|---|---|
| `FerramentaAnaliseBase` | `pipeline/analise_base.py` (analisar + decidir) | `engenheiro_pdi` |
| `FerramentaExtrairBiomarcadores` | `pipeline/extracao.py` (lote, com estratégia adaptativa) | `analista_tecnico` |
| `FerramentaTreinarClassificador` | `pipeline/classificador.py::treinar` | `cientista_dados` |
| `FerramentaAnaliseImagem` | `pipeline/extracao.py::extrair_todos` (single image, legado) | — (mantida para uso pontual) |
| `FerramentaAnaliseTabular` | `pipeline/dados_tabulares.py` | `bioestatistico` |

### Comunicação entre agentes (via filesystem)

Cada execução cria uma pasta `static/runs/run_<timestamp>/`. Os agentes:
1. Recebem `caminho_dataset` e `pasta_run` como inputs do kickoff
2. Tool de cada agente persiste seu output completo em JSON dentro de `pasta_run`
3. Tool retorna apenas um RESUMO em texto para o LLM (não os dados brutos)
4. O próximo agente lê os JSONs do agente anterior

Esse padrão permite o LLM raciocinar sobre os resumos sem ter que ingerir megabytes de dados numéricos.

### Configs (CrewBase auto-discovery)

- `config/agents.yaml` — 5 agentes: `engenheiro_pdi`, `analista_tecnico`, `cientista_dados`, `radiologista_ia`, `bioestatistico`
- `config/tasks.yaml` — 5 tasks: `tarefa_analise_base`, `tarefa_extracao`, `tarefa_treinar_classificador`, `tarefa_laudo`, `tarefa_laudo_tabular`

### Onde Flask ainda chama código diretamente

Apenas para operações que não fazem sentido envolver LLM (são determinísticas e baratas):
- `detectar_estrutura()` — roteamento de modo (decisão binária)
- `_consolidar_imagem()` — só lê os JSONs persistidos pelos agentes
- Estatísticas tabulares + classificador no modo tabular puro

A regra: **se o resultado precisa ser interpretado/explicado, vai via agente. Se é só roteamento ou consolidação, fica no Flask.**

---

## Banco de dados

### Tabela `analises`
```sql
id        INTEGER PRIMARY KEY AUTOINCREMENT
data_hora TEXT NOT NULL          -- ISO 8601
imagem    TEXT NOT NULL          -- caminho da imagem analisada
categoria TEXT NOT NULL          -- "BENIGNO" | "MALIGNO" | "INDEFINIDO"
laudo     TEXT                   -- output do radiologista_ia
```

### Tabela `resultados_pipeline`
```sql
id            INTEGER PRIMARY KEY AUTOINCREMENT
data_hora     TEXT NOT NULL
dataset_path  TEXT
n_imagens     INTEGER
pipeline_json TEXT               -- dict completo (modo, estatísticas, métricas, ROC, etc.)
melhor_modelo TEXT               -- "SVM" | "RandomForest" | "N/A"
analise_id    INTEGER            -- FK → analises.id
```

A coluna `pipeline_json` é o **payload principal** — guarda tudo que a Tela 2 precisa renderizar.

---

## Biomarcadores — regra de interpretação

| Métrica | Categoria | Sinal de Malignidade |
|---|---|---|
| Circularidade | Morfologia | Baixa (< 0.7) |
| Solidez | Morfologia | Baixa (margens irregulares) |
| Entropia | Textura (GLCM) | Alta (tecido heterogêneo) |
| Homogeneidade | Textura (GLCM) | Baixa |
| Energia | Textura (GLCM) | Baixa |
| Contraste | Textura (GLCM) | Alto |
| SNR | Intensidade | Qualidade do sinal — não diagnóstico |
| Assimetria | Intensidade | Complementar |
| Curtose | Intensidade | Complementar |

Regra geral: **baixa solidez + alta entropia → suspeito de malignidade**.

---

## Convenções de código

- **Português** para variáveis de domínio (`laudo`, `categoria`, `biomarcadores`, `solidez`). Inglês para infraestrutura (`conn`, `path`, `model`).
- **Sem comentários** que expliquem o "o quê" — só o "por quê" quando não óbvio.
- **Pipeline = funções puras**: cada etapa recebe e devolve dados, sem I/O.
- Toda a I/O (DB, HTML, arquivos) concentrada em `app.py` e `database.py`.
- **Templates HTML são a fonte da verdade visual** — nunca editar HTML gerado em runtime (legado do `main.py`).
- **Pydantic** para schemas de ferramentas CrewAI.

---

## Problema conhecido: encoding no Windows

CrewAI emite emojis nos logs do EventBus. Terminal Windows com `charmap` (cp1252) gera `[EventBus Error]`. Avisos cosméticos — não afetam execução.

Mitigação em `.env`:
```
PYTHONUTF8=1
PYTHONIOENCODING=utf-8
```

---

## O que NÃO fazer

- Não usar `pip install` — usar `uv add <pacote>`.
- Não commitar `.env`, `biostatusia.db`, `models/`, `src/biostatusia/static/uploads/`.
- Não editar HTMLs gerados em runtime (`dashboard_*.html`, `relatorio_*.html`).
- Não trocar `Process.sequential` por `Process.hierarchical` sem revisar `manager_llm`.
- Não aumentar `max_iter` dos agentes sem medir tempo de resposta.
- Não adicionar ferramentas ao `radiologista_ia`.
- Não restringir a detecção de estrutura — manter a flexibilidade do `detectar_estrutura()`.
- Não treinar classificadores fora do contexto rotulado — verificar `modo == 'dataset_rotulado'`.

---

## Aviso ético obrigatório

Este sistema é uma **ferramenta de suporte à decisão clínica**. Nenhuma mudança de código deve remover o aviso de que os laudos **não substituem a avaliação de um médico habilitado**. Esse aviso deve estar presente em toda saída visual e no laudo do `radiologista_ia`.
