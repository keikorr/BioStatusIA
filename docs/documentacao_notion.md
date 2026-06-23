# 📖 Dossiê de Documentação: BioStatusIA v2

> **Sistema de Apoio à Decisão Clínica (CDSS)** para análise automatizada de **18 tipos de sinais biomédicos** em 5 famílias, com IA Multi-Agente local (CrewAI + Ollama), AutoML de 6 modelos e Laudo Interativo por seleção de ROI/trecho.

Projeto acadêmico de mestrado em IA na Saúde — Fortaleza, CE.

---

## 🎯 1. Objetivos do Projeto (v2)

O **BioStatusIA v2** expande o CDSS original (focado em ultrassom mamário) para uma plataforma **universal de análise biomédica**. Seus princípios fundamentais são:

1. **Aceitar qualquer tipo de dado biomédico** — imagem, sinal temporal, áudio, DICOM, volume 3D ou vídeo médico
2. **Auto-detecção do tipo de entrada** — 10 modos identificados automaticamente
3. **Pipeline agentificado especializado por família** — 6 crews, 11 agentes, 10 tools
4. **AutoML rigoroso** — 6 modelos, 5-fold CV, métricas clínicas enriquecidas, teste de McNemar
5. **Laudo Interativo** — o médico seleciona um trecho/ROI e recebe laudo focado exclusivamente naquele recorte

---

## 🛠️ 2. Requisitos do Sistema (v2)

### Requisitos Funcionais (RF)

*   **RF-01 (Detecção Universal):** Reconhecer e rotear automaticamente 10 modos de dados em 5 famílias de sinais biomédicos.
*   **RF-02 (SinalNormalizado):** Toda leitura de sinal deve produzir um `SinalNormalizado` — dataclass unificada com família, tipo, dados, taxa de amostragem, canais, metadados e dados de visualização (≤2000 pontos para Plotly).
*   **RF-03 (Análise Estatística Cega):** Calcular métricas sobre os dados brutos antes de qualquer limpeza, para evitar viés de seleção.
*   **RF-04 (Pré-Processamento Adaptativo):** Pipeline determinístico de decisão baseado em estatísticas detectadas (ruído, contraste, outliers, tamanho).
*   **RF-05 (AutoML Enriquecido):** 6 classificadores concorrentes, 5-fold StratifiedKFold, ECE, latência de inferência, teste de McNemar, seleção por AUC com preferência por sensibilidade ≥ 0.80.
*   **RF-06 (Laudo IA Especializado):** Cada família de sinal tem agente e task específicos — `radiologista_ia` interpreta achados considerando o contexto clínico do tipo de sinal.
*   **RF-07 (Laudo Interativo):** Endpoint `POST /laudo_interativo` recebe seleção (ROI / trecho temporal / frame) e retorna laudo focado com 5 seções obrigatórias.
*   **RF-08 (Interface em 4 Abas):** Pré-processamento, Estatísticas, AutoML/Laudo, Laudo Interativo.

### Requisitos Não-Funcionais (RNF)

*   **RNF-01 (Privacidade Total):** Processamento 100% local — nenhum dado de saúde enviado para APIs externas.
*   **RNF-02 (LLM Local):** `qwen2.5:3b` via Ollama — sem dependência de conectividade.
*   **RNF-03 (Capacidade para Volumes 3D):** `MAX_CONTENT_LENGTH = 4 GB` para suportar TC e RM completos.
*   **RNF-04 (Idempotência do Banco):** Migração v2 via `ALTER TABLE` com `try/except` — segura em re-execuções.
*   **RNF-05 (Retrocompatibilidade):** Pipeline CLI (`main.py`) e crews originais de ultrassom mantidos intactos.

---

## 🧬 3. As 5 Famílias de Sinal

### Família F1 — Sinais Temporais Fisiológicos

