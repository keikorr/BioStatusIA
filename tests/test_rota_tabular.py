"""Rota tabular: o AutoML roda antes do laudo e o laudo recebe os números reais."""
import sys
import types

import pytest

flask = pytest.importorskip("flask")


class _CrewFalsa:
    recebido: dict = {}

    def crew(self):
        return self

    def kickoff(self, inputs):
        _CrewFalsa.recebido = inputs
        return "laudo de teste"


@pytest.fixture
def cliente(tmp_path, monkeypatch):
    falso = types.ModuleType("biostatusia.crew")
    for nome in ("BioStatusIACrew", "BioStatusIACrewTabular", "BioStatusIACrewSinal",
                 "BioStatusIACrewImagem3D", "BioStatusIACrewVideo", "BioStatusIACrewInterativo"):
        setattr(falso, nome, _CrewFalsa)
    monkeypatch.setitem(sys.modules, "biostatusia.crew", falso)

    import biostatusia.database as db
    from biostatusia.pipeline import classificador
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "t.db")
    monkeypatch.setattr(classificador, "MODEL_DIR", tmp_path / "models")
    capturado = {}
    monkeypatch.setattr(db, "salvar", lambda *a, **k: 1)

    def _salvar_resultado(**kw):
        capturado.update(kw)
        return 1
    monkeypatch.setattr(db, "salvar_resultado", _salvar_resultado)

    from biostatusia.app import app
    app.config["TESTING"] = True
    return app.test_client(), capturado


def test_laudo_tabular_recebe_resultado_do_automl(cliente, tmp_path):
    client, capturado = cliente
    linhas = ["id,idade,pressao,outcome"]
    for i in range(80):
        linhas.append(f"{i},{30 + i % 40},{'N/A' if i % 11 == 0 else 110 + (i % 2) * 25},{i % 2}")
    csv = tmp_path / "base.csv"
    csv.write_text("\n".join(linhas))
    resp = client.post("/analisar", data={"caminho_manual": str(csv)})
    assert resp.status_code == 302
    dados = capturado["pipeline_data"]
    assert "id" not in dados["schema_tabular"]["feature_names"]
    assert dados["melhor_modelo"] in dados["metricas"]
    assert dados["melhor_modelo"] in _CrewFalsa.recebido["resumo_automl"]
    assert not (tmp_path / "models").exists()
