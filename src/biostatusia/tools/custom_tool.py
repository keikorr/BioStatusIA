import os
import cv2
import numpy as np
import requests
from io import BytesIO
from PIL import Image
from skimage.feature import graycomatrix, graycoprops
from scipy.stats import skew, kurtosis
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

class MorphologyAnalyzer:
    @staticmethod
    def get_shape_metrics(gray_img):
        # Threshold adaptativo para melhor segmentação em ultrassom
        thresh = cv2.adaptiveThreshold(gray_img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                     cv2.THRESH_BINARY, 11, 2)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return {"circularity": 0, "solidity": 0}
            
        cnt = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(cnt)
        perimeter = cv2.arcLength(cnt, True)
        
        # Cálculo de Circularidade
        if perimeter == 0: 
            circularity = 0
        else:
            circularity = (4 * np.pi * area) / (perimeter**2)
            
        # Cálculo de Solidez (Área / Área do Fecho Convexo)
        hull = cv2.convexHull(cnt)
        hull_area = cv2.contourArea(hull)
        solidity = area / hull_area if hull_area > 0 else 0
        
        return {
            "circularidade": round(float(circularity), 4),
            "solidez": round(float(solidity), 4)
        }

class IntensityAnalyzer:
    @staticmethod
    def get_distribution_metrics(img_array):
        flat_data = img_array.flatten()
        mean_val = np.mean(flat_data)
        std_val = np.std(flat_data)
        
        # SNR (Razão Sinal-Ruído)
        snr = mean_val / (std_val + 1e-8)
        
        # Estatísticas de distribuição (Assimetria e Curtose)
        assimetria = skew(flat_data)
        curtose = kurtosis(flat_data)
        
        return {
            "snr": round(float(snr), 4),
            "assimetria": round(float(assimetria), 4),
            "curtose": round(float(curtose), 4)
        }

class ImageStatsAnalyzer:
    def normalize_image(self, img):
        img = img.astype(np.float32)
        min_val, max_val = img.min(), img.max()
        denom = (max_val - min_val) + 1e-8
        normalized = (img - min_val) / denom
        if len(normalized.shape) == 2:
            normalized = np.stack([normalized]*3, axis=-1)
        return normalized

    def load_image(self, path):
        try:
            if path.startswith("http"):
                headers = {'User-Agent': 'Mozilla/5.0'}
                response = requests.get(path, headers=headers)
                img = Image.open(BytesIO(response.content)).convert('RGB')
            else:
                img = Image.open(path).convert('RGB')
            return self.normalize_image(np.array(img))
        except:
            return None

    def process(self, path):
        img_array = self.load_image(path)
        if img_array is None: return None
        
        img_u8 = (img_array * 255).astype('uint8')
        gray = cv2.cvtColor(img_u8, cv2.COLOR_RGB2GRAY)
        
        # 1. Métricas de Distribuição e Intensidade
        dist = IntensityAnalyzer.get_distribution_metrics(img_array)
        
        # 2. Métricas de Textura (GLCM)
        glcm = graycomatrix(gray, [1], [0], 256, symmetric=True, normed=True)
        contrast = graycoprops(glcm, 'contrast')[0, 0]
        homogeneity = graycoprops(glcm, 'homogeneity')[0, 0]
        energy = graycoprops(glcm, 'energy')[0, 0]
        
        # 3. Entropia (Complexidade)
        hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
        p = hist / (hist.sum() + 1e-10)
        entropy = -np.sum(p * np.log2(p + 1e-10))
        
        # 4. Métricas Morfológicas (Forma)
        shape = MorphologyAnalyzer.get_shape_metrics(gray)
        
        return {
            "morfologia": shape,
            "textura_glcm": {
                "contraste": round(float(contrast), 4),
                "homogeneidade": round(float(homogeneity), 4),
                "energia": round(float(energy), 4),
                "entropia": round(float(entropy), 4)
            },
            "distribuicao_intensidade": dist
        }

# Criamos um esquema para forçar o nome correto do argumento
class AnaliseImagemInput(BaseModel):
    caminho_imagem: str = Field(..., description="O caminho completo ou URL da imagem para análise.")

class FerramentaAnaliseImagem(BaseTool):
    name: str = "ferramenta_analise_imagem"
    description: str = "Realiza extração profunda de biomarcadores matemáticos de imagens de ultrassom."
    # Adicionamos esta linha para vincular o esquema acima
    args_schema: type[BaseModel] = AnaliseImagemInput

    def _run(self, caminho_imagem: str) -> str:
        analyzer = ImageStatsAnalyzer()
        # Limpa possíveis aspas que o LLM possa ter colocado
        caminho_limpo = caminho_imagem.strip("'\"")
        
        res = analyzer.process(caminho_limpo)
        if not res:
            return "Erro: Falha ao processar a imagem. Verifique o caminho ou formato."
        return str(res)