| Tipo | Biblioteca | Features Diagnósticas |
|---|---|---|
| ECG | `wfdb`, `mne` | FC_bpm, RMSSD, SDNN, pNN50, R-peaks |
| EEG | `mne` | Bandas δ/θ/α/β/γ, ratio α/β |
| EMG | `mne` | RMS envelope, frequência mediana |
| EOG / PPG / PA | `mne`, `scipy` | RMS, PSD, centroide espectral |
| Espirometria | ElementTree (XML) | FVC, FEV1, FEV1/FVC, PEF |
| PSG / Movimento | `bioread`, `scipy` | RMS, PSD, bandas de potência |

**Formatos:** `.dat/.hea` (WFDB), `.edf/.bdf` (EDF+/BDF), `.mat` (Matlab), `.xml` (Schiller/Cosmed), `.c3d` (Movimento)

### Família F2 — Áudio Biomédico

| Tipo | Padrões Clínicos |
|---|---|
| Fonocardiograma | Sopros S1/S2, Split, Clique |
| Sons Pulmonares | Crepitações, Sibilos, Normal (ICBHI 2017) |

**Features:** MFCCs (20 + delta), centroide espectral, bandwidth, rolloff, chroma (12), flatness, ZCR, energia por banda (sub-20Hz / 20–200Hz / 200Hz–1kHz / 1–2kHz / 2k+Hz)

**Formatos:** `.wav`, `.flac`, `.mp3`

### Família F3 — Imagem DICOM 2D

| Modalidade | SOPClassUID detectado | Interpretação Clínica |
|---|---|---|
| Raio-X de Tórax | `1.2.840.10008.5.1.4.1.1.1.1` | Consolidações, derrames, pneumotórax |
| Mamografia | `1.2.840.10008.5.1.4.1.1.1.2` | Densidades BI-RADS, microcalcificações |
| Ultrassom | `1.2.840.10008.5.1.4.1.1.6` | Ecogenicidade, sombreamento |

**Processamento:** Janelamento Hounsfield automático via `WindowCenter/Width`, Rescale Slope/Intercept, 9 biomarcadores radiômicos + DICOM-específicos

**Formato:** `.dcm` (arquivo único)

### Família F4 — Volumes 3D

| Formato | Biblioteca | Convenção de Eixos |
|---|---|---|
| `.nii` / `.nii.gz` | nibabel | Transpõe (X,Y,Z) → (Z,Y,X) axial-first |
| `.mha` | SimpleITK | Lido diretamente (Z,Y,X) |
| Série DICOM (≥10 `.dcm`) | pydicom | Ordenada por InstanceNumber, empilhada (D,H,W) |

**Features 3D:** stats globais (média/desvio/P5/P95/voxels_altos), GLCM por plano ortogonal (axial/coronal/sagital), morfologia 3D (volume em mm³, esfericidade, bounding box axes)

**Rota especial:** `GET /slice/<resultado_id>/<idx>` → base64 PNG do slice axial para slider interativo

### Família F5 — Vídeo Médico

| Modalidade | Features Diagnósticas |
|---|---|
| Endoscopia | Variação de cor/textura, detecção de pólipos |
| Ecocardiografia | Motion index de parede cardíaca |
| Ultrassom dinâmico | Movimento de estruturas |

**Processamento:** OpenCV, amostragem adaptativa (até 300 frames), (n_frames, 256, 256) float32 [0,1]

**Features:** contagem/FPS, brilho médio/desvio, variação temporal, motion index, frame de maior movimento, P90 motion, % frames alta variação, textura do keyframe (GLCM, entropia, skewness, kurtosis)

**Rota especial:** `GET /frame/<resultado_id>/<idx>` → base64 PNG do frame para slider interativo

---

## 🤖 4. Arquitetura Multi-Agente (v2)

### 6 Crews CrewAI

