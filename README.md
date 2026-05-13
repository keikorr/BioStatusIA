# 🧬 BiostatsIA: Sistema Multi-Agente para Radiômica

> **Sistema Inteligente de Apoio à Decisão Clínica (CDSS) para análise automatizada de imagens médicas via Radiômica, Visão Computacional e IA Multi-Agente.**

O **BiostatsIA** é um Sistema de Apoio à Decisão Clínica (**Clinical Decision Support System - CDSS**) desenvolvido para o processamento automatizado de imagens de ultrassom, utilizando uma arquitetura **multi-agente com CrewAI**.

O sistema combina **Visão Computacional Clássica**, **Radiômica** e **Large Language Models (LLMs)** para transformar imagens médicas em **dados clínicos estruturados, interpretáveis e auditáveis**.

A proposta central é reduzir a subjetividade da análise diagnóstica por imagem, extraindo biomarcadores quantitativos e gerando laudos automatizados com alta explicabilidade.

---

## 🎯 Objetivo do Projeto

O projeto tem como foco a análise inteligente de exames de ultrassom, especialmente no contexto da identificação de lesões benignas e malignas.

Através da **Radiômica**, o sistema extrai padrões matemáticos que frequentemente são imperceptíveis à observação humana, fornecendo suporte quantitativo para decisões clínicas.

### Principais Diferenciais

✅ **Explicabilidade (Explainable AI)**  
O sistema evita decisões do tipo "caixa-preta". Cada inferência é fundamentada em métricas quantitativas como:

- Solidez
- Circularidade
- Entropia
- Homogeneidade
- Assimetria
- Curtose
- Relação sinal-ruído (SNR)

---

✅ **Privacidade e Processamento Local**  
Toda a camada de processamento de linguagem natural pode ser executada localmente via **Ollama**, garantindo que dados sensíveis não deixem a infraestrutura hospitalar/local.

---

✅ **Arquitetura Multi-Agente**  
Cada agente possui responsabilidade especializada dentro do pipeline:

- **Analista Técnico**
- **Radiologista IA**
- **Classificador Cognitivo**
- **Gerador de Relatórios**

---

✅ **Dual Reporting**  
Geração simultânea de:

- **Laudo técnico detalhado**
- **Dashboard clínico moderno**
- **Relatório auditável**

---

## 🏗️ Arquitetura da Solução

```text
                    ┌──────────────────────┐
                    │ Dataset de Ultrassom │
                    └──────────┬───────────┘
                               │
                               ▼
                ┌──────────────────────────────┐
                │ Ingestão via KaggleHub       │
                └──────────┬───────────────────┘
                           │
                           ▼
          ┌──────────────────────────────────────────┐
          │ Processamento Digital de Imagem (PDI)    │
          │ OpenCV + Scikit-Image                    │
          │ - Segmentação                            │
          │ - Limpeza                                │
          │ - Extração de Features                   │
          └──────────┬───────────────────────────────┘
                     │
                     ▼
      ┌────────────────────────────────────────────────────┐
      │ Pipeline Multi-Agente (CrewAI)                     │
      │                                                    │
      │  Analista Técnico                                  │
      │      ↓                                             │
      │  Validação das métricas                            │
      │                                                    │
      │  Radiologista IA                                   │
      │      ↓                                             │
      │  Interpretação diagnóstica                         │
      │                                                    │
      │  Classificador Cognitivo                           │
      │      ↓                                             │
      │  Llama 3.1 classifica o exame                     │
      │                                                    │
      │  Gerador de Relatórios                             │
      └──────────┬─────────────────────────────────────────┘
                 │
                 ▼
      ┌──────────────────────────────────────────┐
      │ HTML + Tailwind CSS                      │
      │ Dashboard + Relatórios                   │
      └──────────────────────────────────────────┘
```

---

## ⚙️ Como Funciona

O BiostatsIA opera em **5 etapas principais**:

### 1. 📥 Ingestão de Dados

Aquisição automatizada do dataset utilizando:

- `kagglehub`

Exemplo:

```python
import kagglehub
```

---

### 2. 🖼️ Processamento Digital de Imagem

Responsável por:

- Pré-processamento
- Segmentação da lesão
- Extração de características radiômicas

Bibliotecas:

- OpenCV
- Scikit-Image
- NumPy

---

### 3. 🤖 Orquestração Multi-Agente

#### 🔬 Analista Técnico
Valida consistência matemática das features extraídas.

Exemplo:

