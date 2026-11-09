import csv
from pathlib import Path

import numpy as np

LABEL_KEYWORDS = {
    "label", "class", "diagnosis", "diagnostico", "target",
    "categoria", "outcome", "y", "result", "resultado",
}
MALIGNANT_KEYWORDS = {
    "m", "malignant", "maligno", "malign", "positive",
    "1", "true", "yes", "sim", "abnormal",
}


def carregar_csv(caminho: str) -> tuple[list[str], list[list[str]]] | None:
    """Carrega um CSV ou TXT delimitado. Detecta o separador automaticamente."""
    caminho_p = Path(caminho)
    if not caminho_p.exists() or not caminho_p.is_file():
        return None

    try:
        with open(caminho_p, "r", encoding="utf-8-sig") as f:
            sample = f.read(4096)
    except UnicodeDecodeError:
        with open(caminho_p, "r", encoding="latin-1") as f:
            sample = f.read(4096)

    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
        delimitador = dialect.delimiter
    except csv.Error:
        delimitador = ","

    try:
        with open(caminho_p, "r", encoding="utf-8-sig") as f:
            reader = csv.reader(f, delimiter=delimitador)
            rows = [row for row in reader if any(c.strip() for c in row)]
    except UnicodeDecodeError:
        with open(caminho_p, "r", encoding="latin-1") as f:
            reader = csv.reader(f, delimiter=delimitador)
            rows = [row for row in reader if any(c.strip() for c in row)]

    if len(rows) < 2:
        return None

    header = [h.strip() for h in rows[0]]
    data = rows[1:]
    return header, data


TOKENS_AUSENTES = {"", "?", "nan", "null", "none", "na", "n/a", "-", "#n/a"}
NOMES_IDENTIFICADORES = {
    "id", "index", "unnamed: 0", "patient", "patient_id", "paciente", "id_paciente",
    "subject", "subject_id", "sujeito", "record", "record_id", "name", "nome", "codigo",
}
LIMITE_CARDINALIDADE_ONEHOT = 20
FRACAO_MINIMA_NUMERICA = 0.95


def _chave_sujeito(valor: str) -> str:
    """Remove o sufixo de repetição (ex.: 'phon_R01_S01_3' -> 'phon_R01_S01'),
    para agrupar gravações/registros do mesmo sujeito."""
    import re
    return re.sub(r"[_\-.]\d+$", "", valor.strip())


def _ausente(valor: str) -> bool:
    return valor.strip().lower() in TOKENS_AUSENTES


def _valores_coluna(data: list[list[str]], idx: int) -> list[str]:
    return [row[idx].strip() for row in data if idx < len(row) and not _ausente(row[idx])]


def _eh_numerica(valores: list[str]) -> bool:
    if not valores:
        return False
    ok = 0
    for v in valores:
        try:
            float(v.replace(",", "."))
            ok += 1
        except ValueError:
            pass
    return ok / len(valores) >= FRACAO_MINIMA_NUMERICA


def detectar_schema(header: list[str], data: list[list[str]]) -> dict:
    """Identifica coluna-rótulo, colunas identificadoras, numéricas e
    categóricas de baixa cardinalidade, olhando a base inteira.

    - Numérica: >= 95% dos valores não ausentes convertem para número; tokens
      de ausência (ex.: "N/A", "?") viram NaN em vez de descartar a coluna.
    - Identificadores (id, patient_id, name...) nunca entram como feature; se
      algum se repete entre linhas, é usado como grupo de sujeito no split.
    - Categóricas com 2 a 20 valores entram via one-hot; as demais colunas
      descartadas ficam listadas em `colunas_descartadas`.
    """
    n_cols = len(header)

    label_idx = None
    for i, name in enumerate(header):
        if name.lower().strip() in LABEL_KEYWORDS:
            label_idx = i
            break
    if label_idx is None and n_cols > 1:
        for idx in (n_cols - 1, 0):
            if 2 <= len(set(_valores_coluna(data, idx))) <= 10:
                label_idx = idx
                break

    id_cols = [i for i, h in enumerate(header)
               if i != label_idx and h.strip().lower() in NOMES_IDENTIFICADORES]

    numeric_cols, categorical_cols, descartadas = [], [], []
    categorias: dict[int, list[str]] = {}
    for i in range(n_cols):
        if i == label_idx or i in id_cols:
            continue
        valores = _valores_coluna(data, i)
        if _eh_numerica(valores):
            numeric_cols.append(i)
            continue
        unicos = sorted(set(valores))
        if 2 <= len(unicos) <= LIMITE_CARDINALIDADE_ONEHOT:
            categorical_cols.append(i)
            categorias[i] = unicos
        else:
            descartadas.append(header[i])

    grupo_idx, grupo_derivado = None, False
    for i in id_cols:
        valores = _valores_coluna(data, i)
        if not valores:
            continue
        if len(set(valores)) < len(valores):
            grupo_idx = i
            break
        derivados = [_chave_sujeito(v) for v in valores]
        if len(set(derivados)) < len(derivados):
            grupo_idx, grupo_derivado = i, True
            break

    onehot_names = [f"{header[i]}={c}" for i in categorical_cols for c in categorias[i]]
    return {
        "label_idx": label_idx,
        "label_name": header[label_idx] if label_idx is not None else None,
        "feature_indices": numeric_cols,
        "categorical_indices": categorical_cols,
        "categorical_categorias": {str(k): v for k, v in categorias.items()},
        "feature_names": [header[i] for i in numeric_cols] + onehot_names,
        "n_features": len(numeric_cols) + len(onehot_names),
        "n_amostras": len(data),
        "colunas_identificadoras": [header[i] for i in id_cols],
        "coluna_grupo": header[grupo_idx] if grupo_idx is not None else None,
        "grupo_idx": grupo_idx,
        "grupo_derivado_de_sufixo": grupo_derivado,
        "colunas_descartadas": descartadas,
    }


