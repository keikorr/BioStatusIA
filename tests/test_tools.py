"""Tier 3 — contrato de comunicação por filesystem das tools (sem LLM/Ollama).

As tools são wrappers puros sobre o pipeline: executam a etapa e persistem um JSON
na pasta do run. O agente seguinte lê esse JSON. Aqui validamos que a cadeia de
imagem grava os 3 artefatos esperados e que a tool tabular retorna um resumo.
"""
import json

import pytest

pytest.importorskip("crewai")


def test_cadeia_imagem_grava_artefatos(raiz, tmp_path):
    from biostatusia.tools.analise_base_tool import FerramentaAnaliseBase
    from biostatusia.tools.extracao_tool import FerramentaExtrairBiomarcadores
    from biostatusia.tools.treino_tool import FerramentaTreinarClassificador

    ds = str(raiz / "dataset_teste_busi")
    run = str(tmp_path)

    FerramentaAnaliseBase()._run(ds, run)
    assert (tmp_path / "analise_base.json").exists()

    FerramentaExtrairBiomarcadores()._run(ds, run)
    assert (tmp_path / "biomarcadores.json").exists()

    FerramentaTreinarClassificador()._run(run)
    metr_path = tmp_path / "metricas.json"
    assert metr_path.exists()
    metr = json.loads(metr_path.read_text(encoding="utf-8"))
    # Mini-BUSI tem >=10 amostras rotuladas → deve treinar e escolher um vencedor
    assert "metricas" in metr and metr.get("melhor_modelo")


def test_ferramenta_tabular_retorna_resumo(raiz):
    from biostatusia.tools.tabular_tool import FerramentaAnaliseTabular
    out = FerramentaAnaliseTabular()._run(str(raiz / "dataset_teste_csv" / "wbcd_50.csv"))
    assert isinstance(out, str) and len(out) > 0
