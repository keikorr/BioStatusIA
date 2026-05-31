# 📖 Dossiê de Documentação: BioStatusIA

> **Sistema de Apoio à Decisão Clínica (CDSS)** para análise inteligente de imagens médicas e dados tabulares com IA Multi-Agente Local (CrewAI + Ollama) e AutoML.

Este documento contém toda a especificação técnica, arquitetura de dados e modificações recentes do projeto, estruturado para ser colado diretamente no **Notion**.

---

## 🎯 1. Objetivos do Projeto
O **BioStatusIA** foi concebido para ser uma ferramenta universal de suporte à decisão clínica médica. O seu princípio fundamental é **aceitar qualquer tipo de dado de entrada** (imagem, lote de imagens, CSV com dados clínicos ou misto), identificar automaticamente a estrutura e disparar o pipeline adequado de processamento sem intervenção humana.

---

## 🛠️ 2. Requisitos do Sistema

### Requisitos Funcionais (RF)
*   **RF-01 (Detecção Automática):** O sistema deve reconhecer e rotear automaticamente 5 modos de dados: `imagem_unica`, `imagens_soltas`, `dataset_rotulado`, `tabular` (CSV/TXT) e `multimodal`.
*   **RF-02 (Análise Estatística Cega):** Calcular métricas estatísticas sobre os dados brutos originais (antes de qualquer limpeza) para evitar viés.
*   **RF-03 (Pré-Processamento Adaptativo):** O sistema deve propor e justificar o melhor conjunto de filtros baseado estritamente nas estatísticas da base.
*   **RF-04 (AutoML de Alta Competição):** Treinar 6 classificadores concorrentes em paralelo e salvar o de maior desempenho (AUC-ROC).
*   **RF-05 (Geração de Laudo Clínico):** Gerar um laudo em linguagem natural médica assinado por agentes IA através do CrewAI + LLM local.
*   **RF-06 (Interface em Abas):** Painel web em Flask organizado em 3 visões (Pré-processamento, Estatística e AutoML/Laudo).

### Requisitos Não-Funcionais (RNF)
*   **RNF-01 (Privacidade e Segurança):** Processamento 100% local. Nenhuma informação de saúde ou imagem de paciente pode ser enviada para APIs externas.
*   **RNF-02 (Modelo de Linguagem):** Utilizar o modelo local `qwen2.5:3b` via Ollama.
*   **RNF-03 (Performance de ML Clássico):** Biblioteca `scikit-learn` para treino rápido (< 5 segundos para o AutoML tabular).
*   **RNF-04 (Interface Fluida):** Tailwind CSS + Plotly.js para carregamento assíncrono e gráficos interativos no navegador.

---

## 🧬 3. Arquitetura Unificada de Processamento
Tanto imagens quanto dados tabulares seguem rigorosamente a mesma simetria metodológica científica de ponta a ponta:

```
Dado Bruto (Raw) ──> Análise Estatística ──> Proposta de Pré-Proc ──> Execução do Pré-Proc ──> AutoML (Modelagem) ──> Laudo IA
```

### Fluxo Detalhado por Tipo de Dado:

| Etapa | Fluxo de Imagens (Ultrassom) | Fluxo Tabular Clínico (CSV) |
| :--- | :--- | :--- |
| **1. Dado Raw** | Imagens originais em escala de cinza. | Leitura das colunas numéricas tolerando NaNs (`?`, `NaN`, `-`). |
| **2. Estatística** | Média de luz, contraste, ruído (sigma) e outliers (IQR). | **31 Métricas Univariadas** (Central, Posição, Forma, Shapiro, Outliers) + Pearson/Spearman. |
| **3. Proposta** | Engenheiro de PDI decide filtros baseados no ruído e contraste. | Sistema avalia nulos e outliers acumulados para propor Imputação e Scalers. |
| **4. Execução** | Non-Local Means/Gaussian, CLAHE, Percentil 1-99%. | Imputação por **Mediana** + **RobustScaler** (para outliers) ou **StandardScaler**. |
| **5. AutoML** | Treina e avalia 6 modelos (AUC). | Treina e avalia 6 modelos sob o Scaler dinâmico proposto. |
| **6. Laudo IA** | Equipe de 4 agentes (PDI -> Técnico -> Dados -> Radiologista). | Agente Bioestatístico traduz o dossiê em laudo textual. |

