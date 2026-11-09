import json
from pathlib import Path

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from biostatusia.pipeline.classificador import treinar


class TreinoInput(BaseModel):
    pasta_run: str = Field(..., description="Pasta de workspace com biomarcadores.json.")


class FerramentaTreinarClassificador(BaseTool):
    name: str = "ferramenta_treinar_classificador"
    description: str = (
        "Compara 6 classificadores (LR, KNN, SVM, RandomForest, GradientBoosting, MLP) com os "
        "biomarcadores extraídos; seleção por validação cruzada interna com piso de sensibilidade. "
        "Requer dataset rotulado (BENIGNO + MALIGNO, mínimo 10 amostras com 2 classes). "
        "Persiste métricas, ROC e matriz de confusão em metricas.json e retorna resumo."
    )
    args_schema: type[BaseModel] = TreinoInput

    def _run(self, pasta_run: str) -> str:
        pasta = Path(pasta_run.strip("'\""))
        bio_path = pasta / "biomarcadores.json"
        if not bio_path.exists():
            return f"Erro: biomarcadores.json não encontrado em {pasta}. Extraia biomarcadores antes."

        with open(bio_path, "r", encoding="utf-8") as f:
            registros = json.load(f)

        registros_treino = [r for r in registros if r.get("label") is not None]
        labels = {r["label"] for r in registros_treino}

        if len(registros_treino) < 10 or len(labels) < 2:
            msg = (
                f"Treino não executado: {len(registros_treino)} amostras rotuladas, "
                f"{len(labels)} classes (mínimo: 10 amostras, 2 classes)."
            )
            with open(pasta / "metricas.json", "w", encoding="utf-8") as f:
                json.dump({"aviso": msg}, f, indent=2)
            return msg

        try:
            resultado = treinar([
                {"biomarcadores": r["biomarcadores"], "label": r["label"]}
                for r in registros_treino
            ])
        except Exception as e:
            return f"Erro ao treinar: {e}"

        with open(pasta / "metricas.json", "w", encoding="utf-8") as f:
            json.dump(resultado, f, indent=2)

        if "melhor_modelo" not in resultado:
            return resultado.get("aviso", "Treino não executado.")

        melhor = resultado["melhor_modelo"]
        metricas = resultado["metricas"]
        linhas = [
            f"Treino concluído: {resultado['n_treino']} amostras de treino, "
            f"{resultado['n_teste']} de teste (split estratificado 80/20).",
            "",
            f"Modelo selecionado: **{melhor}** — escolhido pelo score interno na validação "
            f"cruzada do treino (AUROC, MCC, ECE e piso de sensibilidade 0,80); o teste não "
            f"participa da escolha.",
        ]
        if not resultado.get("piso_sensibilidade_atingido", True):
            linhas += ["", f"ATENÇÃO: {resultado['aviso_piso_sensibilidade']}"]
        linhas += [
            "",
            "Métricas no conjunto de teste:",
            "",
            "| Modelo | Acurácia | Sensibilidade | Especificidade | AUC | MCC | ECE |",
            "|---|---|---|---|---|---|---|",
        ]
        for nome, m in metricas.items():
            linhas.append(
                f"| {nome} | {m['acuracia']} | {m['sensibilidade']} | {m['especificidade']} | "
                f"{m['auc']} | {m['mcc']} | {m['ece']} |"
            )
        linhas.append("")
        linhas.append("Resultado completo persistido em metricas.json.")
        return "\n".join(linhas)
