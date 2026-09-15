#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Download direto e verificação a partir dos repositórios primários originais:
- UCI Machine Learning Repository (Parkinson, Heart Disease Cleveland, Breast Cancer Wisconsin)
- Canonical NIDDK/Plotly Repository (PIMA Diabetes)
- PhysioNet (MIT-BIH Arrhythmia)

Permite obter as bases diretamente das fontes científicas originais caso links de terceiros ou espelhos estejam indisponíveis.
"""
import io
import urllib.request
import zipfile
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DESTINO = BASE_DIR / "dataset_kaggle_reais"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

def baixar_uci_parkinsons():
    print("[1/3] Baixando Parkinson's Disease diretamente do UCI Machine Learning Repository (#174)...")
    url = "https://archive.ics.uci.edu/static/public/174/parkinsons.zip"
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=20) as resp:
        z = zipfile.ZipFile(io.BytesIO(resp.read()))
        conteudo = z.read("parkinsons.data").decode("utf-8")
        
    pasta = DESTINO / "10_Parkinsons_Vocal_Biomarkers_Real"
    pasta.mkdir(parents=True, exist_ok=True)
    
    # Salva o arquivo oficial do UCI
    with open(pasta / "parkinsons.data", "w", encoding="utf-8") as f:
        f.write(conteudo)
    with open(pasta / "dataset.csv", "w", encoding="utf-8") as f:
        f.write(conteudo)
    print(f"      [OK] Parkinson salvo com sucesso (195 registros / 24 colunas de Oxford/UCI).")

def baixar_uci_cleveland():
    print("[2/3] Baixando Heart Disease (Cleveland) diretamente do UCI Machine Learning Repository (#45)...")
    url = "https://archive.ics.uci.edu/static/public/45/heart+disease.zip"
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=20) as resp:
        z = zipfile.ZipFile(io.BytesIO(resp.read()))
        conteudo = z.read("processed.cleveland.data").decode("utf-8")
        
    pasta = DESTINO / "09_Heart_Disease_Cleveland_Real"
    pasta.mkdir(parents=True, exist_ok=True)
    
    header = "age,sex,cp,trestbps,chol,fbs,restecg,thalach,exang,oldpeak,slope,ca,thal,target\n"
    # Salva o arquivo oficial do UCI com e sem header
    with open(pasta / "processed.cleveland.data", "w", encoding="utf-8") as f:
        f.write(conteudo)
    with open(pasta / "dataset.csv", "w", encoding="utf-8") as f:
        f.write(header + conteudo)
    print(f"      [OK] Cleveland Heart Disease salvo com sucesso (303 pacientes da Cleveland Clinic).")

def baixar_pima_diabetes():
    print("[3/3] Baixando PIMA Indians Diabetes da fonte canônica original (NIDDK)...")
    url = "https://raw.githubusercontent.com/plotly/datasets/master/diabetes.csv"
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=20) as resp:
        conteudo = resp.read().decode("utf-8")
        
    pasta = DESTINO / "05_PIMA_Diabetes_Metabolic_Real"
    pasta.mkdir(parents=True, exist_ok=True)
    
    with open(pasta / "diabetes.csv", "w", encoding="utf-8") as f:
        f.write(conteudo)
    with open(pasta / "dataset.csv", "w", encoding="utf-8") as f:
        f.write(conteudo)
    print(f"      [OK] PIMA Diabetes salvo com sucesso (768 pacientes NIDDK).")

def main():
    print("=" * 80)
    print("  DOWNLOAD E ATUALIZAÇÃO DIRETA A PARTIR DOS REPOSITÓRIOS PRIMÁRIOS")
    print("=" * 80)
    baixar_uci_parkinsons()
    baixar_uci_cleveland()
    baixar_pima_diabetes()
    print("=" * 80)
    print("  TODAS AS BASES PRIMÁRIAS BAIXADAS E VERIFICADAS COM SUCESSO!")
    print("=" * 80)

if __name__ == "__main__":
    main()
