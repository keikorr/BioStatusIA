# Auditoria metodológica — BioStatusIA (v3)

Auditoria baseada na leitura do **código real** (`src/biostatusia/pipeline/*`,
`crew.py`, `app.py`) e nas **evidências de execução** (`reports/*.md`,
`static/runs/*/metricas.json`). Serve de base técnica para os dois papers IEEE.

## Evidência empírica usada
- **BUSI real (780 imagens; 570 benignas / 210 malignas):** melhor modelo
  RandomForest — Acc 0,814 · AUC 0,800 · Prec 0,76 · **Recall 0,452** · F1 0,567.
- **Mini-BUSI (100 imagens):** MLP — AUC 0,94 · Sens 0,90 · Espec 0,90.
- **WBCD-50 tabular (50 amostras, 30 features):** LogisticRegression AUC 1,0.
- **Sintéticos F1/F3/F4 (n=14 cada):** AUC 1,0 em todas — *smoke tests*, não validação.

## Pontos fortes (confirmados no código)
1. Núcleo em **funções puras**; contrato único `SinalNormalizado` desacopla
   leitores de extratores (F1/F3/F4 + tabular).
2. Detecção automática de **9 modos** com fallback `invalido` explícito.
3. **Métricas clínicas ricas** além de acurácia: sensibilidade, especificidade,
   MCC, Kappa, ECE, McNemar, latência — em `avaliacao_modelos.py`.
4. **SMOTE/ADASYN só no treino** no caminho enriquecido (evita vazamento no teste).
5. **SHAP** no vencedor; laudo populacional determinístico; aviso ético obrigatório.
6. Reprodutibilidade via `random_state=42`.

## Ameaças à validade (achados centrais) — ✅ CORRIGIDAS

| # | Achado | Local no código | Impacto | Correção aplicada |
|---|--------|-----------------|---------|-------------------|
| **T1** ✅ | `StandardScaler().fit_transform(X)` aplicado ao dataset **inteiro antes** do `train_test_split` | `avaliacao_modelos.avaliar_modelos`; `classificador.treinar_vetores` | Vazamento de estatísticas do teste → métricas infladas | Split feito **primeiro**; `scaler.fit(X_train)` e só `transform` no teste, em ambos os treinadores |
| **T2** ✅ | SMOTE aplicado **antes** do `StratifiedKFold` (folds tirados do conjunto já superamostrado) | `avaliar_modelos` | Amostras sintéticas vazam entre folds → CV otimista | Escala e `balancear()` reajustados **dentro de cada fold** da CV |
| **T3** ✅ | Critério `if m["sensibilidade"] >= 0.8 or True` — o `or True` anula o piso de sensibilidade | `avaliar_modelos` (seleção do vencedor) | Vencedor era só max-AUC; no BUSI selecionava modelo com recall 0,45 | `or True` removido; piso de sensibilidade ≥ 0,8 agora vigente, com fallback para max-AUC e campo `criterio_selecao` |
| **T4** ✅ | Métricas de teste de **um único split 80/20**; sem CV repetida nem IC | `avaliar_modelos` | Em n pequeno, AUC=1,0 sem significância | `RepeatedStratifiedKFold` (5×3) + **IC 95%** (t-Student) por métrica em `metricas_cv[...]["ic95"]` |

### Status da verificação
Teste funcional em dataset sintético desbalanceado (160×12, 72/28):
`criterio_selecao = "maior AUC com sensibilidade>=0.8"`, `cv_protocolo = {5 splits, 3 repeats}`,
IC95 da AUC do vencedor `[0.901, 0.963]`, balanceamento e SHAP operando — sem erro de runtime.

> **Nota (T4 em `treinar_vetores`):** por design (v3.1) esse caminho é holdout puro
> sem CV/SMOTE/SHAP; nele foi corrigido apenas o vazamento de escala (T1). O rigor
> de CV repetida + IC vive em `avaliar_modelos`, o avaliador enriquecido.

### Observações secundárias
- **McNemar**: o código compara o vencedor com o **primeiro** modelo
  (LogisticRegression), não com o segundo melhor como diz a documentação.
- **`treinar_vetores` (caminho padrão de imagem/tabular) não chama `balancear()`** —
  por isso o BUSI real fica com recall 0,45 (só o caminho `avaliar_modelos` balanceia).
- **GLCM** calculado em **uma única distância e um único ângulo** (d=1, θ=0);
  entropia vem do histograma, não da GLCM — descritor de textura subespecificado.
- **Vetores de dimensão heterogênea** entre famílias (9–15 features) — reuso
  entre famílias exige alinhamento explícito.
- **Camada LLM não validada** factualmente (Ollama `qwen2.5`); *timeouts* >3 h
  reportados nos testes; laudos gerados a partir dos artefatos numéricos.
- **Persistência via `pickle`** — nota de reprodutibilidade/segurança.

## Recomendações prioritárias
1. Corrigir T3 (1 linha) — maior impacto clínico.
2. Migrar scaling e SMOTE para dentro de `Pipeline`/CV (T1, T2).
3. Trocar split único por CV repetida com intervalos de confiança (T4).
4. Ativar balanceamento no caminho padrão `treinar_vetores`.
5. GLCM multi-orientação (0/45/90/135°) e média de Haralick.
6. Checagem de *grounding* factual nos laudos do LLM.

> **Nota honesta para a banca:** o valor científico está em reportar o recall
> real de 0,452 no BUSI em vez de exibir os AUC=1,0 dos conjuntos sintéticos. Os
> dois papers assumem essa postura de auditoria-primeiro.
