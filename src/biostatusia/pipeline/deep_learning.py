"""
Ponto de extensão para Deep Learning — extração de features espaciais via CNN.

Este módulo define o CONTRATO de um extrator profundo sem impor um framework
pesado como dependência obrigatória. A CNN é opcional: se `torch` não estiver
instalado, `cnn_disponivel()` retorna False e o AutoML segue com os
biomarcadores radiômicos clássicos (F3/F4) ou multi-domínio (F1).

Integração pretendida:
  imagem/volume → ExtratorCNN.extrair(...) → vetor de embeddings
                → concatenado aos biomarcadores clássicos
                → avaliacao_modelos.avaliar_modelos(...)

Assim os 6 classificadores clássicos passam a operar sobre features híbridas
(radiômica + CNN) sem alterar o restante do pipeline.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


def cnn_disponivel() -> bool:
    """True se um backend de deep learning (torch) estiver instalado."""
    try:
        import torch  # noqa: F401
        return True
    except ImportError:
        return False


@dataclass
class ConfigCNN:
    arquitetura: str = "resnet18"          # backbone pré-treinado (ImageNet)
    camada_embedding: str = "avgpool"       # camada da qual extrair o vetor
    dim_embedding: int = 512
    tamanho_entrada: tuple[int, int] = (224, 224)
    normalizar_imagenet: bool = True
    dispositivo: str = "cpu"
    extras: dict = field(default_factory=dict)


class ExtratorCNN:
    """
    Extrator de embeddings CNN. A carga do modelo é preguiçosa (lazy) — só ocorre
    quando `extrair` é chamado pela primeira vez, evitando custo quando não usado.
    """

    def __init__(self, config: ConfigCNN | None = None):
        self.config = config or ConfigCNN()
        self._modelo = None

    def _carregar(self):
        if not cnn_disponivel():
            raise ImportError(
                "Backbone CNN requer torch/torchvision. "
                "Instale com: uv add torch torchvision"
            )
        import torch
        import torchvision.models as models

        fabrica = getattr(models, self.config.arquitetura, None)
        if fabrica is None:
            raise ValueError(f"Arquitetura desconhecida: {self.config.arquitetura}")
        rede = fabrica(weights="DEFAULT")
        rede.eval()
        # Remove a cabeça de classificação — mantém apenas o extrator de features.
        if hasattr(rede, "fc"):
            rede.fc = torch.nn.Identity()
        self._modelo = rede.to(self.config.dispositivo)

    def extrair(self, imagens: np.ndarray) -> np.ndarray:
        """
        imagens: (N, H, W) ou (N, H, W, C) float [0,1].
        Retorna (N, dim_embedding). Levanta ImageError clara se sem backend.
        """
        if self._modelo is None:
            self._carregar()
        import torch
        import torch.nn.functional as F

        if imagens.ndim == 3:                       # (N,H,W) → (N,1,H,W)
            imagens = imagens[:, None, :, :]
        elif imagens.ndim == 4 and imagens.shape[-1] in (1, 3):
            imagens = np.transpose(imagens, (0, 3, 1, 2))

        t = torch.as_tensor(imagens, dtype=torch.float32)
        if t.shape[1] == 1:                         # grayscale → 3 canais
            t = t.repeat(1, 3, 1, 1)
        t = F.interpolate(t, size=self.config.tamanho_entrada,
                          mode="bilinear", align_corners=False)
        if self.config.normalizar_imagenet:
            media = torch.tensor([0.485, 0.456, 0.406]).view(1, 3, 1, 1)
            desvio = torch.tensor([0.229, 0.224, 0.225]).view(1, 3, 1, 1)
            t = (t - media) / desvio

        with torch.no_grad():
            emb = self._modelo(t.to(self.config.dispositivo))
        return emb.cpu().numpy().reshape(len(imagens), -1)


def features_hibridas(radiomicas: np.ndarray, embeddings_cnn: np.ndarray | None) -> np.ndarray:
    """Concatena biomarcadores clássicos e embeddings CNN quando disponíveis."""
    if embeddings_cnn is None or embeddings_cnn.size == 0:
        return radiomicas
    return np.hstack([radiomicas, embeddings_cnn])