```
Crew 1 — BioStatusIACrew (Imagem Ultrassom Original)
  ├── engenheiro_pdi         [FerramentaAnaliseBase]          → analise_base.json
  ├── analista_tecnico       [FerramentaExtrairBiomarcadores] → biomarcadores.json
  ├── cientista_dados        [FerramentaTreinarClassificador] → metricas.json
  └── radiologista_ia        [sem tool]                       → Laudo Markdown

Crew 2 — BioStatusIACrewTabular (CSV/TXT)
  └── bioestatistico         [FerramentaAnaliseTabular]       → Laudo Markdown

Crew 3 — BioStatusIACrewSinal (F1 + F2)
  ├── analista_sinais_fisiologicos
  │     ├── [FerramentaExtrairSinalTemporal]  → biomarcadores_temporal.json
  │     └── [FerramentaExtrairAudio]          → biomarcadores_audio.json
  └── radiologista_ia        [sem tool]        → Laudo Markdown

Crew 4 — BioStatusIACrewImagem3D (F3 + F4)
  ├── especialista_imagem_medica
  │     ├── [FerramentaExtrairDICOM]          → biomarcadores_dicom.json
  │     └── [FerramentaExtrairVolume3D]       → biomarcadores_volumetrico.json
  └── radiologista_ia        [sem tool]        → Laudo Markdown

Crew 5 — BioStatusIACrewVideo (F5)
  ├── analista_video_medico  [FerramentaExtrairVideo]         → biomarcadores_video.json
  └── radiologista_ia        [sem tool]                       → Laudo Markdown

Crew 6 — BioStatusIACrewInterativo (Laudo Focado)
  └── radiologista_ia_interativo [sem tool, max_iter=4]       → Laudo Interativo Markdown
```

### 11 Agentes (`config/agents.yaml`)

| Agente | Função | Crews |
|---|---|---|
| `engenheiro_pdi` | PDI + estratégia adaptativa | Crew 1 |
| `analista_tecnico` | Extração radiômica em lote | Crew 1 |
| `cientista_dados` | AutoML + seleção de modelo | Crew 1 |
| `radiologista_ia` | Laudo clínico geral | Crews 1, 3, 4, 5 |
| `bioestatistico` | Análise e laudo tabular | Crew 2 |
| `analista_sinais_fisiologicos` | Features F1/F2 | Crew 3 |
| `analista_audio_biomedico` | Features acústicas F2 | Crew 3 |
| `especialista_imagem_medica` | Features DICOM F3/F4 | Crew 4 |
| `analista_video_medico` | Features de vídeo F5 | Crew 5 |
| `radiologista_ia_interativo` | Laudo focado em seleção | Crew 6 |

### 10 Tools CrewAI (`tools/`)

| Tool | Wrapper | Output |
|---|---|---|
| `FerramentaAnaliseBase` | `analise_base.py` | `analise_base.json` |
| `FerramentaExtrairBiomarcadores` | `extracao.py` (lote) | `biomarcadores.json` |
| `FerramentaTreinarClassificador` | `classificador.py` | `metricas.json` |
| `FerramentaAnaliseTabular` | `dados_tabulares.py` | resumo texto |
| `FerramentaAnaliseImagem` | `extracao.py` (single, legado) | resumo texto |
| `FerramentaExtrairSinalTemporal` | `extracao_temporal.py` | `biomarcadores_temporal.json` |
| `FerramentaExtrairAudio` | `extracao_audio.py` | `biomarcadores_audio.json` |
| `FerramentaExtrairDICOM` | `extracao_dicom.py` | `biomarcadores_dicom.json` |
| `FerramentaExtrairVolume3D` | `extracao_volumetrica.py` | `biomarcadores_volumetrico.json` |
| `FerramentaExtrairVideo` | `extracao_video.py` | `biomarcadores_video.json` |

### Protocolo de comunicação via filesystem

```
static/runs/run_<timestamp>/
├── analise_base.json          ← escrito pelo engenheiro_pdi
├── biomarcadores.json         ← escrito pelo analista_tecnico
├── metricas.json              ← escrito pelo cientista_dados
├── biomarcadores_temporal.json ← escrito por analista_sinais_fisiologicos
├── biomarcadores_audio.json   ← escrito por analista_sinais_fisiologicos
├── biomarcadores_dicom.json   ← escrito por especialista_imagem_medica
├── biomarcadores_volumetrico.json ← escrito por especialista_imagem_medica
└── biomarcadores_video.json   ← escrito por analista_video_medico
```

