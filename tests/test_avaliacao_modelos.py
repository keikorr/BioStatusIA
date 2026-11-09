import numpy as np
import pytest
from sklearn.model_selection import train_test_split

from biostatusia.pipeline.avaliacao_modelos import (
    _resumo, _split_externo, avaliar_e_treinar, calcular_ece,
    calcular_metricas_classificacao, selecionar_melhor_modelo,
)


def test_conjunto_de_teste_nao_influencia_a_selecao(dados_binarios):
    X, y = dados_binarios
    r1, _ = avaliar_e_treinar(X, y)
    _, te = train_test_split(np.arange(len(y)), test_size=0.2, random_state=42, stratify=y)
    X2 = X.copy()
    X2[te] = np.random.default_rng(9).normal(size=X2[te].shape)  # troca só o teste
    r2, _ = avaliar_e_treinar(X2, y)
    assert r1["melhor_modelo"] == r2["melhor_modelo"]
    assert r1["metricas_cv"] == r2["metricas_cv"]
    assert r1["metricas"] != r2["metricas"]


def test_imputacao_ajustada_so_no_treino(dados_binarios):
    X, y = dados_binarios
    X = X.copy()
    X[::5, 0] = np.nan
    X[np.argmax(X[:, 1]), 1] = 1e6  # valor extremo
    r, treinados = avaliar_e_treinar(X, y)
    tr, _ = train_test_split(np.arange(len(y)), test_size=0.2, random_state=42, stratify=y)
    imputer = treinados["LogisticRegression"].named_steps["imputacao"]
    np.testing.assert_allclose(imputer.statistics_, np.nanmedian(X[tr], axis=0))


def test_piso_de_sensibilidade_nao_atingido_e_sinalizado():
    medias = {n: {"auc": 0.8, "acuracia": 0.8, "sensibilidade": 0.5, "mcc": 0.3,
                  "ece": 0.1, "score_clinico": s} for n, s in (("A", 0.4), ("B", 0.5))}
    sel = selecionar_melhor_modelo(medias)
    assert sel["piso_sensibilidade_atingido"] is False
    assert sel["melhor_modelo"] == "B"
    assert "não" in sel["aviso_piso_sensibilidade"].lower()


def test_piso_de_sensibilidade_e_rigido():
    medias = {
        "alto_score": {"auc": 0.95, "acuracia": 0.9, "sensibilidade": 0.70, "mcc": 0.8, "ece": 0.02, "score_clinico": 0.9},
        "elegivel": {"auc": 0.85, "acuracia": 0.8, "sensibilidade": 0.85, "mcc": 0.6, "ece": 0.05, "score_clinico": 0.7},
    }
    sel = selecionar_melhor_modelo(medias)
    assert sel["melhor_modelo"] == "elegivel"
    assert sel["piso_sensibilidade_atingido"] is True
    assert sel["melhor_modelo_convencional"] == "alto_score"
    assert sel["segundo_colocado"] == "alto_score"


def test_ece_conta_probabilidade_igual_a_um():
    y = np.array([0, 0, 1, 1])
    proba = np.array([[0.0, 1.0], [0.0, 1.0], [0.0, 1.0], [0.0, 1.0]])
    assert calcular_ece(y, proba, [0, 1]) == pytest.approx(0.5)


def test_multiclasse_devolve_recall_por_classe():
    from sklearn.datasets import make_classification
    X, y = make_classification(n_samples=180, n_features=6, n_informative=4, n_classes=3,
                               random_state=1)
    r, _ = avaliar_e_treinar(X, y)
    m = r["metricas"][r["melhor_modelo"]]
    assert len(m["recall_por_classe"]) == 3
    assert m["sensibilidade"] == pytest.approx(np.mean(m["recall_por_classe"]), abs=1e-3)
    assert r["roc_data"] == {}


def test_split_por_grupo_nao_mistura_sujeitos(dados_binarios):
    X, y = dados_binarios
    grupos = np.repeat(np.arange(30), 5)
    tr, te, protocolo = _split_externo(X, y, grupos)
    assert set(grupos[tr]).isdisjoint(set(grupos[te]))
    assert "sujeito" in protocolo


def test_desvio_amostral_usa_ddof_1():
    assert _resumo([1.0, 2.0, 3.0])["desvio"] == pytest.approx(1.0)


def test_metricas_binarias_conferem_com_contagens():
    y = np.array([1] * 10 + [0] * 10)
    pred = np.array([1] * 8 + [0] * 2 + [1] * 3 + [0] * 7)
    m = calcular_metricas_classificacao(y, pred, None, [0, 1])
    assert m["sensibilidade"] == 0.8 and m["especificidade"] == 0.7
    assert m["precisao"] == pytest.approx(8 / 11, abs=1e-4)
    assert m["vpn"] == pytest.approx(7 / 9, abs=1e-4)


def test_resultado_e_serializavel(dados_binarios):
    import json
    X, y = dados_binarios
    r, _ = avaliar_e_treinar(X, y)
    json.dumps(r)
    assert r["comparacao_ab"]["modelo_b"] == r["melhor_modelo"]
    assert r["comparacao_ab"]["modelo_a"] == r["segundo_colocado"]
