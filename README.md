# BioStatusIA v2

> Sistema de Apoio à Decisão Clínica (CDSS) para análise automatizada de **18 tipos de sinais biomédicos** em 5 famílias, com IA Multi-Agente local, AutoML de 6 modelos e Laudo Interativo por seleção de ROI.

Pipeline 100% orquestrado por agentes CrewAI rodando sobre LLM local (Ollama), com classificação AutoML (6 modelos, 5-fold CV, métricas enriquecidas) e interface web Flask com 4 abas.

Projeto acadêmico de mestrado em IA na Saúde — Fortaleza, CE.

---

## Princípio fundamental

**O sistema aceita qualquer tipo de dado biomédico.** Ao receber uma entrada, ele:

1. Detecta automaticamente a estrutura e a família de sinal (10 modos)
2. Carrega e normaliza via `SinalNormalizado` (dataclass universal)
3. Extrai biomarcadores específicos da família detectada
4. Treina 6 classificadores concorrentes com avaliação enriquecida (quando há rótulos)
5. Gera laudo preliminar via agentes IA especializados por família
6. Permite laudo interativo focado em seleção de ROI / trecho temporal / frame de vídeo

---

## 5 Famílias de Sinal Suportadas

| Família | Tipos | Formatos de Entrada |
|---|---|---|
| **F1 — Sinais Temporais** | ECG, EEG, EMG, EOG, PPG, PA, Espirometria, PSG, Movimento | `.dat/.hea`, `.edf`, `.bdf`, `.mat`, `.xml`, `.c3d` |
| **F2 — Áudio Biomédico** | Fonocardiograma, Sons Pulmonares (ICBHI) | `.wav`, `.flac`, `.mp3` |
| **F3 — Imagem DICOM 2D** | Raio-X, Mamografia, Ultrassom estático | `.dcm` (arquivo único) |
| **F4 — Volume 3D** | TC, RM, PET/SPECT | `.nii`, `.nii.gz`, `.mha`, pasta com ≥10 `.dcm` |
| **F5 — Vídeo Médico** | Endoscopia, Ultrassom dinâmico, Ecocardiografia | `.mp4`, `.avi`, `.mov` |

---

## 10 Modos detectados automaticamente

| Modo | Entrada | Crew disparada |
|---|---|---|
| `imagem_unica` | Uma imagem `.png/.jpg` | BioStatusIACrew |
| `imagens_soltas` | Pasta/ZIP com imagens sem rótulos | BioStatusIACrew |
| `dataset_rotulado` | Pasta com subpastas `benign/` + `malignant/` | BioStatusIACrew |
| `tabular` | CSV/TXT com features clínicas | BioStatusIACrewTabular |
| `multimodal` | Imagens **e** CSV juntos | BioStatusIACrew + tabular |
| `sinal_temporal` | ECG / EEG / EMG / ... | BioStatusIACrewSinal |
| `audio_biomedico` | Fonocardiograma / Sons pulmonares | BioStatusIACrewSinal |
| `imagem_dicom_2d` | DICOM único (Raio-X, Mamografia...) | BioStatusIACrewImagem3D |
| `volume_3d` | NIfTI / MHA / Série DICOM ≥10 arquivos | BioStatusIACrewImagem3D |
| `video_medico` | Endoscopia / Ultrassom dinâmico | BioStatusIACrewVideo |

Nomes de pastas reconhecidos como rótulo — Benignas: `benign`, `benigno`, `normal`, `negative`, `0` | Malignas: `malignant`, `malign`, `maligno`, `abnormal`, `positive`, `1`

---

## Arquitetura — pipeline 100% agentificado (v2)

6 Crews, 11 agentes, 10 tools — todos em processo `sequential`.

### Crews de Sinal e Imagem

```
BioStatusIACrewSinal (F1/F2)
  analista_sinais_fisiologicos
    ├─ FerramentaExtrairSinalTemporal → biomarcadores_temporal.json
    └─ FerramentaExtrairAudio        → biomarcadores_audio.json
  radiologista_ia → laudo Markdown

BioStatusIACrewImagem3D (F3/F4)
  especialista_imagem_medica
    ├─ FerramentaExtrairDICOM        → biomarcadores_dicom.json
    └─ FerramentaExtrairVolume3D     → biomarcadores_volumetrico.json
  radiologista_ia → laudo Markdown

BioStatusIACrewVideo (F5)
  analista_video_medico
    └─ FerramentaExtrairVideo        → biomarcadores_video.json
  radiologista_ia → laudo Markdown
```

### Crew de Imagem Original (Ultrassom)