---

## 📈 4. O Motor de 31 Métricas Estatísticas
Para dados estruturados tabulares, o sistema extrai o dossiê univariado completo para cada feature clínica:

*   **Tendência Central:** Média, Mediana e Moda.
*   **Dispersão/Variabilidade:** Mínimo, Máximo, Amplitude (*range*), Variância, Desvio Padrão, Coeficiente de Variação (CV) e Intervalo Interquartil (IQR).
*   **Posição:** Quartis (Q1, Q2, Q3), Percentis (P10, P25, P50, P75, P90) e Decis completos (D1 a D9).
*   **Forma:** Assimetria (*skewness*) e Curtose (*kurtosis*).
*   **Outliers:** Contagem de anomalias por Z-score (>2.5 desvios) e Regra 1.5×IQR.
*   **Distribuição:** Sinal-Ruído (SNR), Entropia do histograma de densidade e Uniformidade.
*   **Normalidade:** Testes de Shapiro-Wilk e Kolmogorov-Smirnov.
*   **Grupo & Hipótese:** Média/Desvio por classe e **Teste t de Student** (2 grupos) ou **ANOVA** (múltiplos grupos) para medir a relevância clínica ($p < 0.05$).

---

## 🤖 5. Bateria de AutoML (Modelos Concorrentes)
O arquivo `classificador.py` treina 6 algoritmos de ponta em paralelo:
1.  **Regressão Logística:** Baseline estatística linear de alta interpretabilidade.
2.  **K-Nearest Neighbors (KNN):** Modelo baseado em proximidade espacial.
3.  **Support Vector Machine (SVM RBF):** Captura limites não-lineares em alta dimensão.
4.  **Random Forest Classifier:** Conjunto de árvores robusto contra overfitting.
5.  **Gradient Boosting Classifier:** Árvores sequenciais focadas em redução de erro (estado da arte tabular).
6.  **MLP Classifier (Rede Neural):** Arquitetura MLP de duas camadas (`64x32`) para mapeamento de padrões complexos.

O vencedor é selecionado dinamicamente pela maior **Área Sob a Curva (AUC-ROC)** e salvo em disco.

---

## 🎨 6. Painel de Controle (Visual Premium)
A Tela 2 foi redesenhada sob o conceito de abas, contendo:
*   **Aba 1 (Pré-processamento):** Detalha de forma explicável como o sistema limpou os dados (imagens ou tabelas) com os cards de justificativa da engenharia.
*   **Aba 2 (Estatística):** Sidebar interativa de features. Ao clicar em uma feature, exibe o painel de 31 métricas e a tabela de significância de grupo. Apresenta o **Heatmap Nativo de Correlação** colorido via CSS inline.
*   **Aba 3 (Modelos & Laudo):** Pódio do AutoML, gráficos do Plotly.js (ROC, Confusão, Comparativo), o Laudo Clínico formatado em tipografia médica elegante e o histórico do banco de dados SQLite.

---

## 🔧 7. Configuração do Notion MCP (Integração Futura)
Para permitir que o Antigravity interaja diretamente com o seu Notion (lendo ou escrevendo estas documentações), o arquivo `mcp_config.json` foi configurado e salvo localmente no caminho:
`C:\Users\Braudel\.gemini\antigravity\mcp_config.json`

### Estrutura criada:
```json
{
  "mcpServers": {
    "notion": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-notion"
      ],
      "env": {
        "NOTION_API_KEY": "ntn_663969873673tfYxWV49pgdutriDXp0wkiowziop..."
      }
    }
  }
}
```
*   **Status:** Chave de API integrada com sucesso. A IDE lerá a integração assim que for reiniciada pelo usuário, habilitando os comandos automáticos de escrita de páginas.
