"""
Camada de ingestão com validação estrita (Pydantic) — v3.

Objetivo: antes de acionar qualquer Crew, confirmar que a entrada é legível
pelas bibliotecas oficiais (pydicom / wfdb / mne / nibabel / SimpleITK) e
extrair um cartão de metadados confiável. A detecção deixa de ser puramente
por extensão: cada família tenta uma leitura real de cabeçalho e trata
exceções de forma explícita.

Escopo (F2 áudio e F5 vídeo foram removidos):
  - F1  Sinais Temporais (ECG/EEG/EMG/... — .edf/.bdf/.dat/.hea/.mat/.xml/...)
  - F3  Imagem DICOM 2D (Raio-X, Mamografia — .dcm)
  - F4  Volume 3D (TC, RM — .nii/.nii.gz/.mha ou série ≥10 .dcm)
  - TAB Dados tabulares clínicos (.csv/.txt/.tsv)
  - IMG Imagem comum (.png/.jpg/.tif) — mantida para retrocompatibilidade
"""
from __future__ import annotations

from pathlib import Path
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator

from biostatusia.pipeline.io_utils import (
    eh_dicom,
    eh_imagem,
    eh_sinal_temporal,
    eh_tabular,
    eh_volumetrico,
)

Familia = Literal["F1", "F3", "F4", "TAB", "IMG", ""]
Modo = Literal[
    "sinal_temporal", "imagem_dicom_2d", "volume_3d",
    "tabular", "imagem_unica", "imagens_soltas", "dataset_rotulado",
    "multimodal", "multimodal_expandido", "invalido",
]


class MetadadosSinal(BaseModel):
    """Cartão de metadados extraído do cabeçalho pela biblioteca oficial."""
    modalidade: str = ""
    taxa_amostragem_hz: Optional[float] = Field(default=None, ge=0)
    n_canais: Optional[int] = Field(default=None, ge=0)
    canais: list[str] = Field(default_factory=list)
    dimensoes: list[int] = Field(default_factory=list)
    extras: dict = Field(default_factory=dict)