```
BioStatusIACrew
  engenheiro_pdi       → analise_base.json
  analista_tecnico     → biomarcadores.json
  cientista_dados      → metricas.json
  radiologista_ia      → laudo Markdown
```

### Crew Tabular e Laudo Interativo

```
BioStatusIACrewTabular
  bioestatistico → FerramentaAnaliseTabular → laudo Markdown

BioStatusIACrewInterativo
  radiologista_ia_interativo (sem tool, max_iter=4)
  → laudo focado no trecho/região selecionado
```

Os agentes se comunicam via JSONs em `static/runs/<id>/` — o LLM recebe resumos em texto, não dados brutos.

---

## AutoML — 6 Modelos Concorrentes

`pipeline/avaliacao_modelos.py` treina em 5-fold StratifiedKFold:

| Modelo | Tipo |
|---|---|
| Regressão Logística | Linear |
| KNN | Baseado em distância |
| SVM RBF | Kernel não-linear |
| Random Forest | Ensemble (100 árvores) |
| Gradient Boosting | Boosting (100 estimadores) |
| MLP Neural Network | Rede neural (64×32) |

**Métricas por modelo:** acurácia, sensibilidade, especificidade, precisão, recall, F1, AUC, ECE (Expected Calibration Error), latência de inferência (ms), tempo de treino (s).

**Teste de McNemar** entre os 2 melhores modelos — chi², p-value, significância estatística.

**Critério de seleção:** maior AUC, com preferência por sensibilidade ≥ 0.80 (minimiza falso-negativo).

---

## Biomarcadores extraídos por família

### F1 — Sinais Temporais
- Tempo: RMS, média, desvio, skewness, kurtosis, pico-a-pico, SNR_dB
- Frequência: PSD (Welch), centroide espectral, 4 bandas de potência, freq dominante
- ECG: FC_bpm, RMSSD, SDNN, pNN50
- EEG: bandas delta/theta/alpha/beta/gamma, ratio alpha/beta
- EMG: RMS envelope, frequência mediana
- Espirometria: FVC, FEV1, FEV1/FVC, PEF

### F2 — Áudio Biomédico
- MFCCs (20 coeficientes) + delta MFCCs
- Centroide espectral, bandwidth, rolloff, chroma (12), flatness
- ZCR, RMS envelope, duração, energia por banda de frequência

### F3 — DICOM 2D
- 9 biomarcadores radiômicos (morfologia, GLCM, distribuição de intensidade)
- Densidade alta (%), gradiente médio, uniformidade, modalidade DICOM
- Pixel spacing, hounsfield_range, janelamento HU automático

### F4 — Volume 3D
- Estatísticas globais: média, desvio, P5/P95, voxels_altos
- GLCM por plano ortogonal (axial, coronal, sagital)
- Morfologia 3D: volume da lesão (mm³), esfericidade, bounding box axes

### F5 — Vídeo Médico
- Brilho médio/desvio, variação temporal, contagem de frames
- Motion index por frame, frame de maior movimento, P90 motion
- Textura do keyframe: GLCM, entropia, skewness, kurtosis

### Imagem de Ultrassom (original)
| Grupo | Métrica | Sinal de Malignidade |
|---|---|---|
| Morfologia | Circularidade | Baixa (<0.7) |
| Morfologia | Solidez | Baixa (margens irregulares) |
| Textura (GLCM) | Contraste | Alto |
| Textura (GLCM) | Homogeneidade | Baixa |
| Textura (GLCM) | Energia | Baixa |
| Textura (GLCM) | Entropia | Alta (tecido heterogêneo) |
| Distribuição | SNR | Qualidade do sinal |
| Distribuição | Assimetria | Complementar |
| Distribuição | Curtose | Complementar |

---

## Pré-processamento adaptativo (imagens)

O `engenheiro_pdi` analisa a base antes da extração e escolhe a estratégia:

| Condição | Estratégia |
|---|---|
| Ruído médio > 0.05 | Non-Local Means |
| Ruído ≤ 0.05 | Gaussian blur 5×5 |
| Outliers > 10% (IQR) | Normalização percentil 1–99% |
| Outliers ≤ 10% | Min-max [0,1] |
| Contraste médio < 30 | CLAHE |
| Contraste ≥ 30 | Sem equalização |
| Tamanhos heterogêneos | Resize 256×256 obrigatório |

---

## Interface — Tela 2 com 4 abas

### Aba 1 — Pré-processamento
Estratégia adaptativa com justificativas baseadas nas estatísticas detectadas.

