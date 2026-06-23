"""Tool CrewAI — F5: Extração de Biomarcadores de Vídeo Médico."""
import json
from pathlib import Path

from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class VideoMedicoInput(BaseModel):
    caminho_dataset: str = Field(..., description="Caminho do arquivo de vídeo ou pasta com vídeos médicos.")
    pasta_run: str = Field(..., description="Pasta de workspace para persistir JSONs.")


class FerramentaExtrairVideo(BaseTool):
    name: str = "ferramenta_extrair_video_medico"
    description: str = (
        "Carrega vídeos médicos (Endoscopia, Ultrassom dinâmico) nos formatos "
        ".mp4, .avi, .mov e extrai biomarcadores: variação temporal, motion index, "
        "textura do frame-chave (GLCM, entropia), detecção de frames de alta mudança. "
        "Persiste resultado em JSON."
    )
    args_schema: type[BaseModel] = VideoMedicoInput

    def _run(self, caminho_dataset: str, pasta_run: str) -> str:
        from biostatusia.pipeline.io_utils import listar_sinais, eh_video
        from biostatusia.pipeline.extracao_video import extrair_lote_video

        base = Path(caminho_dataset.strip("'\""))
        pasta = Path(pasta_run.strip("'\""))
        pasta.mkdir(parents=True, exist_ok=True)

        arquivos = listar_sinais(base, eh_video)
        if not arquivos and base.is_file() and eh_video(base):
            arquivos = [{"caminho": str(base), "label": None, "categoria": "INDEFINIDO"}]
        if not arquivos:
            return "Erro: nenhum vídeo médico encontrado (suporte: .mp4, .avi, .mov)."

        resultados = extrair_lote_video(arquivos)
        ok = [r for r in resultados if "biomarcadores" in r]
        erros = [r for r in resultados if "erro" in r]

        metricas_clf: dict = {}
        rotulados = [r for r in ok if r.get("label") is not None]
        if len(rotulados) >= 10:
            import numpy as np
            from biostatusia.tools.sinais_temporais_tool import _vetorizar
            from biostatusia.pipeline.avaliacao_modelos import avaliar_modelos
            X = _vetorizar(rotulados)
            y = np.array([r["label"] for r in rotulados])
            metricas_clf = avaliar_modelos(X, y, familia="F5")

        payload = {
            "familia": "F5",
            "tipo": ok[0].get("tipo", "Vídeo Médico") if ok else "Vídeo Médico",
            "n_arquivos": len(arquivos),
            "n_processados": len(ok),
            "n_erros": len(erros),
            "biomarcadores": ok,
        }
        if metricas_clf:
            payload.update({
                "metricas": metricas_clf.get("metricas", {}),
                "roc_data": metricas_clf.get("roc_data", {}),
                "confusion_matrix": metricas_clf.get("confusion_matrix", {}),
                "melhor_modelo": metricas_clf.get("melhor_modelo", "N/A"),
            })

        with open(pasta / "biomarcadores_video.json", "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)

        resumo = (
            f"Vídeos médicos processados: {len(ok)}/{len(arquivos)}.\n"
            f"Tipo: {payload['tipo']}\nErros: {len(erros)}\n"
        )
        if ok:
            bio0 = ok[0]["biomarcadores"]
            tmp = bio0.get("temporal_video", {})
            mov = bio0.get("movimento", {})
            tex = bio0.get("textura_keyframe", {})
            resumo += (
                f"Exemplo (1º vídeo):\n"
                f"  - Frames: {tmp.get('n_frames', 'N/A')} @ {tmp.get('fps', 'N/A')} fps\n"
                f"  - Motion index: {mov.get('motion_index_medio', 'N/A')}\n"
                f"  - Entropia keyframe: {tex.get('entropia', 'N/A')}\n"
                f"  - Frames alta variação (%): {mov.get('frames_alta_variacao_pct', 'N/A')}\n"
            )
        resumo += "\nResultado persistido em biomarcadores_video.json."
        return resumo
