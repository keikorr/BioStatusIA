import json
import zipfile
from pathlib import Path

import markdown as md
from flask import Flask, redirect, render_template, request, url_for

from biostatusia.pipeline.io_utils import (
    criar_pasta_run,
    eh_imagem,
    eh_tabular,
    encontrar_csv,
    label_pasta,
    listar_imagens,
)

app = Flask(__name__, template_folder="templates", static_folder="static")
app.config["MAX_CONTENT_LENGTH"] = 500 * 1024 * 1024  # 500 MB

UPLOAD_DIR = Path(__file__).parent / "static" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Detecção de modo
# ---------------------------------------------------------------------------

def detectar_estrutura(caminho: Path) -> str:
    """Retorna: 'imagem_unica' | 'tabular' | 'multimodal' |
                'dataset_rotulado' | 'imagens_soltas' | 'invalido'."""
    if caminho.is_file():
        if eh_imagem(caminho):
            return "imagem_unica"
        if eh_tabular(caminho):
            return "tabular"
        return "invalido"
    if not caminho.is_dir():
        return "invalido"

    tem_tab = False
    tem_img = False
    for arq in caminho.rglob("*"):
        if arq.is_file():
            if eh_tabular(arq):
                tem_tab = True
            elif eh_imagem(arq):
                tem_img = True

    if tem_tab and tem_img:
        return "multimodal"
    if tem_tab:
        return "tabular"

    tem_b = tem_m = False
    for sub in caminho.rglob("*"):
        if sub.is_dir():
            label = label_pasta(sub.name)
            if label == 0:
                tem_b = True
            elif label == 1:
                tem_m = True
    if tem_b and tem_m:
        return "dataset_rotulado"
    if tem_img:
        return "imagens_soltas"
    return "invalido"


# ---------------------------------------------------------------------------
# Leitura dos artefatos JSON persistidos pelos agentes
# ---------------------------------------------------------------------------

def _ler_json(pasta: Path, nome: str) -> dict | list | None:
    arq = pasta / nome
    if not arq.exists():
        return None
    with open(arq, "r", encoding="utf-8") as f:
        return json.load(f)


def _consolidar_imagem(pasta_run: Path, modo: str) -> dict:
    """Lê os JSONs gerados pelos agentes e monta o dict para a Tela 2."""
    analise_base = _ler_json(pasta_run, "analise_base.json") or {}
    biomarcadores = _ler_json(pasta_run, "biomarcadores.json") or []
    metricas = _ler_json(pasta_run, "metricas.json") or {}

    pipeline_data: dict = {
        "modo": modo,
        "n_imagens": len(biomarcadores),
        "analise_base": analise_base.get("analise", {}),
        "estrategia_preproc": analise_base.get("estrategia", {}),
    }

    # Estatísticas descritivas dos biomarcadores
    import numpy as np
    campos = [
        ("morfologia", "circularidade"),
        ("morfologia", "solidez"),
        ("textura_glcm", "contraste"),
        ("textura_glcm", "homogeneidade"),
        ("textura_glcm", "energia"),
        ("textura_glcm", "entropia"),
        ("distribuicao_intensidade", "snr"),
        ("distribuicao_intensidade", "assimetria"),
        ("distribuicao_intensidade", "curtose"),
    ]
    por_cat: dict = {}
    for r in biomarcadores:
        por_cat.setdefault(r["categoria"], []).append(r["biomarcadores"])

    estatisticas: dict = {}
    for cat, lista in por_cat.items():
        estatisticas[cat] = {"n": len(lista), "campos": {}}
        for grupo, campo in campos:
            valores = [b[grupo][campo] for b in lista if grupo in b and campo in b[grupo]]
            if not valores:
                continue
            arr = np.array(valores)
            estatisticas[cat]["campos"][campo] = {
                "media": round(float(arr.mean()), 4),
                "mediana": round(float(np.median(arr)), 4),
                "desvio": round(float(arr.std()), 4),
                "min": round(float(arr.min()), 4),
                "max": round(float(arr.max()), 4),
                "valores": arr.tolist(),
            }
    pipeline_data["estatisticas"] = estatisticas

    # Classificador (se treinou)
    if metricas and "metricas" in metricas:
        pipeline_data.update(metricas)
    elif metricas and "aviso" in metricas:
        pipeline_data["aviso_classificador"] = metricas["aviso"]

    return pipeline_data


