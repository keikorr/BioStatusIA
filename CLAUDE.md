# BioStatusIA v2 — Diretrizes do Projeto para Claude

## O que é este projeto

Sistema de Apoio à Decisão Clínica (CDSS) para análise automatizada de **18 tipos de sinais biomédicos** organizados em 5 famílias. O pipeline é **flexível e detecta automaticamente o tipo de entrada**: aceita qualquer formato e adapta todo o processamento ao que for viável. Combina **radiômica e extração multi-domínio** (OpenCV/scikit-image/MNE/librosa), **AutoML com 6 classificadores e avaliação enriquecida** (Sensibilidade, Especificidade, ECE, McNemar), **IA Multi-Agente** (6 Crews CrewAI + Ollama) e uma **interface web Flask com 4 abas**.

Contexto acadêmico: projeto de mestrado em IA na Saúde — Fortaleza, CE.

---

## Princípio fundamental — entrada flexível

> **O sistema aceita QUALQUER tipo de dado.** Sempre executa análise estatística sobre o que receber e adapta o pipeline ao que é viável.

Existem **10 modos** detectados automaticamente em `app.py::detectar_estrutura()`:

| Modo | O que é | Crew disparada |
|---|---|---|
| `imagem_unica` | Uma imagem `.png/.jpg/.bmp/.tif` | `BioStatusIACrew` |
| `imagens_soltas` | Pasta/ZIP com imagens sem rótulos | `BioStatusIACrew` |
| `dataset_rotulado` | Pasta com subpastas `benign/` e `malignant/` | `BioStatusIACrew` |
| `tabular` | CSV/TXT/TSV único ou pasta só com tabulares | `BioStatusIACrewTabular` |
| `multimodal` | Pasta/ZIP com imagens **e** CSV/TXT juntos | `BioStatusIACrew` + tabular |
| `sinal_temporal` | Arquivos `.dat/.hea/.edf/.bdf/.mat/.xml/.c3d` | `BioStatusIACrewSinal` |
| `audio_biomedico` | Arquivos `.wav/.flac/.mp3` (fonocardiograma/sons pulmonares) | `BioStatusIACrewSinal` |
| `imagem_dicom_2d` | Arquivo `.dcm` único (Raio-X, Mamografia, Ultrassom estático) | `BioStatusIACrewImagem3D` |
| `volume_3d` | `.nii/.nii.gz/.mha` ou pasta com ≥10 `.dcm` (TC, RM, PET/SPECT) | `BioStatusIACrewImagem3D` |
| `video_medico` | `.mp4/.avi/.mov` (Endoscopia, Ultrassom dinâmico) | `BioStatusIACrewVideo` |
| `multimodal_expandido` | Mix de imagens/sinais/vídeo/tabular | `BioStatusIACrew` + sub-crews |

A análise estatística sempre roda. Treino de classificadores só ocorre com rótulos e ≥10 amostras com 2 classes. Laudo IA roda apenas quando há sinal ou imagem disponível.

---

## 5 Famílias de Sinal (v2)

| Família | Tipos suportados | Biblioteca de leitura |
|---|---|---|
| **F1 — Sinais Temporais** | ECG, EEG, EMG, EOG, PPG, PA, Espirometria, PSG, Movimento | `mne`, `wfdb`, `scipy`, `bioread` |
| **F2 — Áudio Biomédico** | Fonocardiograma, Sons Pulmonares | `soundfile`, `librosa`, `scipy` |
| **F3 — Imagem DICOM 2D** | Raio-X, Mamografia, Ultrassom estático | `pydicom` |
| **F4 — Volume 3D** | TC, RM, PET/SPECT | `nibabel`, `SimpleITK` |
| **F5 — Vídeo Médico** | Endoscopia, Ultrassom dinâmico | `cv2` (OpenCV) |

### `SinalNormalizado` — dataclass de saída unificada