Cada tool persiste o JSON completo → retorna resumo em texto ao LLM → próximo agente lê o JSON. O LLM nunca ingere megabytes de dados numéricos.

---

## 📊 5. AutoML Enriquecido (`pipeline/avaliacao_modelos.py`)

### 6 Modelos Concorrentes

| # | Modelo | Tipo | Justificativa Clínica |
|---|---|---|---|
| 1 | Regressão Logística | Linear | Baseline interpretável, coeficientes = importância de features |
| 2 | KNN (k=5) | Distância | Robusto em distribuições multimodais |
| 3 | SVM RBF | Kernel | Estado da arte em alta dimensão com poucas amostras |
| 4 | Random Forest (100) | Ensemble | Alta estabilidade, importância de features |
| 5 | Gradient Boosting (100) | Boosting | Melhor AUC em dados tabulares médicos |
| 6 | MLP (64×32) | Rede Neural | Mapeamento de padrões não-lineares complexos |

### Protocolo de Avaliação

```
Dataset com rótulos e ≥10 amostras
  ├── StandardScaler (fit apenas no treino)
  ├── 5-fold StratifiedKFold (random_state=42)
  │     Para cada fold × cada modelo:
  │       - treino + inferência cronometrados
  │       - predict_proba → AUC, ECE
  │       - classification_report → sensibilidade, especificidade, F1
  └── Holdout 20% (test set)
        - ROC curve (FPR, TPR)
        - confusion_matrix
        - McNemar test (top-2 modelos)
```

### Métricas Clínicas (além das padrão)

| Métrica | Fórmula | Relevância Clínica |
|---|---|---|
| **Sensibilidade** | TP / (TP + FN) | Minimiza falso-negativo — detectar malignidade |
| **Especificidade** | TN / (TN + FP) | Minimiza falso-positivo — reduz biópsias desnecessárias |
| **ECE** | Calibration error (10 bins) | Confiança do modelo = probabilidade real |
| **Latência (ms)** | tempo/amostra | Viabilidade clínica em tempo real |
| **McNemar** | χ² + p-value | Diferença estatisticamente significativa entre modelos |

### Critério de Seleção do Vencedor

```python
# Prefere modelo com sensibilidade >= 0.80
candidatos = [m for m in modelos if m["sensibilidade"] >= 0.80]
if candidatos:
    vencedor = max(candidatos, key=lambda m: m["auc"])
else:
    vencedor = max(modelos, key=lambda m: m["auc"])
```

---

## 🎨 6. Interface Web — 4 Abas (Tela 2)

### Aba 1 — Pré-processamento

Cards explicativos com decisão + justificativa para cada etapa:
- Denoising escolhido (Non-Local Means vs Gaussian) com ruído detectado
- Normalização escolhida (Percentil 1–99% vs Min-Max) com % de outliers
- Equalização (CLAHE vs nenhuma) com contraste detectado
- Resize (obrigatório vs não necessário) com tamanhos detectados
- Shapiro-Wilk: distribuição normal vs não-normal

### Aba 2 — Estatísticas

- Tabela de biomarcadores (média ± desvio por categoria)
- Boxplot de distribuição por biomarcador (Plotly.js)
- Schema tabular (colunas, tipos, missing values) para modos CSV
- 31 métricas univariadas por feature (sidebar interativa)
- Heatmap de correlação (CSS inline, sem dependência extra)

### Aba 3 — AutoML & Laudo

- Pódio dos 6 modelos com AUC, sensibilidade, especificidade
- Gráfico comparativo de métricas (Plotly.js barras agrupadas)
- Curva ROC (Plotly.js)
- Matriz de Confusão (Plotly.js heatmap)
- Resultado do teste de McNemar
- Laudo clínico em Markdown (tipografia médica elegante)
- Histórico de análises do SQLite (tabela scrollável)

