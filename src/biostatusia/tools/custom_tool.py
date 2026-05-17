from pydantic import BaseModel, Field
from crewai.tools import BaseTool

from biostatusia.pipeline.extracao import extrair_todos


class AnaliseImagemInput(BaseModel):
    caminho_imagem: str = Field(..., description="Caminho completo ou URL da imagem para análise.")


class FerramentaAnaliseImagem(BaseTool):
    name: str = "ferramenta_analise_imagem"
    description: str = "Realiza extração profunda de biomarcadores matemáticos de imagens de ultrassom."
    args_schema: type[BaseModel] = AnaliseImagemInput

    def _run(self, caminho_imagem: str) -> str:
        caminho_limpo = caminho_imagem.strip("'\"")
        res = extrair_todos(caminho_limpo)
        if not res:
            return "Erro: Falha ao processar a imagem. Verifique o caminho ou formato."
        return str(res)
