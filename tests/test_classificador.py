import numpy as np

from biostatusia.pipeline import classificador


def _bio(v):
    return {"morfologia": {"circularidade": v[0], "solidez": v[1]},
            "textura_glcm": {"contraste": v[2], "homogeneidade": v[3], "energia": v[4], "entropia": v[5]},
            "distribuicao_intensidade": {"snr": v[6], "assimetria": v[7], "curtose": v[8]}}


def test_classificar_usa_o_modelo_vencedor(tmp_path, monkeypatch):
    monkeypatch.setattr(classificador, "MODEL_DIR", tmp_path)
    rng = np.random.default_rng(0)
    registros = []
    for i in range(80):
        lab = i % 2
        registros.append({"biomarcadores": _bio(rng.normal(lab * 2, 1, 9)), "label": lab})
    r = classificador.treinar(registros)
    assert (tmp_path / classificador.ARQUIVO_VENCEDOR).exists()
    cat, prob = classificador.classificar(_bio(np.full(9, 2.0)))
    assert cat == "MALIGNO" and prob > 0.5
    import pickle
    salvo = pickle.load(open(tmp_path / classificador.ARQUIVO_VENCEDOR, "rb"))
    assert salvo["nome"] == r["melhor_modelo"]


def test_persistir_false_nao_grava(tmp_path, monkeypatch):
    monkeypatch.setattr(classificador, "MODEL_DIR", tmp_path)
    X = np.random.default_rng(1).normal(size=(40, 3))
    y = np.array([0, 1] * 20)
    classificador.treinar_vetores(X, y, persistir=False)
    assert not (tmp_path / classificador.ARQUIVO_VENCEDOR).exists()
