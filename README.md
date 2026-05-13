# 🧬 BioStatusIA: Sistema Multi-Agente para Radiômica

> **Sistema Inteligente de Apoio à Decisão Clínica (CDSS) para análise automatizada de imagens médicas via Radiômica, Visão Computacional e IA Multi-Agente.**

O **BioStatusIA** é um Sistema de Apoio à Decisão Clínica (**Clinical Decision Support System - CDSS**) desenvolvido para o processamento automatizado de imagens de ultrassom, utilizando uma arquitetura **multi-agente com CrewAI**.

O sistema combina **Visão Computacional Clássica**, **Radiômica** e **Large Language Models (LLMs)** para transformar imagens médicas em **dados clínicos estruturados, interpretáveis e auditáveis**.

A proposta central é reduzir a subjetividade da análise diagnóstica por imagem, extraindo biomarcadores quantitativos e gerando laudos automatizados com alta explicabilidade.

---

## 🎯 Objetivo do Projeto

O projeto tem como foco a análise inteligente de exames de ultrassom, especialmente no contexto da identificação de lesões benignas e malignas.

Através da **Radiômica**, o sistema extrai padrões matemáticos que frequentemente são imperceptíveis à observação humana, fornecendo suporte quantitativo para decisões clínicas.

### Principais Diferenciais

✅ **Explicabilidade (Explainable AI)**  
O sistema evita decisões do tipo "caixa-preta". Cada inferência é fundamentada em métricas quantitativas como:
* Solidez e Circularidade
* Entropia e Homogeneidade
* Assimetria e Curtose
* Relação sinal-ruído (SNR)

✅ **Privacidade e Processamento Local**  
Toda a camada de processamento de linguagem natural é executada localmente via **Ollama**, garantindo que dados sensíveis não deixem a infraestrutura hospitalar/local.

✅ **Arquitetura Multi-Agente Especializada**  
* **Analista Técnico**: Validação matemática e extração de features.
* **Radiologista IA**: Interpretação clínica e redação de laudo preliminar.
* **Classificador Cognitivo**: Inferência diagnóstica via Llama 3.1.
* **Gerador de Relatórios**: Consolidação dos dados e estruturação dos dashboards em HTML/Tailwind.

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
          │ - Segmentação e Extração de Features     │
          └──────────┬───────────────────────────────┘
                     │
                     ▼
      ┌────────────────────────────────────────────────────┐
      │ Pipeline Multi-Agente (CrewAI + Llama 3.1)         │
      │                                                    │
      │  Analista Técnico (Métricas Radiômicas)            │
      │        ↓                                           │
      │  Radiologista IA (Interpretação Clínica)           │
      │        ↓                                           │
      │  Classificador Cognitivo (Inferência Local)        │
      │        ↓                                           │
      │  Gerador de Relatórios (Consolidação de Dados)     │
      └──────────┬─────────────────────────────────────────┘
                 │
                 ▼
      ┌──────────────────────────────────────────┐
      │ HTML5 + Tailwind CSS                     │
      │ Dashboard Clínico + Relatório Técnico    │
      └──────────────────────────────────────────┘
```

---

## ⚙️ Como Funciona

O **BioStatusIA** opera em etapas integradas:

### 1. 🖼️ Processamento Digital e Radiômica
Responsável pela segmentação da lesão e extração de características através de ferramentas customizadas (`custom_tool.py`), utilizando **OpenCV** e **Scikit-Image**.

### 2. 🤖 Orquestração Multi-Agente
Utiliza o **CrewAI** para gerenciar a colaboração entre agentes. O **Analista Técnico** valida se a solidez e a entropia condizem com padrões de malignidade, enquanto o **Radiologista IA** traduz esses números em linguagem médica.

### 3. 🧠 Inteligência Cognitiva Local
Toda a lógica de classificação é processada pelo **Llama 3.1 via Ollama**, permitindo uma análise semântica profunda do vetor de features sem necessidade de internet.

---

## 🛠️ Instalação

### Pré-requisitos
* **Python**: `>= 3.10 < 3.14`
* **Ollama**: [Instale aqui](https://ollama.com)

### Configuração do Modelo Local
```bash
ollama run llama3.1
```

### Clonando e Instalando
```bash
git clone [https://github.com/JuniorSoares716/BioStatusIA.git](https://github.com/JuniorSoares716/BioStatusIA.git)
cd biostatusia
pip install -r requirements.txt
```

---

## 🚀 Como Executar

Para iniciar o pipeline de testes (configurado para processamento no `main.py`):

```bash
python src/biostatusia/main.py
```

### 📂 Saídas Geradas
* **Dashboard Clínico (`dashboard_inteligencia_medica.html`)**: Interface visual rica com badges de diagnóstico e indicadores de amostragem.
* **Relatório Técnico (`relatorio_tecnico_biostatsia.html`)**: Logs auditáveis do raciocínio dos agentes e métricas brutas.

---

## 🧬 Biomarcadores Analisados

| Categoria | Métricas | Interpretação Clínica |
| :--- | :--- | :--- |
| **Morfologia** | Solidez, Circularidade | Avaliação da regularidade das bordas da lesão. |
| **Textura** | Entropia, Homogeneidade | Avaliação da complexidade estrutural interna. |
| **Estatística** | SNR, Curtose | Qualidade do sinal e distribuição tonal. |

---

## 📁 Estrutura do Projeto

```text
biostatusia/
│
├── src/
│   └── biostatusia/
│       ├── config/
│       │   ├── agents.yaml      # Definição dos perfis
│       │   └── tasks.yaml       # Escopo das tarefas
│       │
│       ├── tools/
│       │   └── custom_tool.py   # Motor de Radiômica
│       │
│       ├── crew.py              # Orquestração e max_iter
│       └── main.py              # Gestão do pipeline e relatórios
│
├── template_moderno.html        # Fonte visual (Tailwind CSS)
├── dashboard_inteligencia_medica.html # Saída visual final
├── relatorio_tecnico_biostatsia.html  # Saída técnica auditável
├── requirements.txt             # Dependências
└── README.md                    # Documentação principal
```

---

## ⚠️ Aviso Importante
> **Este software é uma ferramenta de suporte à decisão clínica.** Não substitui a avaliação ou o diagnóstico realizado por um profissional médico habilitado.

---

## 👨‍💻 Autor
**Projeto acadêmico de pesquisa (Mestrado)**  
📍 Fortaleza, Ceará — Brasil  
**Áreas**: IA na Saúde, Radiômica e Sistemas Multi-Agente.

---

## 📜 Licença
```text
MIT License
```