```python
@dataclass
class SinalNormalizado:
    familia: str          # "F1" | "F2" | "F3" | "F4" | "F5"
    tipo: str             # "ECG" | "EEG" | "Fonocardiograma" | ...
    dados: np.ndarray     # array bruto
    taxa_amostragem: float
    canais: list[str]
    metadados: dict
    caminho_original: str
    dados_viz: list       # ≤2000 pontos para Plotly (downsampled)
```

Toda leitura passa por `pipeline/io_sinais.py::carregar_sinal()` que despacha para o leitor correto e retorna `SinalNormalizado`.

---

## Estado atual do projeto (v2)

| Componente | Status |
|---|---|
| Motor de radiômica (`pipeline/extracao.py`) | Feito |
| Extratores F1–F5 (`pipeline/extracao_*.py`) | Feito |
| Leitores F1–F5 (`pipeline/leitura_*.py`) | Feito |
| Dispatcher universal (`pipeline/io_sinais.py`) | Feito |
| AutoML 6 modelos + métricas enriquecidas (`pipeline/avaliacao_modelos.py`) | Feito |
| 6 Crews CrewAI | Feito |
| 11 agentes (`config/agents.yaml`) | Feito |
| 11 tasks (`config/tasks.yaml`) | Feito |
| 10 tools CrewAI (`tools/`) | Feito |
| Banco SQLite com 3 tabelas + migração v2 | Feito |
| Servidor Flask com 5 rotas + 3 rotas novas | Feito |
| Tela 1 — upload universal (10 modos) | Feito |
| Tela 2 — 4 abas + Laudo Interativo | Feito |
| Dashboard HTML estático CLI (`main.py`) | Mantido para retrocompatibilidade |

---

## Fluxo completo (v2)

```
[Tela 1 — Upload]
  Usuário envia: imagem, ZIP, CSV, .edf, .dcm, .nii, .mp4, caminho local...
        │
        ▼
[detectar_estrutura()]     ←── app.py
  10 modos: imagem_unica | imagens_soltas | dataset_rotulado | tabular |
            multimodal | sinal_temporal | audio_biomedico | imagem_dicom_2d |
            volume_3d | video_medico | multimodal_expandido
        │
        ├──[F1/F2]──► BioStatusIACrewSinal
        │                analista_sinais_fisiologicos (Temporal/Audio)
        │                → radiologista_ia
        │
        ├──[F3/F4]──► BioStatusIACrewImagem3D
        │                especialista_imagem_medica (DICOM 2D / Volume 3D)
        │                → radiologista_ia
        │
        ├──[F5]──────► BioStatusIACrewVideo
        │                analista_video_medico
        │                → radiologista_ia
        │
        ├──[Img]────► BioStatusIACrew (original)
        │                engenheiro_pdi → analista_tecnico
        │                → cientista_dados → radiologista_ia
        │
        └──[CSV]────► BioStatusIACrewTabular
                         bioestatistico → laudo tabular
        │
        ▼
[avaliacao_modelos.py]   ←── quando há rótulos e ≥10 amostras
  6 classificadores, 5-fold CV, métricas enriquecidas, McNemar A/B
        │
        ▼
[Persistência]  ←── database.py
  Tabela `analises`
  Tabela `resultados_pipeline` (família_sinal, sinal_tipo)
  Tabela `laudos_interativos` (novo v2)
        │
        ▼
[Tela 2 — Resultados (4 abas)]
  Aba 1: Estatísticas + Biomarcadores
  Aba 2: Pré-processamento + Estratégia
  Aba 3: AutoML + Laudo IA (Markdown)
  Aba 4: Laudo Interativo (seleção de ROI / trecho temporal / frame)
```

---

## Stack (v2)