def _linhas_rotuladas(data: list[list[str]], schema: dict) -> list[list[str]]:
    label_idx = schema["label_idx"]
    if label_idx is None:
        return data
    return [row for row in data if label_idx < len(row) and row[label_idx].strip()]


def extrair_features(data: list[list[str]], schema: dict) -> tuple[np.ndarray, np.ndarray | None, dict]:
    """Converte data em (X, y, label_map). Ausentes viram NaN (imputados depois,
    dentro de cada fold); categóricas entram em one-hot após as numéricas."""
    feature_idx = schema["feature_indices"]
    cat_idx = schema.get("categorical_indices", [])
    categorias = schema.get("categorical_categorias", {})
    label_idx = schema["label_idx"]
    linhas = _linhas_rotuladas(data, schema)

    X_rows: list[list[float]] = []
    for row in linhas:
        features = []
        for i in feature_idx:
            val = row[i].strip() if i < len(row) else ""
            if _ausente(val):
                features.append(np.nan)
                continue
            try:
                features.append(float(val.replace(",", ".")))
            except ValueError:
                features.append(np.nan)
        for i in cat_idx:
            val = row[i].strip() if i < len(row) else ""
            for c in categorias.get(str(i), []):
                features.append(1.0 if val == c else 0.0)
        X_rows.append(features)

    X = np.array(X_rows, dtype=np.float64).reshape(len(X_rows), schema["n_features"])
    if label_idx is None or not linhas:
        return X, None, {}

    y_raw = [row[label_idx].strip() for row in linhas]
    unique_labels = sorted(set(y_raw))
    label_map: dict = {}
    if len(unique_labels) == 2:
        for lbl in unique_labels:
            label_map[lbl] = 1 if lbl.lower() in MALIGNANT_KEYWORDS else 0
        if len(set(label_map.values())) == 1:
            label_map = {unique_labels[0]: 0, unique_labels[1]: 1}
    else:
        label_map = {lbl: i for i, lbl in enumerate(unique_labels)}

    y = np.array([label_map[lbl] for lbl in y_raw], dtype=np.int64)
    return X, y, label_map


def extrair_grupos(data: list[list[str]], schema: dict) -> np.ndarray | None:
    """Identificador de sujeito por linha (mesma ordem de `extrair_features`),
    ou None quando a base tem um registro por sujeito / sem identificador."""
    gi = schema.get("grupo_idx")
    if gi is None:
        return None
    brutos = [row[gi].strip() if gi < len(row) else "" for row in _linhas_rotuladas(data, schema)]
    if schema.get("grupo_derivado_de_sufixo"):
        brutos = [_chave_sujeito(v) for v in brutos]
    return np.array(brutos)