### Aba 2 — Estatísticas
Tabela de biomarcadores, boxplot de distribuição, schema tabular e 31 métricas univariadas.

### Aba 3 — AutoML & Laudo
Pódio dos 6 modelos, gráficos Plotly.js (ROC, Confusão, Comparativo), laudo clínico em Markdown, histórico SQLite.

### Aba 4 — Laudo Interativo
Seleção de região de interesse diretamente na interface → laudo IA focado exclusivamente no trecho selecionado.

| Família | Interface |
|---|---|
| F1/F2 | Plotly brush selection em série temporal + dropdown de canal |
| F3 | Canvas overlay para ROI retangular em DICOM |
| F4 | Slider de slice axial + canvas ROI |
| F5 | Slider de frame + range de frames para análise |

---

## Stack tecnológica (v2)

| Camada | Tecnologia |
|---|---|
| Backend | Python 3.11, Flask 3.1 |
| LLM local | Ollama (`qwen2.5:3b`) |
| Agentes | CrewAI ≥0.203 (6 crews, 11 agentes) |
| Sinais fisiológicos | MNE-Python, wfdb |
| Áudio biomédico | librosa, soundfile |
| Imagens DICOM | pydicom |
| Volumes 3D | nibabel, SimpleITK |
| Visão computacional | OpenCV, scikit-image |
| AutoML | scikit-learn (6 modelos) |
| Banco de dados | SQLite (3 tabelas) |
| Gerenciador de pacotes | `uv` |
| Frontend | HTML5 + Tailwind CSS (CDN) |
| Gráficos | Plotly.js (CDN) |

---

## Instalação

### Pré-requisitos