| Componente | Tecnologia | Versão |
|---|---|---|
| Python | 3.11 | `>=3.10,<3.13` |
| Gerenciador de pacotes | `uv` | Sempre `uv sync` / `uv add` |
| LLM | Ollama `qwen2.5:3b` | Configurado em `.env` |
| Agentes | CrewAI | `>=0.203.1,<1.0.0` |
| Servidor web | Flask | `>=3.0.0` |
| Banco de dados | SQLite (built-in) | `biostatusia.db` na raiz |
| Visão Computacional | OpenCV, scikit-image | — |
| Sinais Fisiológicos | MNE-Python, wfdb | — |
| Áudio Biomédico | librosa, soundfile | — |
| DICOM | pydicom | — |
| Volumes 3D | nibabel, SimpleITK | — |
| Classificadores ML | scikit-learn | `>=1.3.0` (6 modelos) |
| Gráficos | Plotly.js (via CDN) | 2.32 |
| Frontend | Tailwind CSS (via CDN) | latest |

Ao adicionar dependências: `uv add <pacote>` — nunca `pip install`.

`MAX_CONTENT_LENGTH = 4 * 1024 * 1024 * 1024` (4 GB — necessário para volumes 3D e vídeos longos).

---

## Estrutura de arquivos (v2)

```
BioStatusIA/
├── CLAUDE.md
├── README.md
├── docs/
│   └── documentacao_notion.md       # Documentação completa no formato Notion
├── .env                              # MODEL, API_BASE, PYTHONUTF8 — não commitar
├── pyproject.toml
├── biostatusia.db                    # SQLite — não versionar
├── models/                           # Modelos .pkl treinados — não versionar
├── dataset_teste/                    # Mini-BUSI (imagens)
├── dataset_teste_csv/                # WBCD-50 (tabular)
│
└── src/biostatusia/
    ├── app.py                        # Flask: detectar_estrutura, rotas, consolidação
    ├── main.py                       # Pipeline CLI (retrocompatibilidade)
    ├── crew.py                       # 6 Crews CrewAI
    ├── database.py                   # SQLite: 3 tabelas + migração v2
    │
    ├── pipeline/                     # Funções puras (chamadas pelas tools)
    │   ├── __init__.py
    │   ├── io_utils.py               # Extensões + predicados para 5 famílias
    │   ├── io_sinais.py              # SinalNormalizado + carregar_sinal()
    │   ├── analise_base.py           # analisar_base + decidir_estrategia
    │   ├── preprocessamento.py       # preprocessar + preprocessar_adaptativo
    │   ├── segmentacao.py
    │   ├── extracao.py               # extrair_todos (imagens + estratégia)
    │   ├── classificador.py          # treinar() + treinar_vetores()
    │   ├── dados_tabulares.py        # CSV/TXT: schema, features, stats
    │   ├── avaliacao_modelos.py      # 6 modelos, 5-fold CV, ECE, McNemar
    │   ├── leitura_temporal.py       # Lê .dat/.edf/.mat/.xml/.c3d → SinalNormalizado
    │   ├── leitura_audio.py          # Lê .wav/.flac/.mp3 → SinalNormalizado
    │   ├── leitura_dicom.py          # Lê .dcm único ou série → SinalNormalizado
    │   ├── leitura_volumetrica.py    # Lê .nii/.nii.gz/.mha → SinalNormalizado
    │   ├── leitura_video.py          # Lê .mp4/.avi/.mov → SinalNormalizado
    │   ├── extracao_temporal.py      # Features F1: RMS, HRV, bandas EEG, FVC...
    │   ├── extracao_audio.py         # Features F2: MFCC, ZCR, centroide, bandas
    │   ├── extracao_dicom.py         # Features F3: 9 biomarcadores + DICOM-específicos
    │   ├── extracao_volumetrica.py   # Features F4: stats 3D, GLCM por plano, morfologia
    │   └── extracao_video.py         # Features F5: motion index, textura keyframe
    │
    ├── config/
    │   ├── agents.yaml               # 11 agentes
    │   └── tasks.yaml                # 11 tasks
    │
    ├── tools/                        # CrewAI BaseTool — wrappers sobre pipeline/
    │   ├── analise_base_tool.py      # FerramentaAnaliseBase
    │   ├── extracao_tool.py          # FerramentaExtrairBiomarcadores (lote)
    │   ├── treino_tool.py            # FerramentaTreinarClassificador
    │   ├── tabular_tool.py           # FerramentaAnaliseTabular
    │   ├── custom_tool.py            # FerramentaAnaliseImagem (single, legado)
    │   ├── sinais_temporais_tool.py  # FerramentaExtrairSinalTemporal
    │   ├── audio_biomedico_tool.py   # FerramentaExtrairAudio
    │   ├── dicom_tool.py             # FerramentaExtrairDICOM
    │   ├── volumetrico_tool.py       # FerramentaExtrairVolume3D
    │   └── video_medico_tool.py      # FerramentaExtrairVideo
    │
    ├── static/
    │   ├── uploads/                  # Arquivos enviados — não versionar
    │   └── runs/                     # Workspaces dos kickoffs — não versionar
    │
    └── templates/
        ├── tela1_upload.html         # Upload com drag & drop (10 modos)
        └── tela2_resultados.html     # 4 abas + Laudo Interativo
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

**Rota**: `GET /` e `POST /analisar`

Aceita três formas de entrada:
1. **Upload de arquivo** (drag & drop ou seletor): imagem, ZIP, CSV, EDF, DICOM, NIfTI, MP4
2. **Caminho manual** (texto): qualquer pasta ou arquivo no disco
3. **Vazio**: usa cache do KaggleHub (dataset BUSI)

- Arquivos vão para `src/biostatusia/static/uploads/`
- ZIPs são extraídos automaticamente
- `MAX_CONTENT_LENGTH = 4 GB`

---

## Tela 2 — Resultados (4 abas)

**Rota**: `GET /resultados/<int:resultado_id>`

| Aba | Conteúdo | Quando aparece |
|---|---|---|
| **Aba 1 — Pré-processamento** | Análise da base, estratégia adaptativa, justificativas | Modos com imagem |
| **Aba 2 — Estatísticas** | Tabela de biomarcadores, boxplot, schema tabular | Sempre |
| **Aba 3 — AutoML & Laudo** | Comparação 6 modelos, ROC, matriz confusão, laudo Markdown | Sempre; gráficos só se treinado |
| **Aba 4 — Laudo Interativo** | Seleção de ROI/trecho/frame → laudo IA focado | Sempre (conteúdo varia por família) |

### Aba 4 — Laudo Interativo (detalhe)

| Família | Interface de seleção |
|---|---|
| F1/F2 (sinal/áudio) | Plotly com `dragmode: 'select'` + dropdown de canal |
| F3 (DICOM 2D) | Canvas overlay com ROI retangular |
| F4 (Volume 3D) | Slider de slice (chama `GET /slice/<id>/<idx>`) + canvas ROI |
| F5 (Vídeo) | Slider de frame (chama `GET /frame/<id>/<idx>`) + range inputs |
| Default (imagem comum) | Canvas overlay com ROI retangular |

Rotas novas em `app.py`:
- `POST /laudo_interativo` — recebe JSON com seleção, dispara `BioStatusIACrewInterativo`, salva em `laudos_interativos`, retorna `{"laudo_html": ..., "laudo_id": ...}`
- `GET /slice/<resultado_id>/<idx>` — retorna slice axial de volume 3D como `{"imagem_b64": ..., "n_slices": ...}`
- `GET /frame/<resultado_id>/<idx>` — retorna frame de vídeo como `{"imagem_b64": ..., "frame_idx": ...}`

---

## AutoML — `pipeline/avaliacao_modelos.py`

### 6 modelos concorrentes

| Modelo | Parâmetros |
|---|---|
| `LogisticRegression` | `max_iter=1000` |
| `KNeighborsClassifier` | `n_neighbors=5` |
| `SVC` (RBF) | `probability=True` |
| `RandomForestClassifier` | `n_estimators=100, random_state=42` |
| `GradientBoostingClassifier` | `n_estimators=100, random_state=42` |
| `MLPClassifier` | `hidden_layer_sizes=(64,32), max_iter=500` |

### Métricas enriquecidas por fold

- `acuracia`, `sensibilidade` (recall positivo), `especificidade` (recall negativo)
- `precisao`, `recall`, `f1`, `auc`
- `ece` — Expected Calibration Error (10 bins)
- `latencia_inferencia_ms` — tempo médio por predição
- `tempo_treino_s` — tempo de treino

### Teste de McNemar (A/B)

- Compara os dois melhores modelos (maior AUC)
- Retorna: chi², p-value, `diferenca_significativa` (p < 0.05)

### Critério de seleção

Melhor modelo = maior AUC, com preferência por `sensibilidade ≥ 0.8` (minimiza falso-negativo em contexto clínico).

---

## Agentes CrewAI (v2) — 6 Crews, 11 agentes

### Crew 1: `BioStatusIACrew` — fluxo completo de imagem (original)

| Ordem | Agente | Tool | Output |
|---|---|---|---|
| 1 | `engenheiro_pdi` | `FerramentaAnaliseBase` | `analise_base.json` |
| 2 | `analista_tecnico` | `FerramentaExtrairBiomarcadores` | `biomarcadores.json` |
| 3 | `cientista_dados` | `FerramentaTreinarClassificador` | `metricas.json` |
| 4 | `radiologista_ia` | — | Laudo Markdown |

### Crew 2: `BioStatusIACrewTabular`

| Agente | Tool |
|---|---|
| `bioestatistico` | `FerramentaAnaliseTabular` |

### Crew 3: `BioStatusIACrewSinal` — F1 + F2

| Ordem | Agente | Tools |
|---|---|---|
| 1 | `analista_sinais_fisiologicos` | `FerramentaExtrairSinalTemporal` + `FerramentaExtrairAudio` |
| 2 | `radiologista_ia` | — |

### Crew 4: `BioStatusIACrewImagem3D` — F3 + F4

| Ordem | Agente | Tools |
|---|---|---|
| 1 | `especialista_imagem_medica` | `FerramentaExtrairDICOM` + `FerramentaExtrairVolume3D` |
| 2 | `radiologista_ia` | — |

### Crew 5: `BioStatusIACrewVideo` — F5

| Ordem | Agente | Tool |
|---|---|---|
| 1 | `analista_video_medico` | `FerramentaExtrairVideo` |
| 2 | `radiologista_ia` | — |

### Crew 6: `BioStatusIACrewInterativo` — Laudo Interativo

| Agente | Tools | Restrição |
|---|---|---|
| `radiologista_ia_interativo` | — (sem tools) | `max_iter=4`, sem tool calls |

Laudo interativo tem **5 seções obrigatórias**: Achado Principal, Severidade 1–5, Comparação com Referência, Recomendação Imediata, Aviso Ético.

### Comunicação entre agentes (via filesystem)

Cada execução cria `static/runs/run_<timestamp>/`. Tools persistem JSONs completos; retornam apenas resumo em texto ao LLM. O agente seguinte lê os JSONs do anterior.

---

## Banco de dados (v2)

### Tabela `analises` (inalterada)
```sql
id        INTEGER PRIMARY KEY AUTOINCREMENT
data_hora TEXT NOT NULL
imagem    TEXT NOT NULL
categoria TEXT NOT NULL   -- "BENIGNO" | "MALIGNO" | "INDEFINIDO" | "TABULAR" | "SINAL"
laudo     TEXT
```

### Tabela `resultados_pipeline` (migração v2 — novas colunas)
```sql
id            INTEGER PRIMARY KEY AUTOINCREMENT
data_hora     TEXT NOT NULL
dataset_path  TEXT
n_imagens     INTEGER
pipeline_json TEXT               -- payload completo para Tela 2
melhor_modelo TEXT
analise_id    INTEGER            -- FK → analises.id
familia_sinal TEXT               -- "F1" | "F2" | "F3" | "F4" | "F5" | ""
sinal_tipo    TEXT               -- "ECG" | "EEG" | "Raio-X" | ...
```

### Tabela `laudos_interativos` (nova v2)
```sql
id            INTEGER PRIMARY KEY AUTOINCREMENT
resultado_id  INTEGER            -- FK → resultados_pipeline.id
trecho_inicio REAL               -- segundos ou índice de início
trecho_fim    REAL               -- segundos ou índice de fim
roi_json      TEXT               -- JSON com x,y,w,h para ROI de imagem
canal         TEXT               -- canal selecionado (ECG lead, EEG canal...)
slice_idx     INTEGER            -- índice de slice para volumes 3D
laudo_foco    TEXT               -- laudo interativo gerado
data_hora     TEXT NOT NULL
```

Migração v2 é idempotente (`_migrar_v2()` usa `try/except OperationalError` para `ALTER TABLE`).

---

## Pipeline adaptativo de leitura e extração

### F1 — Sinais Temporais (`leitura_temporal.py` → `extracao_temporal.py`)

**Leitores:**
- `.dat/.hea` → `wfdb.rdrecord()`
- `.edf/.bdf` → `mne.io.read_raw_edf/bdf()`
- `.mat` → `scipy.io.loadmat()`
- `.xml` → ElementTree (Espirometria Schiller/Cosmed)
- `.c3d` → `bioread` (Movimento/PSG)

**Features extraídas:**
- Domínio do tempo: RMS, média, desvio, skewness, kurtosis, pico-a-pico, SNR_dB
- Domínio da frequência: PSD (Welch), centroide espectral, 4 bandas de potência, freq dominante
- ECG específico: R-peaks (scipy), FC_bpm, RMSSD, SDNN, pNN50
- EEG específico: bandas delta/theta/alpha/beta/gamma relativas, ratio alpha/beta
- EMG específico: RMS envelope, frequência mediana
- Espirometria: FVC, FEV1, FEV1/FVC, PEF

### F2 — Áudio Biomédico (`leitura_audio.py` → `extracao_audio.py`)

- MFCCs (20 coeficientes) + delta MFCCs
- Centroide espectral, bandwidth, rolloff, chroma (12), flatness, contraste espectral
- ZCR, RMS envelope, duração
- Bandas de energia: sub-20Hz, 20–200Hz, 200Hz–1kHz, 1–2kHz, 2k+Hz

### F3 — DICOM 2D (`leitura_dicom.py` → `extracao_dicom.py`)

- 9 biomarcadores originais (morfologia, textura GLCM, distribuição)
- DICOM-específicos: densidade alta (%), gradiente médio, uniformidade, modalidade, pixel_spacing, hounsfield_range
- Janelamento HU automático (WindowCenter/Width do header DICOM)
- SOPClassUID para identificar modalidade

### F4 — Volume 3D (`leitura_volumetrica.py` → `extracao_volumetrica.py`)

- nibabel para `.nii/.nii.gz` (transpõe X,Y,Z → Z,Y,X axial-first)
- SimpleITK para `.mha`
- Stats globais: média, desvio, mediana, skewness, kurtosis, P5/P95, n_voxels_altos
- GLCM por plano ortogonal (axial/coronal/sagital)
- Morfologia 3D: volume da lesão (mm³), esfericidade, axes do bounding box
- `slice_para_png_base64(volume, idx)` → base64 para a rota `/slice/`

### F5 — Vídeo Médico (`leitura_video.py` → `extracao_video.py`)

- OpenCV com amostragem adaptativa (até `max_frames=300`)
- Frames armazenados como `(n_frames, 256, 256)` float32 [0,1]
- Temporal: contagem de frames, FPS, brilho médio/desvio, variação temporal
- Movimento: motion index (diff de frames), frame de maior movimento, P90 motion, % frames alta variação
- Textura do keyframe (maior variância): GLCM, entropia, skewness, kurtosis
- `frame_para_png_base64(frame)` → base64 para a rota `/frame/`

---

## Biomarcadores — regra de interpretação (imagens)

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

## Datasets de validação (Kaggle)

| Família | Dataset | Slug no Kaggle | Formato |
|---|---|---|---|
| F1 — ECG | ECG Heartbeat Categorization | `shayanfazeli/heartbeat` | CSV (MIT-BIH) |
| F2 — Áudio | Respiratory Sound Database (ICBHI 2017) | `vbookshelf/respiratory-sound-database` | WAV + CSV |
| F3 — DICOM/Raio-X | Chest X-Ray Images (Pneumonia) | `paultimothymooney/chest-xray-pneumonia` | JPEG (NORMAL/PNEUMONIA) |
| F5 — Endoscopia | Kvasir Dataset v2 | `meliodas23/kvasir-v2` | JPEG (8 classes) |

Para volumes 3D (F4), datasets como BRATS são muito pesados para KaggleHub — usar download direto.

---

## Nomes de pastas reconhecidos como rótulo

```python
PASTAS_BENIGNAS = {"benign", "benigno", "normal", "negative", "0"}
PASTAS_MALIGNAS = {"malignant", "malign", "maligno", "abnormal", "positive", "1"}
```

Busca **recursiva** — funciona com estruturas aninhadas como `Dataset_BUSI_with_GT/benign/`.

---

## Detecção de coluna-rótulo em CSV/TXT

`pipeline/dados_tabulares.py::detectar_schema()` identifica:
1. Por nome: `label`, `class`, `diagnosis`, `target`, `outcome`, `y`, `categoria`, `resultado`
2. Se não achar por nome: última coluna com 2–10 valores únicos
3. Rótulos binários mapeados para 0/1 via `MALIGNANT_KEYWORDS`

Separador detectado automaticamente (`,`, `;`, `\t`, `|`). Encoding: UTF-8 com fallback Latin-1.

---

## Convenções de código

- **Português** para variáveis de domínio (`laudo`, `categoria`, `biomarcadores`, `solidez`). Inglês para infraestrutura (`conn`, `path`, `model`).
- **Sem comentários** que expliquem o "o quê" — só o "por quê" quando não óbvio.
- **Pipeline = funções puras**: cada etapa recebe e devolve dados, sem I/O.
- Toda I/O (DB, HTML, arquivos) concentrada em `app.py` e `database.py`.
- **Templates HTML são a fonte da verdade visual** — nunca editar HTML gerado em runtime.
- **Pydantic** para schemas de ferramentas CrewAI.

---

## Problema conhecido: encoding no Windows

CrewAI emite emojis nos logs do EventBus. Terminal com `charmap` (cp1252) gera `[EventBus Error]`. Cosméticos — não afetam execução.

```
PYTHONUTF8=1
PYTHONIOENCODING=utf-8
```

---

## O que NÃO fazer

- Não usar `pip install` — usar `uv add <pacote>`.
- Não commitar `.env`, `biostatusia.db`, `models/`, `src/biostatusia/static/uploads/`.
- Não editar HTMLs gerados em runtime.
- Não trocar `Process.sequential` por `Process.hierarchical` sem revisar `manager_llm`.
- Não aumentar `max_iter` sem medir tempo de resposta.
- Não adicionar ferramentas ao `radiologista_ia` nem ao `radiologista_ia_interativo`.
- Não restringir `detectar_estrutura()` — manter os 10 modos.
- Não treinar classificadores fora do contexto rotulado.
- Não reduzir `MAX_CONTENT_LENGTH` — volumes 3D precisam de 4 GB.
- Não quebrar a `SinalNormalizado` — é o contrato entre leitores e extratores.
- Não remover o Aviso Ético de nenhuma saída visual ou laudo.

---

## Aviso ético obrigatório

Este sistema é uma **ferramenta de suporte à decisão clínica**. Nenhuma mudança de código deve remover o aviso de que os laudos **não substituem a avaliação de um médico habilitado**. Esse aviso é obrigatório em:
- Toda saída visual (Tela 2)
- Todo laudo do `radiologista_ia`
- Todo laudo do `radiologista_ia_interativo` (5ª seção obrigatória)
- Todo laudo do `bioestatistico`