### Aba 4 — Laudo Interativo

Interface diferente por família:

```
F1/F2 — Sinais Temporais / Áudio
  ├── Plotly com dragmode: 'select' — brush selection
  ├── Dropdown de canal (ex: lead II, EEG Fz, etc.)
  ├── Display do trecho selecionado (t_início → t_fim em segundos)
  └── Botão "Analisar Trecho" → POST /laudo_interativo

F3 — DICOM 2D
  ├── <canvas> sobre imagem DICOM renderizada
  ├── Desenho de ROI retangular (mousedown/mousemove/mouseup)
  ├── Display das coordenadas da ROI
  └── Botão "Analisar ROI" → POST /laudo_interativo

F4 — Volume 3D
  ├── Slider de slice axial (GET /slice/<id>/<idx>)
  ├── <canvas> sobre o slice atual para ROI
  └── Botão "Analisar ROI no Slice" → POST /laudo_interativo

F5 — Vídeo Médico
  ├── Slider de frame (GET /frame/<id>/<idx>)
  ├── Range inputs (frame início → frame fim)
  └── Botão "Analisar Trecho de Vídeo" → POST /laudo_interativo
```

**Laudo Interativo — 5 seções obrigatórias:**
1. **Achado Principal** — o que chama atenção neste trecho/região
2. **Severidade Estimada** — escala 1 (normal) a 5 (crítico) com justificativa
3. **Comparação com Referência** — valores normais esperados vs achado
4. **Recomendação Imediata** — próximo passo clínico sugerido
5. **Aviso Ético** — este laudo é de suporte e NÃO substitui avaliação médica

---

## 💾 7. Banco de Dados SQLite (3 tabelas)

### `analises`
```sql
CREATE TABLE analises (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    data_hora TEXT NOT NULL,
    imagem    TEXT NOT NULL,
    categoria TEXT NOT NULL,  -- BENIGNO | MALIGNO | INDEFINIDO | TABULAR | SINAL
    laudo     TEXT
);
```

### `resultados_pipeline` (expandida na migração v2)
```sql
CREATE TABLE resultados_pipeline (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    data_hora     TEXT NOT NULL,
    dataset_path  TEXT,
    n_imagens     INTEGER,
    pipeline_json TEXT,           -- payload completo para Tela 2
    melhor_modelo TEXT,
    analise_id    INTEGER REFERENCES analises(id),
    familia_sinal TEXT,           -- F1 | F2 | F3 | F4 | F5  [novo v2]
    sinal_tipo    TEXT            -- ECG | Raio-X | ...        [novo v2]
);
```

### `laudos_interativos` (nova em v2)
```sql
CREATE TABLE laudos_interativos (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    resultado_id  INTEGER REFERENCES resultados_pipeline(id),
    trecho_inicio REAL,
    trecho_fim    REAL,
    roi_json      TEXT,
    canal         TEXT,
    slice_idx     INTEGER,
    laudo_foco    TEXT,
    data_hora     TEXT NOT NULL
);
```

**Migração v2** (`database.py::_migrar_v2()`): usa `try/except OperationalError` para `ALTER TABLE` — idempotente em re-execuções.

---

