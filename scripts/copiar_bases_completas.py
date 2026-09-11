#!/usr/bin/env python
"""
Copia todas as bases de dados completas do cache do kagglehub para dataset_kaggle_reais/.
Garante que todas as imagens (BUSI, Brain Tumor, COVID-19, Brain Oncology)
e todos os arquivos de sinais (MIT-BIH e PTB) estejam 100% presentes no projeto.
"""
import shutil
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CACHE = Path.home() / ".cache" / "kagglehub" / "datasets"
DESTINO = BASE_DIR / "dataset_kaggle_reais"

def copiar_pasta_com_progresso(origem: Path, destino: Path, descricao: str):
    print(f"\n[+] Copiando {descricao}...")
    print(f"    Origem:  {origem}")
    print(f"    Destino: {destino}")
    
    if not origem.exists():
        print(f"    [ERRO] Diretório de origem não encontrado: {origem}")
        return False
        
    destino.mkdir(parents=True, exist_ok=True)
    
    t0 = time.time()
    n_copiados = 0
    total_bytes = 0
    
    # Copia recursiva
    for item in origem.rglob("*"):
        if item.is_file():
            rel_path = item.relative_to(origem)
            dest_file = destino / rel_path
            dest_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Copia se não existir ou se tamanho for diferente
            if not dest_file.exists() or dest_file.stat().st_size != item.stat().st_size:
                shutil.copy2(item, dest_file)
            
            n_copiados += 1
            total_bytes += item.stat().st_size
            
            if n_copiados % 5000 == 0:
                print(f"    ... {n_copiados} arquivos transferidos...")
                
    duracao = time.time() - t0
    mb = total_bytes / (1024 * 1024)
    print(f"    [OK] {n_copiados} arquivos ({mb:.2f} MB) sincronizados em {duracao:.1f}s.")
    return True

def main():
    print("=" * 75)
    print("  SINCRONIZAÇÃO COMPLETA DOS DATASETS REAIS -> dataset_kaggle_reais/")
    print("=" * 75)
    
    # 1. BUSI Breast Ultrasound
    busi_src = CACHE / "aryashah2k/breast-ultrasound-images-dataset/versions/1/Dataset_BUSI_with_GT"
    busi_dst = DESTINO / "02_BUSI_Breast_Ultrasound_Real"
    copiar_pasta_com_progresso(busi_src, busi_dst, "02_BUSI_Breast_Ultrasound_Real (Completo)")
    
    # 2. MIT-BIH & PTB ECG Signals
    ecg_src = CACHE / "shayanfazeli/heartbeat/versions/1"
    ecg_dst = DESTINO / "03_MITBIH_PTB_ECG_Signals_Real"
    copiar_pasta_com_progresso(ecg_src, ecg_dst, "03_MITBIH_PTB_ECG_Signals_Real (Completo)")
    # Mantém dataset.csv apontando para o teste ou cria se não existir
    if not (ecg_dst / "dataset.csv").exists() and (ecg_dst / "mitbih_test.csv").exists():
        shutil.copy2(ecg_dst / "mitbih_test.csv", ecg_dst / "dataset.csv")

    # 3. Brain Tumor MRI
    bt_src = CACHE / "masoudnickparvar/brain-tumor-mri-dataset/versions/2"
    bt_dst = DESTINO / "06_Brain_Tumor_MRI_Real"
    copiar_pasta_com_progresso(bt_src, bt_dst, "06_Brain_Tumor_MRI_Real (Completo)")

    # 4. COVID-19 Chest X-Ray
    covid_src = CACHE / "tawsifurrahman/covid19-radiography-database/versions/5/COVID-19_Radiography_Dataset"
    covid_dst = DESTINO / "07_COVID19_ChestXRay_Real"
    copiar_pasta_com_progresso(covid_src, covid_dst, "07_COVID19_ChestXRay_Real (Completo)")

    # 5. Brain MRI Oncology
    onco_src = CACHE / "navoneel/brain-mri-images-for-brain-tumor-detection/versions/1/brain_tumor_dataset"
    onco_dst = DESTINO / "08_Brain_MRI_Oncology_Real"
    copiar_pasta_com_progresso(onco_src, onco_dst, "08_Brain_MRI_Oncology_Real (Completo)")

    print("\n" + "=" * 75)
    print("  SINCRONIZAÇÃO DE TODAS AS BASES FINALIZADA COM SUCESSO!")
    print("=" * 75)

if __name__ == "__main__":
    main()
