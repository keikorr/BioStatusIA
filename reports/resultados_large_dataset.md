# Resultados - Base de Imagens Completa (Kaggle)

Dataset localizado em: `C:\Users\Braudel\.cache\kagglehub\datasets\aryashah2k\breast-ultrasound-images-dataset\versions\1\Dataset_BUSI_with_GT`

### Analisando Base (Engenheiro PDI)
```
Análise concluída em 780 imagens.
- Intensidade média: 83.63 (desvio 21.34)
- Outliers (IQR): 1
- Normalidade (Shapiro p): 0.0207 (normal=False)
- Contraste médio: 51.53
- Ruído estimado: 0.0
- Tamanhos consistentes: False

Estratégia escolhida:
- Denoising: gaussian
- Normalização: minmax
- Equalização: none
- Tamanho-alvo: [256, 256]

Resultado completo persistido em analise_base.json.
```
### Extraindo Biomarcadores (Analista Técnico)
```
Extração concluída em 780 imagens (BENIGNO=570, MALIGNO=210, INDEFINIDO=0).
Estratégia aplicada: denoising=gaussian, normalização=minmax, equalização=none.

Exemplo (primeira imagem):
- Morfologia: solidez=0.86, circularidade=0.0302
- Textura: entropia=7.6359, homogeneidade=0.336
- Intensidade: SNR=2.3674

Dataset completo persistido em biomarcadores.json.
```
### Treinando Classificador (AutoML)
```
Treino concluído sobre 780 amostras (test_size=0.2).

Melhor modelo: **RandomForest** (selecionado por maior AUC-ROC).

| Modelo | Acurácia | Precisão | Recall | F1 | AUC |
|---|---|---|---|---|---|
| LogisticRegression | 0.7436 | 0.75 | 0.0714 | 0.1304 | 0.7684 |
| KNN | 0.7756 | 0.6296 | 0.4048 | 0.4928 | 0.7635 |
| SVM | 0.7756 | 1.0 | 0.1667 | 0.2857 | 0.7444 |
| RandomForest | 0.8141 | 0.76 | 0.4524 | 0.5672 | 0.7998 |
| GradientBoosting | 0.75 | 0.5556 | 0.3571 | 0.4348 | 0.7558 |
| MLP | 0.7308 | 0.5 | 0.5476 | 0.5227 | 0.713 |

Resultado completo persistido em metricas.json.
```