## 🌐 8. API Flask — Rotas (v2)

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/` | Tela 1 — Upload |
| `POST` | `/analisar` | Dispara pipeline completo → redireciona para `/resultados/<id>` |
| `GET` | `/resultados/<id>` | Tela 2 — Exibe resultado do pipeline |
| `POST` | `/laudo_interativo` | **[novo v2]** Recebe seleção JSON → retorna laudo focado |
| `GET` | `/slice/<id>/<idx>` | **[novo v2]** Retorna slice axial de volume 3D como base64 |
| `GET` | `/frame/<id>/<idx>` | **[novo v2]** Retorna frame de vídeo como base64 |

### Payload de `/laudo_interativo` (POST)

```json
{
    "resultado_id": 42,
    "tipo": "sinal_temporal",
    "canal": "II",
    "trecho_inicio": 12.5,
    "trecho_fim": 15.0,
    "roi": null,
    "slice_idx": null,
    "frame_inicio": null,
    "frame_fim": null
}
```

Resposta:
```json
{
    "laudo_html": "<h2>Achado Principal</h2>...",
    "laudo_id": 7
}
```

---

## 📦 9. Stack Tecnológica Completa (v2)

| Camada | Tecnologia | Versão |
|---|---|---|
| Python | 3.11 | `>=3.10,<3.13` |
| Gerenciador | `uv` | — |
| LLM | Ollama `qwen2.5:3b` | local |
| Agentes | CrewAI | `>=0.203.1,<1.0.0` |
| Servidor Web | Flask | `>=3.0.0` |
| Banco | SQLite (built-in) | 3 tabelas |
| Sinais F1 | MNE-Python, wfdb | — |
| Áudio F2 | librosa, soundfile | — |
| DICOM F3 | pydicom | — |
| Volumes F4 | nibabel, SimpleITK | — |
| Visão | OpenCV, scikit-image | — |
| AutoML | scikit-learn | `>=1.3.0` |
| Gráficos | Plotly.js | 2.32 (CDN) |
| Frontend | Tailwind CSS | latest (CDN) |
| Capacidade Upload | — | 4 GB (`MAX_CONTENT_LENGTH`) |

---

## 🗃️ 10. Datasets de Validação (Kaggle)

| Família | Dataset | Kaggle Slug | Formato | Classes | Tamanho |
|---|---|---|---|---|---|
| **F1 — ECG** | ECG Heartbeat Categorization (MIT-BIH) | `shayanfazeli/heartbeat` | CSV | 5 arritmias | 109K amostras |
| **F2 — Áudio** | Respiratory Sound Database (ICBHI 2017) | `vbookshelf/respiratory-sound-database` | WAV + CSV | Normal/Crackle/Wheeze/Both | 920 gravações |
| **F3 — Raio-X** | Chest X-Ray Images (Pneumonia) | `paultimothymooney/chest-xray-pneumonia` | JPEG | NORMAL / PNEUMONIA | 5.8K imagens |
| **F5 — Endoscopia** | Kvasir Dataset v2 | `meliodas23/kvasir-v2` | JPEG | 8 classes (pólipos, etc.) | 8K imagens |

**Nota F4 (Volumes 3D):** Datasets de TC/RM (ex: BRATS, LUNA16) são muito pesados para KaggleHub — usar download direto via site oficial ou `kaggle datasets download` na CLI.

**Estrutura esperada para validação com o pipeline:**
```
dataset_ecg/
├── normal/          ← CSV com rótulo 0
└── abnormal/        ← CSV com rótulo 1

dataset_sons_pulmonares/
├── normal/          ← WAV de sons normais
└── abnormal/        ← WAV de crepitações/sibilos

dataset_raio_x/
├── NORMAL/          ← automaticamente reconhecido como "normal"
└── PNEUMONIA/       ← mapeado para malignant_keywords → rótulo 1
```

---

## 🔄 11. Fluxo Completo v2 (Diagrama)

```
ENTRADA (qualquer)
      │
      ▼
detectar_estrutura()   ←── app.py
      │
      ├── imagem_unica / imagens_soltas / dataset_rotulado / multimodal
      │         └──► BioStatusIACrew (4 agentes)
      │               engenheiro_pdi → analista_tecnico → cientista_dados → radiologista_ia
      │
      ├── tabular (CSV/TXT)
      │         └──► BioStatusIACrewTabular (1 agente)
      │               bioestatistico → laudo tabular
      │
      ├── sinal_temporal / audio_biomedico (F1/F2)
      │         └──► BioStatusIACrewSinal (2 agentes)
      │               analista_sinais_fisiologicos → radiologista_ia
      │
      ├── imagem_dicom_2d / volume_3d (F3/F4)
      │         └──► BioStatusIACrewImagem3D (2 agentes)
      │               especialista_imagem_medica → radiologista_ia
      │
      └── video_medico (F5)
                └──► BioStatusIACrewVideo (2 agentes)
                      analista_video_medico → radiologista_ia
      │
      ▼
