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


def detectar_schema(header: list[str], data: list[list[str]]) -> dict:
    """Identifica coluna-rótulo e colunas numéricas."""
    n_cols = len(header)

    label_idx = None
    for i, name in enumerate(header):
        if name.lower().strip() in LABEL_KEYWORDS:
            label_idx = i
            break

    if label_idx is None and n_cols > 1:
        ultimos = [row[-1].strip() for row in data[:50] if len(row) >= n_cols]
        unicos = set(ultimos)
        if 2 <= len(unicos) <= 10:
            label_idx = n_cols - 1

    numeric_cols: list[int] = []
    for i in range(n_cols):
        if i == label_idx:
            continue
        eh_numerica = True
        amostras_parseadas = 0
        for row in data[:30]:
            if i < len(row) and row[i].strip():
                try:
                    float(row[i].replace(",", "."))
                    amostras_parseadas += 1
                except ValueError:
                    eh_numerica = False
                    break
        if eh_numerica and amostras_parseadas > 0:
            numeric_cols.append(i)

    return {
        "label_idx": label_idx,
        "label_name": header[label_idx] if label_idx is not None else None,
        "feature_indices": numeric_cols,
        "feature_names": [header[i] for i in numeric_cols],
        "n_features": len(numeric_cols),
        "n_amostras": len(data),
    }


def extrair_features(data: list[list[str]], schema: dict) -> tuple[np.ndarray, np.ndarray | None, dict]:
    """Converte data em (X, y, label_map)."""
    feature_idx = schema["feature_indices"]
    label_idx = schema["label_idx"]

    X_rows: list[list[float]] = []
    y_raw: list[str] = []

    for row in data:
        try:
            features = [float(row[i].replace(",", ".")) for i in feature_idx]
        except (ValueError, IndexError):
            continue
        X_rows.append(features)
        if label_idx is not None and label_idx < len(row):
            y_raw.append(row[label_idx].strip())

    X = np.array(X_rows, dtype=np.float64)
    label_map: dict = {}

    if label_idx is None or not y_raw:
        return X, None, label_map

    unique_labels = sorted(set(y_raw))
    if len(unique_labels) == 2:
        for lbl in unique_labels:
            label_map[lbl] = 1 if lbl.lower().strip() in MALIGNANT_KEYWORDS else 0
        if len(set(label_map.values())) == 1:
            label_map = {unique_labels[0]: 0, unique_labels[1]: 1}
    else:
        label_map = {lbl: i for i, lbl in enumerate(unique_labels)}

    y = np.array([label_map[lbl] for lbl in y_raw], dtype=np.int64)
    return X, y, label_map


def analisar_tabular(X: np.ndarray, y: np.ndarray | None, schema: dict) -> dict:
    """Estatísticas descritivas das features tabulares."""
    if X.size == 0:
        return {"n_amostras": 0, "n_features": 0, "features": {}}

    feature_names = schema["feature_names"]
    stats: dict = {
        "n_amostras": int(X.shape[0]),
        "n_features": int(X.shape[1]),
        "features": {},
        "label_name": schema.get("label_name"),
    }

    for i, name in enumerate(feature_names):
        col = X[:, i]
        stats["features"][name] = {
            "media": round(float(col.mean()), 4),
            "mediana": round(float(np.median(col)), 4),
            "desvio": round(float(col.std()), 4),
            "min": round(float(col.min()), 4),
            "max": round(float(col.max()), 4),
        }

    if y is not None:
        unique, counts = np.unique(y, return_counts=True)
        stats["distribuicao_labels"] = {int(u): int(c) for u, c in zip(unique, counts)}

    return stats
