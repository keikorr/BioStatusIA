import numpy as np

from biostatusia.pipeline.dados_tabulares import detectar_schema, extrair_features, extrair_grupos


def _stroke_like():
    header = ["id", "gender", "age", "bmi", "smoking_status", "stroke"]
    data = []
    for i in range(80):
        data.append([str(1000 + i), ["Male", "Female"][i % 2], str(30 + i % 40),
                     "N/A" if i % 9 == 1 else f"{22 + i % 10}.5",
                     ["never smoked", "formerly smoked", "Unknown"][i % 3], str(int(i % 6 == 0))])
    return header, data


def test_coluna_com_na_textual_continua_numerica():
    header, data = _stroke_like()
    sc = detectar_schema(header, data)
    assert "bmi" in sc["feature_names"]
    X, y, _ = extrair_features(data, sc)
    assert np.isnan(X[:, sc["feature_names"].index("bmi")]).sum() == sum(r[3] == "N/A" for r in data)


def test_identificador_nao_entra_como_feature():
    header, data = _stroke_like()
    sc = detectar_schema(header, data)
    assert "id" not in sc["feature_names"]
    assert sc["colunas_identificadoras"] == ["id"]
    assert sc["coluna_grupo"] is None


def test_categoricas_em_one_hot():
    header, data = _stroke_like()
    sc = detectar_schema(header, data)
    assert "gender=Female" in sc["feature_names"]
    X, _, _ = extrair_features(data, sc)
    assert X.shape == (80, sc["n_features"])


def test_grupo_derivado_do_nome_do_registro():
    header = ["name", "jitter", "status"]
    data = [[f"phon_R01_S{i // 6:02d}_{i % 6 + 1}", str(i * 0.01), str(i // 6 % 2)] for i in range(60)]
    sc = detectar_schema(header, data)
    grupos = extrair_grupos(data, sc)
    assert sc["coluna_grupo"] == "name"
    assert len(set(grupos)) == 10