class EntradaValidada(BaseModel):
    """
    Resultado da ingestão validada. `valido=False` bloqueia o acionamento dos
    agentes e devolve `erros` legíveis para a UI.
    """
    caminho: str
    existe: bool
    modo: Modo
    familia: Familia = ""
    tipo: str = ""
    valido: bool = False
    metadados: MetadadosSinal = Field(default_factory=MetadadosSinal)
    erros: list[str] = Field(default_factory=list)

    @field_validator("caminho")
    @classmethod
    def _nao_vazio(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("caminho vazio")
        return v

    @property
    def crew_alvo(self) -> str:
        return {
            "F1": "BioStatusIACrewSinal",
            "F3": "BioStatusIACrewImagem3D",
            "F4": "BioStatusIACrewImagem3D",
            "TAB": "BioStatusIACrewTabular",
            "IMG": "BioStatusIACrew",
        }.get(self.familia, "")


# ── Validadores por família (leitura real de cabeçalho) ───────────────────────

def _validar_dicom(path: Path) -> MetadadosSinal:
    import pydicom

    ds = pydicom.dcmread(str(path), stop_before_pixels=True, force=True)
    modalidade = str(getattr(ds, "Modality", "") or "")
    linhas = int(getattr(ds, "Rows", 0) or 0)
    colunas = int(getattr(ds, "Columns", 0) or 0)
    n_frames = int(getattr(ds, "NumberOfFrames", 1) or 1)
    if not modalidade and not (linhas and colunas):
        raise ValueError("DICOM sem tags mínimas (Modality/Rows/Columns).")
    return MetadadosSinal(
        modalidade=modalidade or "DICOM",
        dimensoes=[linhas, colunas],
        extras={
            "sop_class_uid": str(getattr(ds, "SOPClassUID", "")),
            "n_frames": n_frames,
            "photometric": str(getattr(ds, "PhotometricInterpretation", "")),
        },
    )


def _validar_temporal(path: Path) -> MetadadosSinal:
    ext = path.suffix.lower()

    if ext in {".edf", ".bdf"}:
        import mne
        raw = mne.io.read_raw_edf(str(path), preload=False, verbose="ERROR") \
            if ext == ".edf" else mne.io.read_raw_bdf(str(path), preload=False, verbose="ERROR")
        return MetadadosSinal(
            modalidade="EEG/ECG",
            taxa_amostragem_hz=float(raw.info["sfreq"]),
            n_canais=len(raw.ch_names),
            canais=list(raw.ch_names)[:64],
        )

    if ext in {".dat", ".hea"}:
        import wfdb
        rec = wfdb.rdheader(str(path.with_suffix("")))
        return MetadadosSinal(
            modalidade="PhysioNet",
            taxa_amostragem_hz=float(getattr(rec, "fs", 0.0) or 0.0),
            n_canais=int(getattr(rec, "n_sig", 0) or 0),
            canais=list(getattr(rec, "sig_name", []) or [])[:64],
        )

    if ext == ".mat":
        from scipy.io import loadmat
        m = loadmat(str(path))
        arrays = {k: v for k, v in m.items() if not k.startswith("__")}
        maior = max(arrays.items(), key=lambda kv: getattr(kv[1], "size", 0), default=(None, None))
        dims = list(getattr(maior[1], "shape", ())) if maior[1] is not None else []
        return MetadadosSinal(modalidade="MATLAB", dimensoes=dims,
                              extras={"variaveis": list(arrays.keys())})

    # .xml, .c3d, .set, etc. — validação leve de existência/legibilidade
    if not path.stat().st_size:
        raise ValueError(f"Arquivo de sinal vazio: {path.name}")
    return MetadadosSinal(modalidade="Sinal Temporal")


def _validar_volume(path: Path) -> MetadadosSinal:
    suffixes = [s.lower() for s in path.suffixes]
    if path.suffix.lower() == ".nii" or suffixes == [".nii", ".gz"]:
        import nibabel as nib
        img = nib.load(str(path))
        shape = [int(x) for x in img.shape]
        if len(shape) < 3:
            raise ValueError(f"NIfTI '{path.name}' não é volumétrico (shape {shape}).")
        return MetadadosSinal(modalidade="Volume NIfTI", dimensoes=shape)

    import SimpleITK as sitk
    img = sitk.ReadImage(str(path))
    shape = list(img.GetSize())
    return MetadadosSinal(modalidade="Volume MHA", dimensoes=shape)


# ── Ponto de entrada de arquivo único ─────────────────────────────────────────

def validar_arquivo(caminho: str | Path) -> EntradaValidada:
    """
    Valida um ÚNICO arquivo lendo o cabeçalho com a biblioteca oficial.
    Nunca levanta exceção: falhas viram `valido=False` + `erros`.
    """
    path = Path(caminho)
    base = EntradaValidada(caminho=str(path), existe=path.exists(), modo="invalido")

    if not path.exists() or not path.is_file():
        base.erros.append(f"Arquivo não encontrado: {path}")
        return base

    try:
        if eh_imagem(path):
            base.modo, base.familia, base.tipo, base.valido = "imagem_unica", "IMG", "Imagem", True
        elif eh_tabular(path):
            base.modo, base.familia, base.tipo, base.valido = "tabular", "TAB", "Tabular", True
        elif eh_dicom(path):
            base.metadados = _validar_dicom(path)
            base.modo, base.familia = "imagem_dicom_2d", "F3"
            base.tipo, base.valido = base.metadados.modalidade, True
        elif eh_volumetrico(path):
            base.metadados = _validar_volume(path)
            base.modo, base.familia = "volume_3d", "F4"
            base.tipo, base.valido = base.metadados.modalidade, True
        elif eh_sinal_temporal(path):
            base.metadados = _validar_temporal(path)
            base.modo, base.familia = "sinal_temporal", "F1"
            base.tipo, base.valido = base.metadados.modalidade, True
        else:
            base.erros.append(f"Extensão fora de escopo (F1/F3/F4/TAB/IMG): {path.suffix}")
    except ImportError as e:
        base.erros.append(f"Dependência ausente para {path.suffix}: {e}")
    except Exception as e:  # leitura de cabeçalho falhou — arquivo corrompido/incompatível
        base.erros.append(f"Falha ao validar cabeçalho de {path.name}: {e}")

    return base