def resumo_automl_texto(resultado: dict) -> str:
    """Resumo factual do AutoML para o agente que redige o laudo."""
    if "melhor_modelo" not in resultado:
        return resultado.get("aviso_classificador") or resultado.get("aviso") or (
            "AutoML não executado.")
    melhor = resultado["melhor_modelo"]
    m = resultado["metricas"][melhor]
    linhas = [
        f"Modelo selecionado: {melhor} ({resultado.get('criterio_selecao', '')}).",
        f"Teste ({resultado.get('n_teste')} amostras): acurácia {m['acuracia']}, "
        f"sensibilidade {m['sensibilidade']}, especificidade {m['especificidade']}, "
        f"AUC {m['auc']}, MCC {m['mcc']}, ECE {m['ece']}.",
        f"Protocolo: {resultado.get('protocolo_validacao', {}).get('split_externo', '')}.",
    ]
    if not resultado.get("piso_sensibilidade_atingido", True):
        linhas.append("AVISO: " + resultado["aviso_piso_sensibilidade"])
    return " ".join(linhas)


def analisar_tabular(X: np.ndarray, y: np.ndarray | None, schema: dict) -> dict:
    """Estatísticas descritivas completas das features tabulares brutas (31 métricas científicas)."""
    import scipy.stats as stats

    if X.size == 0:
        return {"n_amostras": 0, "n_features": 0, "features": {}}

    n_amostras = int(X.shape[0])
    n_features = int(X.shape[1])
    feature_names = schema["feature_names"]

    stats_res: dict = {
        "n_amostras": n_amostras,
        "n_features": n_features,
        "features": {},
        "label_name": schema.get("label_name"),
    }

    # Correlação multivariada global (Pearson, Spearman, Covariância) com tratamento de NaN
    if n_features > 1:
        pearson_mat = np.zeros((n_features, n_features))
        spearman_mat = np.zeros((n_features, n_features))
        
        for r in range(n_features):
            for c in range(n_features):
                if r == c:
                    pearson_mat[r, c] = 1.0
                    spearman_mat[r, c] = 1.0
                else:
                    col_r = X[:, r]
                    col_c = X[:, c]
                    valid_mask = ~np.isnan(col_r) & ~np.isnan(col_c)
                    if valid_mask.sum() >= 3:
                        p_coef, _ = stats.pearsonr(col_r[valid_mask], col_c[valid_mask])
                        pearson_mat[r, c] = float(p_coef) if not np.isnan(p_coef) else 0.0
                        
                        s_coef, _ = stats.spearmanr(col_r[valid_mask], col_c[valid_mask])
                        spearman_mat[r, c] = float(s_coef) if not np.isnan(s_coef) else 0.0
                    else:
                        pearson_mat[r, c] = 0.0
                        spearman_mat[r, c] = 0.0
        
        try:
            # np.ma.cov lida com arrays mascarados (ignorando NaNs)
            cov_mat = np.ma.cov(np.ma.masked_invalid(X), rowvar=False)
            cov_list = cov_mat.tolist() if isinstance(cov_mat, np.ndarray) else [[float(cov_mat)]]
        except Exception:
            cov_list = []
            
        stats_res["correlacoes"] = {
            "pearson": pearson_mat.tolist(),
            "spearman": spearman_mat.tolist(),
            "covariancia": cov_list
        }
    else:
        stats_res["correlacoes"] = {
            "pearson": [[1.0]],
            "spearman": [[1.0]],
            "covariancia": [[float(np.nanvar(X))]] if n_amostras > 1 else [[0.0]]
        }

    for i, name in enumerate(feature_names):
        col = X[:, i]
        valid_col = col[~np.isnan(col)]
        n_valid = len(valid_col)
        n_missing = int(np.isnan(col).sum())
        
        if n_valid == 0:
            continue
            
        # 1. Medidas de Tendência Central
        media = float(np.nanmean(col))
        mediana = float(np.nanmedian(col))
        try:
            mode_res = stats.mode(valid_col, keepdims=True)
            moda = float(mode_res.mode[0]) if len(mode_res.mode) > 0 else float(valid_col[0])
        except Exception:
            moda = media
            
        # 2. Medidas de Dispersão
        v_min = float(np.nanmin(col))
        v_max = float(np.nanmax(col))
        amplitude = v_max - v_min
        variancia = float(np.nanvar(col)) if n_valid > 1 else 0.0
        desvio = float(np.nanstd(col)) if n_valid > 1 else 0.0
        cv = desvio / (media + 1e-8)
        
        # 3. Medidas de Posição (Quartis, Percentis, Decis)
        q25, q50, q75 = np.nanpercentile(col, [25, 50, 75])
        p10, p90 = np.nanpercentile(col, [10, 90])
        decis = np.nanpercentile(col, range(10, 100, 10)).tolist()
        iqr_val = q75 - q25
        
        # 4. Medidas de Forma
        try:
            skew_val = float(stats.skew(col, nan_policy='omit'))
            kurt_val = float(stats.kurtosis(col, nan_policy='omit'))
        except Exception:
            skew_val = 0.0
            kurt_val = 0.0
            
        # 5. Outliers (Z-score e IQR)
        lim_inf = q25 - 1.5 * iqr_val
        lim_sup = q75 + 1.5 * iqr_val
        outliers_iqr = int(((valid_col < lim_inf) | (valid_col > lim_sup)).sum())
        
        if desvio > 0:
            z_scores = (valid_col - media) / desvio
            outliers_z = int((np.abs(z_scores) > 2.5).sum())
        else:
            outliers_z = 0
            
        # 6. Métricas de Distribuição (SNR, Entropia, Densidade)
        snr = media / (desvio + 1e-8)
        hist_counts, _ = np.histogram(valid_col, bins="auto")
        entropia = float(stats.entropy(hist_counts + 1e-8))
        
        n_bins = len(hist_counts)
        max_entropy = np.log(n_bins) if n_bins > 1 else 1.0
        uniformidade = float(1.0 - (entropia / max_entropy)) if max_entropy > 0 else 1.0
        
        # 7. Estatísticas de Normalidade
        try:
            shapiro_stat, shapiro_p = stats.shapiro(valid_col) if n_valid >= 3 else (0.0, 1.0)
            ks_stat, ks_p = stats.kstest(valid_col, 'norm', args=(media, desvio + 1e-8))
        except Exception:
            shapiro_stat, shapiro_p = 0.0, 1.0
            ks_stat, ks_p = 0.0, 1.0
            
        # 8. Estatísticas por Grupo & Testes de Hipótese (se houver rótulo)
        stats_por_grupo = {}
        testes_hipotese = {}
        if y is not None:
            unique_groups = sorted(set(y.tolist()))
            groups_data = []
            for g in unique_groups:
                g_data = col[y == g]
                g_valid = g_data[~np.isnan(g_data)]
                groups_data.append(g_valid)
                stats_por_grupo[int(g)] = {
                    "media": float(np.nanmean(g_data)) if len(g_valid) > 0 else 0.0,
                    "desvio": float(np.nanstd(g_data)) if len(g_valid) > 0 else 0.0,
                }
            
            # Executa testes estatísticos baseados no número de grupos
            try:
                if len(unique_groups) == 2 and len(groups_data[0]) >= 3 and len(groups_data[1]) >= 3:
                    # Teste t de Student para 2 grupos
                    t_stat, t_p = stats.ttest_ind(groups_data[0], groups_data[1], equal_var=False)
                    testes_hipotese["teste_t"] = {
                        "estatistica": float(t_stat) if not np.isnan(t_stat) else 0.0,
                        "p_valor": float(t_p) if not np.isnan(t_p) else 1.0,
                        "diferenca_significativa": bool(t_p < 0.05) if not np.isnan(t_p) else False
                    }
                elif len(unique_groups) > 2 and all(len(g) >= 3 for g in groups_data):
                    # ANOVA para múltiplos grupos
                    f_stat, f_p = stats.f_oneway(*groups_data)
                    testes_hipotese["anova"] = {
                        "estatistica": float(f_stat) if not np.isnan(f_stat) else 0.0,
                        "p_valor": float(f_p) if not np.isnan(f_p) else 1.0,
                        "diferenca_significativa": bool(f_p < 0.05) if not np.isnan(f_p) else False
                    }
            except Exception:
                pass

        # Compilação final de métricas univariadas da feature
        stats_res["features"][name] = {
            # Tendência Central
            "media": round(media, 4),
            "mediana": round(mediana, 4),
            "moda": round(moda, 4),
            
            # Dispersão
            "min": round(v_min, 4),
            "max": round(v_max, 4),
            "amplitude": round(amplitude, 4),
            "variancia": round(variancia, 4),
            "desvio": round(desvio, 4),
            "coeficiente_variacao": round(cv, 4),
            "iqr": round(iqr_val, 4),
            
            # Posição
            "quartis": [round(float(q25), 4), round(float(q50), 4), round(float(q75), 4)],
            "percentis": {
                "P10": round(float(p10), 4),
                "P25": round(float(q25), 4),
                "P50": round(float(q50), 4),
                "P75": round(float(q75), 4),
                "P90": round(float(p90), 4)
            },
            "decis": [round(float(d), 4) for d in decis],
            
            # Forma
            "assimetria": round(skew_val, 4),
            "curtose": round(kurt_val, 4),
            
            # Outliers
            "outliers_iqr": outliers_iqr,
            "outliers_zscore": outliers_z,
            "boxplot_limites": {
                "lim_inf": round(float(lim_inf), 4),
                "lim_sup": round(float(lim_sup), 4)
            },
            
            # Métricas de Distribuição
            "snr": round(snr, 4),
            "entropia": round(entropia, 4),
            "uniformidade": round(uniformidade, 4),
            
            # Normalidade
            "normalidade": {
                "shapiro": {
                    "estatistica": round(float(shapiro_stat), 4),
                    "p_valor": round(float(shapiro_p), 4),
                    "eh_normal": bool(shapiro_p > 0.05)
                },
                "ks": {
                    "estatistica": round(float(ks_stat), 4),
                    "p_valor": round(float(ks_p), 4),
                    "eh_normal": bool(ks_p > 0.05)
                }
            },
            
            # Estatísticas de Grupo & Testes de Hipótese
            "por_grupo": stats_por_grupo,
            "testes_hipotese": testes_hipotese,
            "n_nulos": n_missing
        }

    if y is not None:
        unique, counts = np.unique(y, return_counts=True)
        stats_res["distribuicao_labels"] = {int(u): int(c) for u, c in zip(unique, counts)}

    return stats_res