- Solidez < 0.70 → possível irregularidade morfológica
- Alta entropia → maior heterogeneidade tecidual

---

#### 🩻 Radiologista IA
Interpreta os biomarcadores e produz laudo preliminar.

---

#### 🧠 Classificador Cognitivo
Executado com **Llama 3.1 via Ollama**, responsável por:

- análise semântica do vetor de features
- classificação diagnóstica
- inferência explicável

---

### 4. 📊 Renderização de Resultados

Os dados são renderizados em interfaces modernas usando:

- HTML5
- Tailwind CSS
- templates dinâmicos

---

### 5. 📄 Geração de Relatórios

Produção automática de:

- Dashboard clínico
- Relatório técnico
- Logs auditáveis

---

# 🛠️ Instalação

## Pré-requisitos

### Python

Versão recomendada:

```bash
Python >= 3.10 < 3.14
```

---

### Ollama

Instale o Ollama:

https://ollama.com

---

## Configuração do Modelo Local

Baixe o modelo necessário:

```bash
ollama run llama3.1
```

---

## Clonando o Projeto

```bash
git clone https://github.com/seu-usuario/biostatsia.git
cd biostatsia
```

---

## Instalando Dependências

```bash
pip install -r requirements.txt
```

---

# 🚀 Como Executar

Execute o pipeline principal:

```bash
python src/biostatsia/main.py
```

---

## Execução Esperada

O sistema processará automaticamente imagens do dataset e realizará:

- Segmentação
- Extração de biomarcadores
- Classificação cognitiva
- Geração de dashboard
- Emissão de relatório técnico

---

# 📂 Saídas Geradas

Após execução:

## Dashboard Clínico

```bash
dashboard_inteligencia_medica.html
```

Interface com:

- indicadores visuais
- estatísticas por classe
- badges diagnósticos
- layout responsivo

---

## Relatório Técnico

```bash
relatorio_tecnico_biostatsia.html
```

Inclui:

- logs completos
- métricas brutas
- validações matemáticas
- auditoria do pipeline

---

# 🧬 Biomarcadores Analisados

| Categoria | Métricas | Interpretação Clínica |
|---------|---------|----------------------|
| Morfologia | Solidez, Circularidade | Regularidade e formato das margens |
| Textura | Entropia, Homogeneidade | Complexidade estrutural do tecido |
| Estatística | SNR, Assimetria, Curtose | Distribuição tonal e qualidade do sinal |

---

# 🛠️ Stack Tecnológica

## IA & Orquestração

- CrewAI
- Ollama
- Llama 3.1

---

## Visão Computacional

- OpenCV
- Scikit-Image
- NumPy

---

## Backend

- Python

---

## Frontend / Relatórios

- HTML5
- Tailwind CSS

---

## Dados

- KaggleHub

---

# 📁 Estrutura do Projeto

```text
biostatsia/
│
├── src/
│   └── biostatsia/
│       ├── agents/
│       ├── tools/
│       ├── services/
│       ├── templates/
│       ├── utils/
│       └── main.py
│
├── dashboard_inteligencia_medica.html
├── relatorio_tecnico_biostatsia.html
├── requirements.txt
└── README.md
```

---

# 👨‍🔬 Caso de Uso Clínico

Fluxo resumido:

1. Receber imagem de ultrassom
2. Identificar região de interesse
3. Extrair biomarcadores quantitativos
4. Validar consistência matemática
5. Classificar lesão
6. Gerar laudo automatizado
7. Produzir dashboard clínico

---

# ⚠️ Aviso Importante

> **Este software é uma ferramenta de suporte à decisão clínica.**
>
> Não substitui avaliação, interpretação ou diagnóstico realizado por profissional médico habilitado.

---

# 👨‍💻 Autor

**Projeto acadêmico de pesquisa (Mestrado)**

Área:

- Inteligência Artificial aplicada à Saúde
- Radiômica
- Sistemas Multi-Agente
- Infraestrutura de Dados

📍 Fortaleza, Ceará — Brasil

---

# 📜 Licença

Defina aqui a licença do projeto:

Exemplo:

```text
MIT License
```

---

# 🚀 Futuras Evoluções

- API REST para integração hospitalar
- suporte a DICOM
- integração com PACS
- classificação multiclasses
- explicabilidade visual (heatmaps)
- deploy containerizado com Docker
- dashboard web em tempo real

---

# 💡 Visão

Transformar imagens médicas em inteligência clínica explicável através de IA distribuída.