avaliacao_modelos.py    ←── se há rótulos + ≥10 amostras
      │   6 modelos × 5-fold CV
      │   ECE + McNemar + latência
      ▼
database.py::salvar_resultado()
      │   analises + resultados_pipeline (familia_sinal, sinal_tipo)
      ▼
Tela 2 — 4 Abas
      │
      └── Aba 4: Médico seleciona ROI/trecho
                  │
                  └──► POST /laudo_interativo
                              └──► BioStatusIACrewInterativo
                                    radiologista_ia_interativo
                                    → 5 seções + aviso ético
                                    → laudos_interativos (DB)
```

---

## ⚠️ 12. Trade-offs e Limitações Conhecidas

| Aspecto | Limitação | Mitigação |
|---|---|---|
| Tempo de pipeline | 4–6 agentes × ~30s LLM = 3–8 min | Pipeline assíncrono no roadmap |
| Non-Local Means | ~10× mais lento que Gaussian | Apenas ativado com ruído > 0.05 |
| Volumes 3D | Carregamento completo em RAM | `MAX_CONTENT_LENGTH = 4 GB` |
| Encoding Windows | CrewAI EventBus emite emojis → `[EventBus Error]` no terminal | `.env` com `PYTHONUTF8=1` |
| MNE no Windows | Alguns formatos EEG precisam de driver USB-HID | Usar `.edf` exportado |
| F4 Kaggle | Datasets de TC são muito grandes para KaggleHub | Download direto |

---

## 🔧 13. Configuração do Ambiente

### `.env` completo

```env
MODEL=ollama/qwen2.5:3b
API_BASE=http://localhost:11434
PYTHONUTF8=1
PYTHONIOENCODING=utf-8
```

### Dependências principais (`pyproject.toml`)

```
crewai>=0.203.1,<1.0.0
flask>=3.0.0
scikit-learn>=1.3.0
opencv-python
scikit-image
mne
wfdb
pydicom
nibabel
SimpleITK
librosa
soundfile
python-dotenv
```

### Como rodar

```bash
# Instalar dependências
uv sync

# Iniciar servidor
uv run flask --app src/biostatusia/app.py run --port 5000

# Ou usar o CLI retrocompatível
uv run biostatsia
```

---

## 🔒 14. Aviso Ético Obrigatório

> **Este sistema é uma ferramenta de suporte à decisão clínica (CDSS). Os laudos gerados pelos agentes de IA são preliminares e baseados em análise computacional automática. Eles NÃO substituem, em nenhuma circunstância, a avaliação clínica de um médico habilitado. Todo resultado deve ser interpretado por um profissional de saúde qualificado antes de qualquer decisão diagnóstica ou terapêutica.**

Este aviso é **obrigatório** em:
- Toda saída visual da Tela 2
- Todo laudo do `radiologista_ia` (task: `tarefa_laudo`, `tarefa_laudo_sinal`)
- 5ª seção do `radiologista_ia_interativo` (task: `tarefa_laudo_interativo`)
- Todo laudo do `bioestatistico` (task: `tarefa_laudo_tabular`)

---

## 📝 15. Histórico de Versões

| Versão | Data | Principais Mudanças |
|---|---|---|
| v1.0 | 2025-12 | CDSS original: ultrassom mamário, 5 modos, 2 crews, 5 agentes, 5 tools |
| v1.5 | 2026-01 | AutoML 6 modelos, interface em abas premium, sidebar interativa de estatísticas |
| **v2.0** | **2026-06** | **5 famílias de sinal, 10 modos, 6 crews, 11 agentes, 10 tools, Laudo Interativo, avaliação enriquecida (ECE/McNemar/sensibilidade/especificidade), 3 tabelas SQLite** |