# ---------------------------------------------------------------------------
# Rotas
# ---------------------------------------------------------------------------

@app.route("/")
def tela1():
    return render_template("tela1_upload.html")


@app.route("/analisar", methods=["POST"])
def analisar():
    from biostatusia.crew import BioStatusIACrew, BioStatusIACrewTabular
    from biostatusia.database import salvar, salvar_resultado
    from biostatusia.pipeline.classificador import treinar_vetores
    from biostatusia.pipeline.dados_tabulares import (
        analisar_tabular, carregar_csv, detectar_schema, extrair_features,
        decidir_estrategia_tabular, preprocessar_tabular_amostras,
    )

    # 1. Resolver caminho do dataset
    arquivo = request.files.get("arquivo")
    caminho_manual = request.form.get("caminho_manual", "").strip()
    kaggle_id = request.form.get("kaggle_id", "").strip()

    dataset_path = ""
    if arquivo and arquivo.filename:
        nome = arquivo.filename
        dest = UPLOAD_DIR / nome
        arquivo.save(str(dest))
        if nome.lower().endswith(".zip"):
            pasta_extracao = UPLOAD_DIR / Path(nome).stem
            pasta_extracao.mkdir(exist_ok=True)
            with zipfile.ZipFile(dest, "r") as z:
                z.extractall(pasta_extracao)
            dataset_path = str(pasta_extracao)
        else:
            dataset_path = str(dest)
    elif caminho_manual:
        dataset_path = caminho_manual
    else:
        try:
            import kagglehub
            dataset_to_download = kaggle_id if kaggle_id else "aryashah2k/breast-ultrasound-images-dataset"
            dataset_path = kagglehub.dataset_download(dataset_to_download)
        except Exception as e:
            return f"Nenhum dataset fornecido e KaggleHub falhou: {e}", 400

    # 2. Detectar modo
    base_path = Path(dataset_path)
    if not base_path.exists():
        return f"Caminho não encontrado: {dataset_path}", 400

    modo = detectar_estrutura(base_path)
    if modo == "invalido":
        return (
            "Entrada não reconhecida. Aceito: imagem (.png/.jpg/.bmp/.tif), "
            "CSV/TXT tabular, ZIP, ou pasta com imagens e/ou CSV."
        ), 400

    # 3. Criar workspace da run
    pasta_run = criar_pasta_run()

    # === MODO TABULAR PURO ===
    if modo == "tabular":
        csv_path = encontrar_csv(base_path)
        if not csv_path:
            return "Nenhum arquivo CSV/TXT encontrado.", 400

        # Crew tabular gera o laudo via bioestatistico
        try:
            crew_out = BioStatusIACrewTabular().crew().kickoff(
                inputs={"caminho_csv": str(csv_path)}
            )
            laudo = str(crew_out)
        except Exception as e:
            laudo = f"Erro no agente bioestatístico: {e}"

        # Stats e classificador continuam em Flask (operações puras determinísticas)
        resultado = carregar_csv(str(csv_path))
        if not resultado:
            return "Falha ao ler o arquivo tabular.", 400
        header, data = resultado
        schema = detectar_schema(header, data)
        
        # 1. Extrair features bruto (mantendo NaNs)
        X_raw, y, label_map = extrair_features(data, schema)
        
        # 2. Análise Estatística sobre o bruto
        stats_tab = analisar_tabular(X_raw, y, schema)
        
        # 3. Decidir Estratégia de Pré-processamento
        estrategia = decidir_estrategia_tabular(stats_tab)
        
        # 4. Executar Pré-processamento (imputar NaNs)
        X_preproc = preprocessar_tabular_amostras(X_raw, estrategia)

        pipeline_data: dict = {
            "modo": "tabular",
            "n_imagens": stats_tab["n_amostras"],
            "arquivo_tabular": str(csv_path),
            "schema_tabular": schema,
            "label_map": label_map,
            "tabular_stats": stats_tab,
            "estrategia_preproc": estrategia,
        }

        melhor = "N/A"
        if y is not None and len(set(y.tolist())) >= 2 and len(X_preproc) >= 10:
            try:
                # O AutoML roda com o escalamento dinâmico
                res_clf = treinar_vetores(X_preproc, y, scaling=estrategia["escalamento"])
                pipeline_data.update(res_clf)
                melhor = res_clf["melhor_modelo"]
            except Exception as e:
                pipeline_data["erro_classificador"] = str(e)
        else:
            pipeline_data["aviso_classificador"] = (
                f"Treino não executado: {len(X_preproc)} amostras, "
                f"{len(set(y.tolist())) if y is not None else 0} classes."
            )

        analise_id = salvar(str(csv_path), "TABULAR", laudo)
        resultado_id = salvar_resultado(
            dataset_path=dataset_path,
            n_imagens=stats_tab["n_amostras"],
            pipeline_data=pipeline_data,
            melhor_modelo=melhor,
            analise_id=analise_id,
        )
        return redirect(url_for("tela2", resultado_id=resultado_id))

    # === MODOS COM IMAGEM (imagem_unica, imagens_soltas, dataset_rotulado, multimodal) ===
    imagens = listar_imagens(base_path)
    if not imagens:
        return "Nenhuma imagem válida encontrada.", 400

    # Pipeline completo via Crew (4 agentes sequenciais)
    try:
        crew_out = BioStatusIACrew().crew().kickoff(inputs={
            "caminho_dataset": dataset_path,
            "pasta_run": str(pasta_run),
        })
        laudo = str(crew_out)
    except Exception as e:
        laudo = f"Erro no pipeline CrewAI: {e}"

    # Consolidar dados dos JSONs persistidos pelos agentes
    pipeline_data = _consolidar_imagem(pasta_run, modo)
    melhor = pipeline_data.get("melhor_modelo", "N/A")

    # Multimodal: adicionar análise tabular ao mesmo resultado
    if modo == "multimodal":
        csv_path = encontrar_csv(base_path)
        if csv_path:
            resultado_csv = carregar_csv(str(csv_path))
            if resultado_csv:
                header_t, data_t = resultado_csv
                schema_t = detectar_schema(header_t, data_t)
                X_t, y_t, label_map_t = extrair_features(data_t, schema_t)
                if X_t.size > 0:
                    pipeline_data["tabular_stats"] = analisar_tabular(X_t, y_t, schema_t)
                    pipeline_data["schema_tabular"] = schema_t
                    pipeline_data["label_map"] = label_map_t
                    pipeline_data["arquivo_tabular"] = str(csv_path)
                    if y_t is not None and len(set(y_t.tolist())) >= 2 and len(X_t) >= 10:
                        try:
                            res_tab = treinar_vetores(X_t, y_t)
                            pipeline_data["metricas_tabular"] = res_tab["metricas"]
                            pipeline_data["roc_data_tabular"] = res_tab["roc_data"]
                            pipeline_data["cm_tabular"] = res_tab["confusion_matrix"]
                            pipeline_data["melhor_modelo_tabular"] = res_tab["melhor_modelo"]
                        except Exception as e:
                            pipeline_data["erro_classificador_tabular"] = str(e)

    # Persistir no banco
    primeira = imagens[0]
    analise_id = salvar(primeira["caminho"], primeira["categoria"], laudo)
    resultado_id = salvar_resultado(
        dataset_path=dataset_path,
        n_imagens=pipeline_data["n_imagens"],
        pipeline_data=pipeline_data,
        melhor_modelo=melhor,
        analise_id=analise_id,
    )
    return redirect(url_for("tela2", resultado_id=resultado_id))


@app.route("/resultados/<int:resultado_id>")
def tela2(resultado_id: int):
    from biostatusia.database import buscar_resultado, listar

    dados = buscar_resultado(resultado_id)
    if not dados:
        return "Resultado não encontrado.", 404

    pipeline = dados["pipeline"]
    laudo_html = md.markdown(dados["laudo"] or "")
    historico = listar()

    return render_template(
        "tela2_resultados.html",
        dados=dados,
        pipeline=pipeline,
        pipeline_json=json.dumps(pipeline),
        laudo_html=laudo_html,
        historico=historico,
    )


if __name__ == "__main__":
    app.run(debug=True, port=5000)
