# Prompt mestre para o Stitch — BioStatusIA

> Como usar: cole o bloco abaixo (tudo dentro de "PROMPT PARA O STITCH") no Stitch, em modo
> **Web / Desktop**. Se o Stitch cortar por tamanho, gere primeiro pela seção "DESIGN SYSTEM"
> + "TELA 1" e depois peça cada tela seguinte referenciando o mesmo design system.

---

## PROMPT PARA O STITCH

Crie o design de uma aplicação **web desktop** chamada **BioStatusIA**, um Sistema de Apoio à
Decisão Clínica (CDSS) que analisa sinais e imagens biomédicas com IA. Público: médicos e
pesquisadores. Idioma da interface: **português do Brasil**. Tom: software clínico
profissional, confiável e científico. Gere as telas em resolução de desktop largo (1440px),
com layouts amplos, tabelas e gráficos lado a lado.

### DESIGN SYSTEM (aplicar a todas as telas)

- **Estilo geral:** "clínico moderno" — base clara, cartões brancos com cantos bem
  arredondados (border-radius 16px), sombras suaves, muito respiro. Nada de gradientes
  pesados.
- **Cores:**
  - Fundo da página: cinza muito claro (#F5F8FA).
  - Cartões: branco (#FFFFFF), borda sutil (#E2E8F0).
  - Cor primária: azul-petróleo/teal (#0F766E) para botões, links, abas ativas e cabeçalhos.
  - Teal escuro (#115E59) para a barra de topo.
  - Texto: cinza-ardósia escuro (#1E293B) para títulos, (#475569) para corpo.
  - **Badges de categoria clínica:** BENIGNO = verde (#16A34A), MALIGNO = vermelho (#DC2626),
    INDEFINIDO = cinza (#64748B). Sempre em formato de pílula.
  - Acentos de status: sucesso verde, alerta âmbar (#D97706), erro vermelho.
- **Tipografia:** fonte sans-serif limpa (Inter). Títulos em semibold, corpo regular,
  números de métricas em destaque (tabular-nums).
- **Componentes recorrentes:** barra de topo fixa com logo "🧬 BioStatusIA" à esquerda e
  navegação/histórico à direita; cartões de conteúdo; abas horizontais; tabelas de dados com
  cabeçalho fixo e linhas zebradas; gráficos (boxplot, curva ROC, matriz de confusão, radar,
  barras de importância) no estilo Plotly limpo; botão primário teal preenchido e botão
  secundário contornado.
- **Banner ético obrigatório:** em todas as telas de resultado/laudo, uma faixa discreta cor
  âmbar-claro com ícone de aviso e o texto: *"Este relatório é gerado por IA para suporte à
  decisão clínica e não substitui a avaliação de um médico habilitado."*

---

### TELA 1 — Upload e Detecção Automática de Tipo

Tela inicial de envio de dados. Estrutura vertical centralizada, largura máx. ~900px:

- Barra de topo com o logo e, à direita, um link "Histórico de análises".
- Título grande: **"Envie seus dados biomédicos"** e subtítulo: *"O sistema detecta
  automaticamente o tipo de exame e adapta a análise."*
- **Zona de drag & drop** grande e central (borda tracejada teal, ícone de upload), com texto
  "Arraste um arquivo, ZIP ou pasta aqui — ou clique para selecionar".
- Abaixo, um campo de texto opcional "Caminho local da pasta" com botão "Usar caminho".
- Um seletor opcional "Tipo de sinal (para séries temporais)" com opções: Auto, ECG, EEG,
  EMG, EOG, PPG, PA, Espirometria.
- Um link discreto "Ou usar dataset de exemplo (KaggleHub)" com um campo opcional "ID Kaggle".
- **Faixa de tipos suportados:** uma linha de cartõezinhos/badges com ícone e rótulo,
  mostrando o que é aceito:
  - Imagem (PNG/JPG/TIF)
  - Tabular (CSV/TXT/TSV)
  - F1 — Sinais Temporais (EDF/MAT/DAT/HEA)
  - F3 — DICOM 2D (Raio-X, Mamografia, Ultrassom)
  - F4 — Volume 3D (TC, RM, PET — NII/MHA)
  - Multimodal (imagem + tabular)
- Botão primário grande **"Analisar"** ao final.
- Rodapé com o banner ético e a nota "Projeto de mestrado — IA na Saúde · Fortaleza/CE".

---

### TELA 2 — Resultados da Análise (com 4 abas)

Tela principal de resultados. Layout de largura total. No topo, abaixo da barra de navegação,
um **cabeçalho de contexto** em cartão: nome/caminho do dataset, badges de "Família" (F1/F3/F4
/Tabular), "Modo" e "Nº de amostras", e um destaque "Melhor modelo: RandomForest" quando
houver. Logo abaixo, uma **barra de 4 abas horizontais** (a ativa em teal com sublinhado):

**Aba 1 — Estatísticas & Biomarcadores** (ativa por padrão)
- Cartão "Biomarcadores por amostra": tabela com colunas como Circularidade, Solidez,
  Entropia, Homogeneidade, Energia, Contraste, SNR, Assimetria, Curtose (e categoria em badge
  colorida por linha).
- Cartão "Distribuição por classe": um **boxplot** comparando BENIGNO vs MALIGNO para uma
  métrica selecionável (dropdown).
- Cartão "Schema tabular" (quando dado tabular): coluna-rótulo detectada, nº de features, nº
  de amostras.
- Cartão "Métricas univariadas e correlações": tabela de média/mediana/desvio/min/max e uma
  mini-lista de correlações fortes (|r| ≥ 0.7).

**Aba 2 — Pré-processamento & Engenharia de Features**
- Cartão "Análise da base": estatísticas detectadas (intensidade, ruído, contraste, outliers).
- Cartão "Estratégia adaptativa escolhida": lista de decisões (denoising, normalização,
  equalização, redimensionamento / filtragem de sinal) cada uma com uma justificativa curta
  em texto.
- Cartão "Engenharia de features": **gráfico de barras horizontais** com o ranking de
  importância das features + o método usado (ANOVA/variância). Incluir um **estado vazio**
  elegante ("Nenhuma feature derivada disponível") para quando não houver.

**Aba 3 — AutoML (comparação de modelos)**
- Cartão "Pódio dos modelos": **tabela ranqueada** dos 6 classificadores (LogisticRegression,
  KNN, SVM, RandomForest, GradientBoosting, MLP) com colunas AUC, Sensibilidade,
  Especificidade, F1, MCC, Kappa; o campeão marcado com um troféu 🏆 e destaque teal.
- Cartão "Curva ROC": gráfico de curvas ROC sobrepostas dos modelos.
- Cartão "Matriz de confusão": heatmap 2×2 do modelo campeão.
- Cartão "Radar comparativo": gráfico radar comparando os modelos nas métricas-chave.
- Cartão "Teste A/B (McNemar)": um pequeno painel mostrando os dois melhores modelos, χ²,
  p-valor e um selo "Diferença significativa: Sim/Não".
- Esta aba é **só quantitativa** — sem texto de laudo.

**Aba 4 — Laudo**
- Cartão "Dossiê do Radiologista IA": bloco de texto formatado (laudo em markdown renderizado)
  com um botão "Imprimir" no canto e o banner ético ao final.
- Cartão "Histórico do Prontuário": tabela dos registros anteriores (data, imagem/arquivo,
  categoria em badge).
- **Seção A — Laudo de Amostra:** cartão com duas opções em abas internas: (1) "Enviar
  arquivo avulso" com uma mini zona de upload; (2) "Selecionar de uma análise anterior" com um
  dropdown de resultados e um dropdown de exemplar. Botão "Gerar laudo focado". Abaixo, uma
  área de resultado que exibe o laudo com **5 seções**: Achado Principal, Severidade (com um
  medidor/escala 1 a 5), Comparação com Referência, Recomendação Imediata e Aviso Ético.
- **Seção B — Laudo Populacional:** cartão com botão "Gerar laudo populacional" e uma área que
  mostra distribuição de classes, o pódio do AutoML em tabela, correlações fortes e as top
  features (SHAP). Deixar claro que é um relatório determinístico do dataset inteiro.

---

### TELA 3 (opcional) — Histórico de Análises

Uma tela de listagem acessível pelo link "Histórico" da barra de topo: tabela dos últimos
resultados (ID, data, dataset, nº de amostras, família, melhor modelo, categoria em badge),
com busca no topo e cada linha clicável para abrir a Tela 2 correspondente.

---

Gere todas as telas coerentes com o mesmo design system (cores, tipografia, cartões
arredondados, badges de categoria e banner ético). Priorize clareza de dados: tabelas legíveis,
gráficos limpos e hierarquia visual forte.

## FIM DO PROMPT PARA O STITCH
