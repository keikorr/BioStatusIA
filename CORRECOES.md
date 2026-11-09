# Correções de auditoria (branch `correcoes-auditoria`)

Este documento relaciona cada item do checklist reproduzível (`audit/outputs/02_checklist.md`, gerado por `audit/scripts/02_code_protocol_checklist.py`) à correção feita nesta branch. O checklist foi produzido contra o commit auditado `2d89637` (repositório de pesquisa) e a linhagem `6960fd6` (`atualizacao_features`); esta branch parte da `main` (`e2ad87c`).

**Importante:** as correções alteram o código atual. Elas **não** mudam os 8 resultados publicados no artigo, que continuam sendo os do commit `2d89637`. Rodar o pipeline corrigido produzirá números diferentes (em geral menos otimistas). Nenhum valor aqui constitui validação clínica ou externa.

## Mapa item → correção

| Item | Problema | Situação | Onde |
|---|---|---|---|
| D01 | Seleção de features fora do fold interno (vazamento na CV) | Corrigido: SMOTE/SHAP removidos do treinador padrão; imputação + scaler + modelo dentro de `Pipeline` por fold | `pipeline/avaliacao_modelos.py` |
| D02 | Schema numérico decidido pelas 30 primeiras linhas | Corrigido | `pipeline/dados_tabulares.py::detectar_schema` |
| D03 | Colunas de ID entram como features | Corrigido (`NOMES_IDENTIFICADORES`) | `pipeline/dados_tabulares.py` |
| D05 | "Entropia GLCM" era entropia de histograma; GLCM de um só ângulo | Corrigido: GLCM em 4 ângulos, entropia GLCM real, `entropia_histograma` separada | `pipeline/extracao.py`, `extracao_dicom.py` |
| D06 | Normalização por 255 sem min-max por imagem | Corrigido | `pipeline/preprocessamento.py` |
| D08 | `except Exception` silencioso e dependências ausentes | Corrigido: `requirements.txt` regenerado do `uv.lock`; sem fallback silencioso no caminho padrão | `requirements.txt`, `pyproject.toml` |
| D10 | Narrativa do LLM gerada antes do treino | Corrigido: AutoML roda antes da crew e o resumo é passado a ela | `app.py`, `config/tasks.yaml` |
| D11 | Prompts descreviam 2 modelos e "melhor = maior AUC" | Corrigido | `config/agents.yaml`, `config/tasks.yaml`, `tools/treino_tool.py` |
| D13 | Dois treinadores divergentes | Corrigido: `classificador.treinar*` delega a `avaliacao_modelos` | `pipeline/classificador.py` |
| D14 | Assimetria de hiperparâmetros/pesos entre modelos | Parcial: `max_iter` padronizado (2000) e `random_state` onde aplicável | `pipeline/avaliacao_modelos.py` |
| D16 | ECE: bin final semiaberto excluía amostras | Corrigido (último bin fechado) | `calcular_ece` |
| D18 | DP com `ddof=0` | Corrigido (`ddof=1`) | `_resumo` |
| — | Seleção do vencedor pelo AUC no teste; piso de sensibilidade desativado (`or True`) | Corrigido: seleção só na CV interna com piso rígido 0,80 | `selecionar_melhor_modelo` |
| — | McNemar contra baseline inadequado | Corrigido: vencedor × segundo colocado, descritivo | `_mcnemar_test` |
| — | Split por linha com vários registros por sujeito | Corrigido: split/CV por grupo quando há coluna de sujeito | `extrair_grupos`, `_split_externo` |
| — | `classificar()` carregava `.pkl` arbitrário | Corrigido: só `modelo_vencedor.pkl` | `pipeline/classificador.py` |
| — | HTMLs gerados desatualizados na raiz | Movidos para `docs/exemplos_saida_v1/` | — |
| — | Documentação com "AUC + 5-fold" e `max_iter` antigos | Atualizada | `README.md`, `CLAUDE.md`, `docs/documentacao_notion.md` |

## Não alterado / fora do alcance do código

- **D04, D07, D12, D15, D17, D23:** não foram verificados item a item nesta branch; reavaliar executando `audit/run_all.sh` contra o código corrigido. D12 (tempos) segue valendo: `tempo_treino_s` mede apenas o ajuste final.
- **D09:** tempos de execução de imagem incluem o kickoff do CrewAI; não há alteração de medição.
- **D19–D22, D24:** são questões de proveniência e arredondamento dos números do artigo (origem do dataset, contagens por classe, repositórios distintos). Não se resolvem com código; dependem dos autores.
- Branches diferentes de `main` não foram tocadas, conforme combinado.

## Reprodutibilidade

```bash
uv sync
uv run pytest            # testes em tests/
bash audit/run_all.sh    # scripts de auditoria (ver audit/README.md)
```
