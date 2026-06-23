"""Tool CrewAI — F2: Extração de Biomarcadores de Áudio Biomédico."""
import json
from pathlib import Path

from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class AudioBiomedicoInput(BaseModel):
    caminho_dataset: str = Field(..., description="Caminho do arquivo ou pasta com áudios biomédicos.")
    pasta_run: str = Field(..., description="Pasta de workspace para persistir JSONs.")


class FerramentaExtrairAudio(BaseTool):
    name: str = "ferramenta_extrair_audio_biomedico"
    description: str = (
        "Carrega sinais de áudio biomédico (Fonocardiograma, Sons Pulmonares) "
        "nos formatos .wav, .flac, .mp3, .mat e extrai features acústicas "
        "(MFCCs, espectrograma mel, ZCR, RMS, energia por banda). "
        "Persiste resultado em JSON."
    )
    args_schema: type[BaseModel] = AudioBiomedicoInput

    def _run(self, caminho_dataset: str, pasta_run: str) -> str:
        from biostatusia.pipeline.io_utils import listar_sinais, eh_audio_biomedico
        from biostatusia.pipeline.extracao_audio import extrair_lote_audio

        base = Path(caminho_dataset.strip("'\""))
        pasta = Path(pasta_run.strip("'\""))
        pasta.mkdir(parents=True, exist_ok=True)

        arquivos = listar_sinais(base, eh_audio_biomedico)
        if not arquivos and base.is_file() and eh_audio_biomedico(base):
            arquivos = [{"caminho": str(base), "label": None, "categoria": "INDEFINIDO"}]
        if not arquivos:
            return "Erro: nenhum áudio biomédico encontrado no caminho fornecido."

        resultados = extrair_lote_audio(arquivos)
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
            metricas_clf = avaliar_modelos(X, y, familia="F2")

        payload = {
            "familia": "F2",
            "tipo": ok[0].get("tipo", "Áudio Biomédico") if ok else "Áudio Biomédico",
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
                "comparacao_ab": metricas_clf.get("comparacao_ab", {}),
            })

        with open(pasta / "biomarcadores_audio.json", "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)

        resumo = (
            f"Áudios biomédicos processados: {len(ok)}/{len(arquivos)}.\n"
            f"Tipo: {payload['tipo']}\nErros: {len(erros)}\n"
        )
        if ok:
            bio0 = ok[0]["biomarcadores"]
            esp = bio0.get("espectral", {})
            tmp = bio0.get("temporal_audio", {})
            resumo += (
                f"Exemplo (1º arquivo):\n"
                f"  - Centroide espectral: {esp.get('centroide_hz_media', 'N/A')} Hz\n"
                f"  - ZCR médio: {tmp.get('zcr_media', 'N/A')}\n"
                f"  - RMS médio: {tmp.get('rms_media', 'N/A')}\n"
                f"  - MFCCs: {bio0.get('mfcc', {}).get('mfcc_media', [])[:5]}\n"
            )
        if metricas_clf.get("melhor_modelo"):
            m = metricas_clf["metricas"].get(metricas_clf["melhor_modelo"], {})
            resumo += (
                f"\nMelhor modelo: {metricas_clf['melhor_modelo']}\n"
                f"  - AUC: {m.get('auc', 'N/A')} | Sensib.: {m.get('sensibilidade', 'N/A')}\n"
            )
        resumo += "\nResultado persistido em biomarcadores_audio.json."
        return resumo
