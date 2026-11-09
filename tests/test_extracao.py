import numpy as np

from biostatusia.pipeline.extracao import extrair_glcm


def test_entropia_e_da_glcm_e_histograma_fica_separado():
    rng = np.random.default_rng(0)
    img = (rng.random((64, 64)) * 255).astype(np.uint8)
    r = extrair_glcm(img)
    assert r["entropia"] != r["entropia_histograma"]
    assert r["entropia"] > r["entropia_histograma"]


def test_imagem_constante_tem_entropia_zero():
    r = extrair_glcm(np.full((32, 32), 100, np.uint8))
    assert r["entropia"] == 0.0 and r["entropia_histograma"] == 0.0
    assert r["homogeneidade"] == 1.0


def test_normalizacao_minmax_usa_faixa_da_imagem(tmp_path):
    import cv2
    from biostatusia.pipeline.preprocessamento import preprocessar_adaptativo
    img = np.tile(np.linspace(50, 150, 64, dtype=np.uint8), (64, 1))
    p = tmp_path / "x.png"
    cv2.imwrite(str(p), img)
    out = preprocessar_adaptativo(str(p), {"normalizacao": "minmax", "redimensionar": False})
    assert out.min() == 0.0 and abs(out.max() - 1.0) < 1e-6
