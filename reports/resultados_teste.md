# Resultados dos Testes da Plataforma BioStatusIA (Execução Direta)

## 1. Teste de Imagens (Câncer de Mama Dummy)
### Analisando Base (Engenheiro PDI)
```
Análise concluída em 1 imagens.
- Intensidade média: 9.73 (desvio 0.0)
- Outliers (IQR): 0
- Normalidade (Shapiro p): None (normal=None)
- Contraste médio: 48.85
- Ruído estimado: 0.0
- Tamanhos consistentes: True

Estratégia escolhida:
- Denoising: gaussian
- Normalização: minmax
- Equalização: none
- Tamanho-alvo: [256, 256]

Resultado completo persistido em analise_base.json.
```
### Extraindo Biomarcadores (Analista Técnico)
```
Extração concluída em 1 imagens (BENIGNO=0, MALIGNO=0, INDEFINIDO=1).
Estratégia aplicada: denoising=gaussian, normalização=minmax, equalização=none.

Exemplo (primeira imagem):
- Morfologia: solidez=1.0, circularidade=0.7854
- Textura: entropia=0.3308, homogeneidade=0.9918
- Intensidade: SNR=0.2038

Dataset completo persistido em biomarcadores.json.
```
### Treinando Classificador (Cientista de Dados)
```
Treino não executado: 0 amostras rotuladas, 0 classes (mínimo: 10 amostras, 2 classes).
```

---
## 2. Teste Tabular (WBCD-50 CSV)
### Análise Tabular
```
# Resumo Tabular: wbcd_50.csv

- **Amostras**: 50
- **Features numéricas**: 30
- **Coluna-rótulo**: `diagnosis`
- **Mapa de rótulos**: B→0, M→1
- **Distribuição de classes**: classe 0: 25, classe 1: 25

## Top 10 Features (estatísticas)

| Feature | Média | Mediana | Desvio | Min | Max |
|---|---|---|---|---|---|
| mean radius | 15.3216 | 14.455 | 3.8995 | 8.598 | 25.73 |
| mean texture | 19.8366 | 19.725 | 4.268 | 10.72 | 33.81 |
| mean perimeter | 100.5396 | 94.355 | 27.3766 | 54.66 | 174.2 |
| mean area | 770.634 | 648.25 | 389.8206 | 221.8 | 2010.0 |
| mean smoothness | 0.099 | 0.0992 | 0.0139 | 0.0696 | 0.1243 |
| mean compactness | 0.1213 | 0.1177 | 0.0607 | 0.0321 | 0.2832 |
| mean concavity | 0.1136 | 0.0897 | 0.094 | 0.005 | 0.3514 |
| mean concave points | 0.0621 | 0.0528 | 0.0478 | 0.0051 | 0.1913 |
| mean symmetry | 0.1901 | 0.1847 | 0.0271 | 0.1337 | 0.254 |
| mean fractal dimension | 0.0629 | 0.0616 | 0.0059 | 0.0532 | 0.0763 |

_(+20 features omitidas no resumo)_
```

---
## 3. Teste de Sinal (ECG Dummy)
### Extração de Sinal Temporal (Analista Sinais Fisiológicos)
```
Sinais temporais processados: 1/1 arquivos.
Tipo detectado: Sinal/MATLAB
Erros: 0
Exemplo (1º arquivo):
  - RMS: 0.708217
  - Freq. dominante: 12.0 Hz
  - Desvio: 0.708215

Resultado completo persistido em biomarcadores_temporal.json.
```

---
