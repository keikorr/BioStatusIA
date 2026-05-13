#!/usr/bin/env python
import os
import sys
import markdown
import webbrowser
import kagglehub
from datetime import datetime

# --- CONFIGURAÇÃO DE CAMINHO (FIREWALL DE ERROS) ---
# Garante que o Python encontre o pacote 'biostatsia' independentemente de onde o script é chamado
base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if base_path not in sys.path:
    sys.path.insert(0, base_path)

from biostatusia.crew import BioStatusIACrew

def run():
    print(f"\n🚀 [BIOSTATSIA] Iniciando Sistema de Laudos Híbridos...")
    
    try:
        # 1. DOWNLOAD E SELEÇÃO DE DADOS
        caminho_dataset = kagglehub.dataset_download("aryashah2k/breast-ultrasound-images-dataset")
        base_exames = os.path.join(caminho_dataset, "Dataset_BUSI_with_GT")
        
        categorias = ["benign", "malignant"]
        lista_final_exames = []

        # Seleciona 3 imagens de cada pasta para garantir diversidade no dossiê
        for cat in categorias:
            pasta = os.path.join(base_exames, cat)
            arquivos = [os.path.join(pasta, f) for f in os.listdir(pasta) 
                       if f.endswith('.png') and 'mask' not in f.lower()][:1]
            lista_final_exames.extend(arquivos)

        laudos_acumulados_html = ""
        data_atual = datetime.now().strftime("%d de %B de %Y")
        id_processo = f"USG-{datetime.now().strftime('%Y%m%d')}-BOS"

        # Corta a lista para ter apenas a primeiríssima imagem
        lista_final_exames = lista_final_exames[:1]
        # 2. LOOP DE PROCESSAMENTO MULTI-AGENTE
        for i, caminho_completo in enumerate(lista_final_exames, 1):
            nome_img = os.path.basename(caminho_completo)
            categoria_atual = "MALIGNO" if "malignant" in caminho_completo else "BENIGNO"
            # Define cores para o Dashboard Moderno
            badge_class = "bg-red-100 text-red-700" if categoria_atual == "MALIGNO" else "bg-green-100 text-green-700"
            
            print(f"[{i}/{len(lista_final_exames)}] Analisando {categoria_atual}: {nome_img}...")
            
            # Executa a Crew (Analista Técnico + Radiologista IA)
            resultado = BioStatusIACrew().crew().kickoff(inputs={'caminho_imagem': caminho_completo})
            
            # Converte o Markdown do agente para HTML
            laudo_html = markdown.markdown(str(resultado))
            
            # Monta o bloco visual usando o estilo do template moderno
            bloco_exame = f"""
            <div class="grid grid-cols-1 md:grid-cols-3 gap-8 items-start border-b border-gray-100 pb-12 mb-12">
                <div class="col-span-1 pr-6">
                    <div class="flex items-center gap-2 mb-4">
                        <span class="px-2 py-1 rounded text-[10px] font-bold uppercase {badge_class}">{categoria_atual}</span>
                        <h3 class="text-xs font-bold text-gray-400">{nome_img}</h3>
                    </div>
                    <img src="file:///{caminho_completo}" class="w-full rounded-lg shadow-sm border border-gray-200">
                </div>
                <div class="col-span-2">
                    <div class="bg-teal-50/50 p-6 rounded-xl border border-teal-100">
                        <h4 class="text-teal-800 font-bold text-sm mb-3">Conclusão dos Agentes (Llama 3.1)</h4>
                        <div class="text-sm text-gray-700 leading-relaxed">
                            {laudo_html}
                        </div>
                    </div>
                </div>
            </div>
            """
            laudos_acumulados_html += bloco_exame

        # 3. GERAÇÃO DOS ARQUIVOS FINAIS
        diretorio_raiz = os.path.abspath(os.path.join(base_path, '..'))
        
        # Definição de templates e saídas[cite: 3]
        tmpl_detalhado = os.path.join(diretorio_raiz, "template_relatorio.html")
        tmpl_moderno = os.path.join(diretorio_raiz, "template_moderno.html")
        
        out_detalhado = os.path.join(diretorio_raiz, "relatorio_tecnico_biostatsia.html")
        out_moderno = os.path.join(diretorio_raiz, "dashboard_inteligencia_medica.html")

        # Gerando Relatório Técnico (Original)
        if os.path.exists(tmpl_detalhado):
            with open(tmpl_detalhado, "r", encoding="utf-8") as f:
                html_t = f.read().replace("{{LAUDO_FINAL_AQUI}}", laudos_acumulados_html)
            with open(out_detalhado, "w", encoding="utf-8") as f:
                f.write(html_t)
            print(f"✅ Relatório Técnico: {out_detalhado}")

        # Gerando Dashboard Moderno (Tailwind)[cite: 3]
        if os.path.exists(tmpl_moderno):
            with open(tmpl_moderno, "r", encoding="utf-8") as f:
                html_m = f.read().replace("{{CONTEUDO_DINAMICO}}", laudos_acumulados_html)
                html_m = html_m.replace("{{ID_PROCESSO}}", id_processo)
                html_m = html_m.replace("{{DATA_ATUAL}}", data_atual)
            with open(out_moderno, "w", encoding="utf-8") as f:
                f.write(html_m)
            print(f"✅ Dashboard Moderno: {out_moderno}")

        # Abre os resultados
        webbrowser.open(f"file://{out_moderno}")

    except Exception as e:
        print(f"❌ Erro crítico no pipeline: {e}")

if __name__ == '__main__':
    run()