def decidir_estrategia_tabular(analise: dict) -> dict:
    """Propõe e justifica estratégias de pré-processamento baseando-se na análise do dado bruto."""
    n_total = analise.get("n_amostras", 0)
    
    # Mapeia se há valores nulos globais e outliers
    tem_nulos = False
    outliers_globais = 0
    shapiro_normais = 0
    n_features = len(analise.get("features", {}))
    
    for fname, fstats in analise.get("features", {}).items():
        if fstats.get("n_nulos", 0) > 0:
            tem_nulos = True
        outliers_globais += fstats.get("outliers_iqr", 0)
        if fstats.get("normalidade", {}).get("shapiro", {}).get("eh_normal"):
            shapiro_normais += 1

    estrategia = {
        "imputacao": "none",
        "escalamento": "standard",
        "justificativas": [],
    }

    if tem_nulos:
        estrategia["imputacao"] = "median"
        estrategia["justificativas"].append(
            "Células vazias ou com caracteres de nulo detectadas -> imputação por mediana, "
            "ajustada só no treino de cada fold."
        )
    else:
        estrategia["justificativas"].append(
            "Nenhum valor nulo ou vazio detectado na base de dados -> Imputação desnecessária."
        )

    # Regra fixa (não decidida por LLM): RobustScaler se > 8% das células forem outliers
    # IQR ou se menos de metade das features passar no Shapiro-Wilk (p > 0.05).
    pct_outliers = (outliers_globais / (n_total * n_features + 1e-8))
    tamanho_insuficiente = (shapiro_normais / (n_features + 1e-8)) < 0.5
    
    if pct_outliers > 0.08 or tamanho_insuficiente:
        estrategia["escalamento"] = "robust"
        estrategia["justificativas"].append(
            f"Taxa acumulada de outliers ({pct_outliers:.1%}) ou comportamento não-gaussiano dominante -> Aplicado RobustScaler para mitigar distorções."
        )
    else:
        estrategia["escalamento"] = "standard"
        estrategia["justificativas"].append(
            f"Distribuição de features regular com baixa taxa de outliers ({pct_outliers:.1%}) -> Aplicado StandardScaler padrão."
        )

    return estrategia


def preprocessar_tabular_amostras(X: np.ndarray, estrategia: dict) -> np.ndarray:
    """Imputação na base inteira — SOMENTE para estatística descritiva. Não
    usar como entrada de treino: o imputer veria o conjunto de teste. O treino
    imputa dentro de cada fold (ver `avaliacao_modelos.montar_pipeline`)."""
    from sklearn.impute import SimpleImputer
    
    X_preproc = X.copy()
    if X_preproc.size > 0:
        if estrategia.get("imputacao") == "median" and np.isnan(X_preproc).any():
            imputer = SimpleImputer(strategy="median")
            X_preproc = imputer.fit_transform(X_preproc)
        elif np.isnan(X_preproc).any():
            # Fallback de segurança se houver nulos perdidos mas imputacao == "none"
            imputer = SimpleImputer(strategy="mean")
            X_preproc = imputer.fit_transform(X_preproc)
            
    return X_preproc