- Python 3.10–3.12
- [uv](https://github.com/astral-sh/uv)
- [Ollama](https://ollama.com) com `qwen2.5:3b`:
  ```bash
  ollama pull qwen2.5:3b
  ```

### Setup

```bash
git clone https://github.com/keikorr/BioStatusIA.git
cd BioStatusIA
uv sync
```

### Configuração `.env`

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

Abra `http://localhost:5000` — Tela 1 com drag & drop para qualquer tipo de dado.

### Datasets de validação (Kaggle)

| Família | Dataset | Kaggle slug |
|---|---|---|
| F1 (ECG) | ECG Heartbeat Categorization | `shayanfazeli/heartbeat` |
| F2 (Sons Pulmonares) | Respiratory Sound Database ICBHI 2017 | `vbookshelf/respiratory-sound-database` |
| F3 (Raio-X) | Chest X-Ray Images (Pneumonia) | `paultimothymooney/chest-xray-pneumonia` |
| F5 (Endoscopia) | Kvasir Dataset v2 | `meliodas23/kvasir-v2` |

### Datasets de teste local

- **Mini-BUSI** (40 imagens): `dataset_teste/`
- **WBCD-50** (50 amostras tabulares): `dataset_teste_csv/wbcd_50.csv`

### CLI retrocompatível (sem UI)

```bash
uv run biostatsia
```

---

## Estrutura do projeto

```
BioStatusIA/
├── README.md
├── CLAUDE.md                          # Diretrizes do projeto para Claude Code
├── docs/
│   └── documentacao_notion.md         # Documentação completa no formato Notion
├── pyproject.toml
├── uv.lock
├── .env                               # MODEL, API_BASE (não versionado)
├── biostatusia.db                     # SQLite (gerado em runtime, não versionado)
├── models/                            # Modelos .pkl treinados (não versionado)
├── dataset_teste/                     # Mini-BUSI para testes
├── dataset_teste_csv/                 # WBCD-50 tabular
│
└── src/biostatusia/
    ├── app.py                         # Flask — 10 modos, 5 rotas (+3 novas v2)
    ├── main.py                        # CLI retrocompatível
    ├── crew.py                        # 6 Crews CrewAI
    ├── database.py                    # SQLite: 3 tabelas + migração v2
    │
    ├── pipeline/                      # Funções puras (chamadas pelas tools)
    │   ├── io_utils.py                # Extensões + predicados 5 famílias
    │   ├── io_sinais.py               # SinalNormalizado + carregar_sinal()
    │   ├── analise_base.py            # analisar_base + decidir_estrategia
    │   ├── preprocessamento.py        # preprocessar + preprocessar_adaptativo
    │   ├── segmentacao.py
    │   ├── extracao.py                # extrair_todos (imagens, com estratégia)
    │   ├── classificador.py           # treinar() + treinar_vetores()
    │   ├── dados_tabulares.py         # CSV/TXT: schema, features, stats
    │   ├── avaliacao_modelos.py       # 6 modelos, 5-fold CV, ECE, McNemar
    │   ├── leitura_temporal.py        # Lê .dat/.edf/.mat/.xml/.c3d
    │   ├── leitura_audio.py           # Lê .wav/.flac/.mp3
    │   ├── leitura_dicom.py           # Lê .dcm único ou série
    │   ├── leitura_volumetrica.py     # Lê .nii/.nii.gz/.mha
    │   ├── leitura_video.py           # Lê .mp4/.avi/.mov
    │   ├── extracao_temporal.py       # Features F1
    │   ├── extracao_audio.py          # Features F2
    │   ├── extracao_dicom.py          # Features F3
    │   ├── extracao_volumetrica.py    # Features F4
    │   └── extracao_video.py          # Features F5
    │
    ├── config/
    │   ├── agents.yaml                # 11 agentes
    │   └── tasks.yaml                 # 11 tasks
    │
    ├── tools/                         # 10 tools CrewAI
    │   ├── analise_base_tool.py
    │   ├── extracao_tool.py
    │   ├── treino_tool.py
    │   ├── tabular_tool.py
    │   ├── custom_tool.py             # legado
    │   ├── sinais_temporais_tool.py
    │   ├── audio_biomedico_tool.py
    │   ├── dicom_tool.py
    │   ├── volumetrico_tool.py
    │   └── video_medico_tool.py
    │
    ├── static/
    │   ├── uploads/                   # Arquivos enviados
    │   └── runs/                      # Workspaces dos kickoffs (JSONs)
    │
    └── templates/
        ├── tela1_upload.html          # Upload universal (10 modos)
        └── tela2_resultados.html      # 4 abas + Laudo Interativo
```

---

## Banco de dados (v2 — 3 tabelas)

### `analises`
| Coluna | Tipo | Descrição |
|---|---|---|
| `id` | INTEGER PK | — |
| `data_hora` | TEXT | ISO 8601 |
| `imagem` | TEXT | caminho do arquivo analisado |
| `categoria` | TEXT | `BENIGNO` / `MALIGNO` / `INDEFINIDO` / `TABULAR` / `SINAL` |
| `laudo` | TEXT | Markdown gerado pelo agente |

### `resultados_pipeline`
| Coluna | Tipo | Descrição |
|---|---|---|
| `id` | INTEGER PK | — |
| `data_hora` | TEXT | ISO 8601 |
| `dataset_path` | TEXT | caminho do dataset |
| `n_imagens` | INTEGER | amostras processadas |
| `pipeline_json` | TEXT | payload completo para Tela 2 |
| `melhor_modelo` | TEXT | nome do vencedor AutoML |
| `analise_id` | INTEGER | FK → analises |
| `familia_sinal` | TEXT | `F1`–`F5` (novo v2) |
| `sinal_tipo` | TEXT | `ECG`, `Raio-X`, etc. (novo v2) |

### `laudos_interativos` (novo v2)
| Coluna | Tipo | Descrição |
|---|---|---|
| `id` | INTEGER PK | — |
| `resultado_id` | INTEGER | FK → resultados_pipeline |
| `trecho_inicio` | REAL | segundos ou índice de início |
| `trecho_fim` | REAL | segundos ou índice de fim |
| `roi_json` | TEXT | JSON `{x,y,w,h}` para ROI de imagem |
| `canal` | TEXT | canal selecionado (lead ECG, etc.) |
| `slice_idx` | INTEGER | índice de slice para volumes 3D |
| `laudo_foco` | TEXT | laudo focado gerado |
| `data_hora` | TEXT | ISO 8601 |

---

## Trade-offs conhecidos

- **Pipeline completo**: 4–6 agentes × ~30s por chamada LLM local = 3–8 min por análise completa.
- **Non-Local Means**: ~10× mais lento que Gaussian. Em datasets >500 imagens com ruído alto, extração notavelmente mais lenta.
- **Volumes 3D**: `MAX_CONTENT_LENGTH = 4 GB` — uploads grandes consomem memória durante extração de slices.
- **Encoding no Windows**: CrewAI emite emojis nos logs — `[EventBus Error]` com `charmap` (cp1252). Cosméticos. Mitigação: `.env` com `PYTHONUTF8=1`.

---

## Aviso ético

Este sistema é uma **ferramenta de suporte à decisão clínica**. Os laudos gerados pelos agentes IA **não substituem a avaliação de um médico habilitado**. Esse aviso é obrigatório em toda saída visual, em todos os laudos e na 5ª seção do Laudo Interativo.

---

## Licença

MIT
