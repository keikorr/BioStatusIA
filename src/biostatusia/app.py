import json
import zipfile
from pathlib import Path

import markdown as md
from flask import Flask, jsonify, redirect, render_template, request, url_for

from biostatusia.pipeline.io_utils import (
    criar_pasta_run,
    eh_dicom,
    eh_imagem,
    eh_sinal_temporal,
    eh_tabular,
    eh_volumetrico,
    encontrar_csv,
    label_pasta,
    listar_imagens,
)

app = Flask(__name__, template_folder="templates", static_folder="static")
app.config["MAX_CONTENT_LENGTH"] = 4096 * 1024 * 1024  # 4 GB

UPLOAD_DIR = Path(__file__).parent / "static" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


# ── Detecção de modo ──────────────────────────────────────────────────────────

def detectar_estrutura(caminho: Path) -> str:
    """
    Retorna o modo de operação detectado (escopo v3 — F1/F3/F4 + tabular).
    Modos de imagem comum: imagem_unica | imagens_soltas | dataset_rotulado | multimodal
    Modos tabular/sinal:    tabular | sinal_temporal | imagem_dicom_2d | volume_3d
    Multimodal expandido:   multimodal_expandido
    Modo inválido:          invalido
    """
    if caminho.is_file():
        if eh_imagem(caminho):
            return "imagem_unica"
        if eh_tabular(caminho):
            return "tabular"
        if eh_sinal_temporal(caminho):
            return "sinal_temporal"
        if eh_dicom(caminho):
            return "imagem_dicom_2d"
        if eh_volumetrico(caminho):
            return "volume_3d"
        return "invalido"

    if not caminho.is_dir():
        return "invalido"

    # Inventariar conteúdo da pasta
    tem_tab = tem_img = tem_temporal = tem_dicom = tem_vol = False
    for arq in caminho.rglob("*"):
        if not arq.is_file():
            continue
        if eh_tabular(arq):        tem_tab = True
        elif eh_imagem(arq):       tem_img = True
        elif eh_sinal_temporal(arq): tem_temporal = True
        elif eh_dicom(arq):        tem_dicom = True
        elif eh_volumetrico(arq):  tem_vol = True

    # ── Multimodal expandido ─────────────────────────────────────────────────
    n_tipos = sum([tem_tab, tem_img, tem_temporal, tem_dicom, tem_vol])
    if n_tipos > 1 and not (tem_tab and tem_img and n_tipos == 2):
        return "multimodal_expandido"

    # ── Modos com imagem comum ───────────────────────────────────────────────
    if tem_tab and tem_img:
        return "multimodal"
    if tem_tab:
        return "tabular"

    # Verificar rótulos (subpastas benign/malignant) — aplica a qualquer família
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

    # ── Modos de arquivo único por família ───────────────────────────────────
    if tem_img:        return "imagens_soltas"
    if tem_temporal:   return "sinal_temporal"
    if tem_vol:        return "volume_3d"
    if tem_dicom:
        # Pasta de DICOMs: muitos → série 3D, poucos → imagem 2D
        n_dcm = sum(1 for f in caminho.rglob("*.dcm") if f.is_file())
        return "volume_3d" if n_dcm >= 10 else "imagem_dicom_2d"

    return "invalido"


# ── Leitura de artefatos JSON dos agentes ─────────────────────────────────────

def _ler_json(pasta: Path, nome: str) -> dict | list | None:
    arq = pasta / nome
    if not arq.exists():
        return None
    with open(arq, "r", encoding="utf-8") as f:
        return json.load(f)


def _computar_engenharia_features(biomarcadores: list, estrategia: dict, limite: int = 24) -> dict | None:
    """Extrai features de engenharia de uma amostra balanceada de imagens e as ordena
    por importância. Retorna estrutura com método, ranking e médias — ou None."""
    import numpy as np
    from biostatusia.pipeline.preprocessamento import (
        engenharia_features, preprocessar_adaptativo, ranquear_features,
    )

    por_cat: dict = {}
    for r in biomarcadores:
        por_cat.setdefault(r.get("categoria", "INDEFINIDO"), []).append(r)

    cota = max(1, limite // max(1, len(por_cat)))
    amostra = [r for lista in por_cat.values() for r in lista[:cota]]
    if not amostra:
        return None

    mapa = {"BENIGNO": 0, "MALIGNO": 1}
    linhas, rotulos, nomes = [], [], None
    for r in amostra:
        caminho = r.get("caminho", "")
        if not caminho or not Path(caminho).exists():
            continue
        img = preprocessar_adaptativo(caminho, estrategia)
        if img is None:
            continue
        feats = engenharia_features(img, estrategia)
        if not feats:
            continue
        if nomes is None:
            nomes = list(feats.keys())
        linhas.append([feats.get(k, 0.0) for k in nomes])
        rotulos.append(mapa.get(r.get("categoria", "")))

    if not linhas or nomes is None:
        return None

    X = np.array(linhas, dtype=float)
    y = None
    if all(v is not None for v in rotulos) and len(set(rotulos)) >= 2:
        y = np.array(rotulos)

    ranking = ranquear_features(X, nomes, y)
    medias = {nomes[i]: round(float(X[:, i].mean()), 4) for i in range(len(nomes))}
    return {
        "metodo": ranking["metodo"],
        "ranking": ranking["ranking"],
        "medias": medias,
        "n_amostras": int(X.shape[0]),
    }


def _consolidar_imagem(pasta_run: Path, modo: str) -> dict:
    """Consolida JSONs da crew de imagem (modos originais)."""
    import numpy as np

    analise_base = _ler_json(pasta_run, "analise_base.json") or {}
    biomarcadores = _ler_json(pasta_run, "biomarcadores.json") or []
    metricas = _ler_json(pasta_run, "metricas.json") or {}

    pipeline_data: dict = {
        "modo": modo,
        "familia": "F3",
        "n_imagens": len(biomarcadores),
        "analise_base": analise_base.get("analise", {}),
        "estrategia_preproc": analise_base.get("estrategia", {}),
    }

    campos = [
        ("morfologia", "circularidade"), ("morfologia", "solidez"),
        ("textura_glcm", "contraste"), ("textura_glcm", "homogeneidade"),
        ("textura_glcm", "energia"), ("textura_glcm", "entropia"),
        ("distribuicao_intensidade", "snr"), ("distribuicao_intensidade", "assimetria"),
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

    pipeline_data["biomarcadores"] = [
        {
            "caminho": r.get("caminho", ""),
            "categoria": r.get("categoria", ""),
            "biomarcadores": r.get("biomarcadores", {}),
        }
        for r in biomarcadores[:50]
    ]

    try:
        fe = _computar_engenharia_features(
            biomarcadores, pipeline_data.get("estrategia_preproc", {})
        )
        if fe:
            pipeline_data["features_engenharia"] = fe
    except Exception:
        pass

    if metricas and "metricas" in metricas:
        pipeline_data.update(metricas)
    elif metricas and "aviso" in metricas:
        pipeline_data["aviso_classificador"] = metricas["aviso"]

    return pipeline_data


def _consolidar_sinal(pasta_run: Path, modo: str, familia: str) -> dict:
    """Consolida JSONs das novas crews de sinal (F1–F5)."""
    _mapa_json = {
        "F1": "biomarcadores_temporal.json",
        "F3": "biomarcadores_dicom.json",
        "F4": "biomarcadores_volumetrico.json",
    }
    nome_json = _mapa_json.get(familia, "biomarcadores_temporal.json")
    payload = _ler_json(pasta_run, nome_json) or {}

    pipeline_data: dict = {
        "modo": modo,
        "familia": familia,
        "tipo_sinal": payload.get("tipo", ""),
        "n_imagens": payload.get("n_processados", 0),
        "n_erros": payload.get("n_erros", 0),
        "biomarcadores_sinal": payload.get("biomarcadores", []),
    }

    # Repassar métricas se treinou classificador
    for chave in ("metricas", "metricas_cv", "roc_data", "confusion_matrix",
                  "melhor_modelo", "comparacao_ab"):
        if chave in payload:
            pipeline_data[chave] = payload[chave]

    # Dados de visualização do primeiro sinal (downsampled)
    bio_list = payload.get("biomarcadores", [])
    if bio_list and "dados_viz" in bio_list[0]:
        pipeline_data["dados_viz"] = bio_list[0]["dados_viz"]
    if bio_list and "canais" in bio_list[0]:
        pipeline_data["canais"] = bio_list[0].get("canais", [])

    return pipeline_data


# ── Rotas principais ──────────────────────────────────────────────────────────

@app.route("/")
def tela1():
    return render_template("tela1_upload.html")


@app.route("/analisar", methods=["POST"])
def analisar():
    from biostatusia.crew import (
        BioStatusIACrew,
        BioStatusIACrewTabular,
        BioStatusIACrewSinal,
        BioStatusIACrewImagem3D,
    )
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
            "Entrada não reconhecida. Aceito: imagens (.png/.jpg/.tif), "
            "CSV/TXT, ZIP, .edf/.mat/.dat/.hea (sinais temporais F1), "
            ".dcm (DICOM 2D F3), .nii/.nii.gz/.mha (volume 3D F4), "
            "ou pasta com qualquer combinação desses arquivos."
        ), 400

    pasta_run = criar_pasta_run()

    # ── MODO TABULAR PURO ─────────────────────────────────────────────────────
    if modo == "tabular":
        csv_path = encontrar_csv(base_path)
        if not csv_path:
            return "Nenhum arquivo CSV/TXT encontrado.", 400
        try:
            crew_out = BioStatusIACrewTabular().crew().kickoff(
                inputs={"caminho_csv": str(csv_path)}
            )
            laudo = str(crew_out)
        except Exception as e:
            laudo = f"Erro no agente bioestatístico: {e}"

        resultado_csv = carregar_csv(str(csv_path))
        if not resultado_csv:
            return "Falha ao ler o arquivo tabular.", 400
        header, data = resultado_csv
        schema = detectar_schema(header, data)
        X_raw, y, label_map = extrair_features(data, schema)
        stats_tab = analisar_tabular(X_raw, y, schema)
        estrategia = decidir_estrategia_tabular(stats_tab)
        X_preproc = preprocessar_tabular_amostras(X_raw, estrategia)

        pipeline_data: dict = {
            "modo": "tabular", "familia": "tabular",
            "n_imagens": stats_tab["n_amostras"],
            "arquivo_tabular": str(csv_path),
            "schema_tabular": schema, "label_map": label_map,
            "tabular_stats": stats_tab, "estrategia_preproc": estrategia,
        }
        melhor = "N/A"
        if y is not None and len(set(y.tolist())) >= 2 and len(X_preproc) >= 10:
            try:
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
            dataset_path=dataset_path, n_imagens=stats_tab["n_amostras"],
            pipeline_data=pipeline_data, melhor_modelo=melhor, analise_id=analise_id,
        )
        return redirect(url_for("tela2", resultado_id=resultado_id))

    # ── MODOS DE SINAL TEMPORAL (F1) ──────────────────────────────────────────
    if modo == "sinal_temporal":
        tipo_sinal = request.form.get("tipo_sinal", "auto")
        try:
            crew_out = BioStatusIACrewSinal().crew().kickoff(inputs={
                "caminho_dataset": dataset_path,
                "pasta_run": str(pasta_run),
                "tipo_sinal": tipo_sinal,
            })
            laudo = str(crew_out)
        except Exception as e:
            laudo = f"Erro no pipeline de sinais: {e}"

        pipeline_data = _consolidar_sinal(pasta_run, modo, "F1")
        melhor = pipeline_data.get("melhor_modelo", "N/A")
        analise_id = salvar(dataset_path, "SINAL_TEMPORAL", laudo)
        resultado_id = salvar_resultado(
            dataset_path=dataset_path, n_imagens=pipeline_data["n_imagens"],
            pipeline_data=pipeline_data, melhor_modelo=melhor, analise_id=analise_id,
            familia_sinal="F1", sinal_tipo=pipeline_data.get("tipo_sinal", ""),
        )
        return redirect(url_for("tela2", resultado_id=resultado_id))

    # ── MODO DICOM 2D (F3) ────────────────────────────────────────────────────
    if modo == "imagem_dicom_2d":
        try:
            crew_out = BioStatusIACrewImagem3D().crew().kickoff(inputs={
                "caminho_dataset": dataset_path,
                "pasta_run": str(pasta_run),
                "tipo_sinal": "DICOM 2D",
            })
            laudo = str(crew_out)
        except Exception as e:
            laudo = f"Erro no pipeline DICOM: {e}"

        pipeline_data = _consolidar_sinal(pasta_run, modo, "F3")
        melhor = pipeline_data.get("melhor_modelo", "N/A")
        analise_id = salvar(dataset_path, "DICOM_2D", laudo)
        resultado_id = salvar_resultado(
            dataset_path=dataset_path, n_imagens=pipeline_data["n_imagens"],
            pipeline_data=pipeline_data, melhor_modelo=melhor, analise_id=analise_id,
            familia_sinal="F3", sinal_tipo=pipeline_data.get("tipo_sinal", ""),
        )
        return redirect(url_for("tela2", resultado_id=resultado_id))

    # ── MODO VOLUME 3D (F4) ────────────────────────────────────────────────────
    if modo == "volume_3d":
        try:
            crew_out = BioStatusIACrewImagem3D().crew().kickoff(inputs={
                "caminho_dataset": dataset_path,
                "pasta_run": str(pasta_run),
                "tipo_sinal": "Volume 3D",
            })
            laudo = str(crew_out)
        except Exception as e:
            laudo = f"Erro no pipeline volumétrico: {e}"

        pipeline_data = _consolidar_sinal(pasta_run, modo, "F4")
        melhor = pipeline_data.get("melhor_modelo", "N/A")
        analise_id = salvar(dataset_path, "VOLUME_3D", laudo)
        resultado_id = salvar_resultado(
            dataset_path=dataset_path, n_imagens=pipeline_data["n_imagens"],
            pipeline_data=pipeline_data, melhor_modelo=melhor, analise_id=analise_id,
            familia_sinal="F4", sinal_tipo=pipeline_data.get("tipo_sinal", ""),
        )
        return redirect(url_for("tela2", resultado_id=resultado_id))

    # ── MODOS COM IMAGEM ORIGINAL (imagem_unica, imagens_soltas, dataset_rotulado, multimodal) ──
    imagens = listar_imagens(base_path)
    if not imagens:
        return "Nenhuma imagem válida encontrada.", 400

    try:
        crew_out = BioStatusIACrew().crew().kickoff(inputs={
            "caminho_dataset": dataset_path,
            "pasta_run": str(pasta_run),
        })
        laudo = str(crew_out)
    except Exception as e:
        laudo = f"Erro no pipeline CrewAI: {e}"

    pipeline_data = _consolidar_imagem(pasta_run, modo)
    melhor = pipeline_data.get("melhor_modelo", "N/A")

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

    primeira = imagens[0]
    analise_id = salvar(primeira["caminho"], primeira["categoria"], laudo)
    resultado_id = salvar_resultado(
        dataset_path=dataset_path, n_imagens=pipeline_data["n_imagens"],
        pipeline_data=pipeline_data, melhor_modelo=melhor, analise_id=analise_id,
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


# ── Rota: Histórico para Aba 4 ───────────────────────────────────────────────

@app.route("/api/historico")
def api_historico():
    """Retorna JSON com os últimos 30 resultados do banco para o seletor da Aba 4."""
    from biostatusia.database import listar_resultados_completo
    return jsonify(listar_resultados_completo())


@app.route("/api/exemplos/<int:resultado_id>")
def api_exemplos(resultado_id: int):
    """Exemplos individuais do dataset carregado nesta análise (para a Aba 4)."""
    from biostatusia.database import buscar_resultado

    dados = buscar_resultado(resultado_id)
    if not dados:
        return jsonify({"erro": f"Resultado {resultado_id} não encontrado"}), 404

    pipeline = dados["pipeline"]
    bio_list = pipeline.get("biomarcadores_sinal") or pipeline.get("biomarcadores") or []
    familia = pipeline.get("familia", "")
    tipo = pipeline.get("tipo_sinal", "")

    exemplos = []
    for i, r in enumerate(bio_list[:50]):
        caminho = r.get("caminho", "")
        nome = Path(caminho).name if caminho else f"exemplo_{i}"
        exemplos.append({
            "idx": i,
            "nome": nome,
            "categoria": r.get("categoria", ""),
            "biomarcadores": r.get("biomarcadores", {}),
            "familia": familia,
            "tipo": tipo,
        })

    return jsonify(exemplos)


# ── Via 1: Laudo Populacional (nível da base) ─────────────────────────────────

@app.route("/laudo_populacional/<int:resultado_id>")
def laudo_populacional(resultado_id: int):
    """
    Relatório analítico determinístico do dataset completo: distribuição
    estatística, correlações de biomarcadores e pódio final do AutoML.
    Não depende do LLM — montado a partir do pipeline_data persistido.
    """
    from biostatusia.database import buscar_resultado
    from biostatusia.pipeline.relatorios import (
        construir_laudo_populacional, construir_podio, correlacoes_biomarcadores,
    )

    dados = buscar_resultado(resultado_id)
    if not dados:
        return jsonify({"erro": f"Resultado {resultado_id} não encontrado"}), 404

    pipeline = dict(dados["pipeline"])

    # Enriquecer com correlações calculadas sobre os biomarcadores de sinal, se houver.
    bio_list = pipeline.get("biomarcadores_sinal", [])
    if bio_list:
        from biostatusia.pipeline.inferencia import achatar_biomarcadores
        vetores, nomes = [], []
        for r in bio_list:
            v = achatar_biomarcadores(r.get("biomarcadores", {}))
            if v.size:
                vetores.append(v.tolist())
        if vetores:
            largura = min(len(x) for x in vetores)
            vetores = [x[:largura] for x in vetores]
            nomes = [f"f{i}" for i in range(largura)]
            pipeline["correlacoes_biomarcadores"] = correlacoes_biomarcadores(vetores, nomes)

    laudo_md = construir_laudo_populacional(pipeline)
    podio = construir_podio(pipeline.get("metricas", {}), pipeline.get("melhor_modelo", ""))
    return jsonify({
        "laudo_html": md.markdown(laudo_md, extensions=["tables"]),
        "laudo_md": laudo_md,
        "podio": podio,
    })


# ── Rota: Laudo de Amostra Avulsa ─────────────────────────────────────────────

@app.route("/laudo_amostra", methods=["POST"])
def laudo_amostra():
    """
    Recebe um arquivo avulso (multipart) OU um resultado_id do banco e
    gera laudo do radiologista_ia_interativo sem executar o pipeline completo.

    Casos de uso da Aba 4 — Seção A:
      - Upload de nova amostra (arquivo de imagem, sinal, DICOM, etc.)
      - Seleção de análise anterior pelo resultado_id
    """
    from biostatusia.crew import BioStatusIACrewInterativo
    from biostatusia.database import buscar_resultado, salvar_laudo_interativo
    import markdown as md_

    resultado_id_str = request.form.get("resultado_id", "").strip()
    arquivo = request.files.get("arquivo")

    # ── Caso 1: análise já existente no banco ──────────────────────────────
    if resultado_id_str and resultado_id_str.isdigit():
        resultado_id = int(resultado_id_str)
        dados = buscar_resultado(resultado_id)
        if not dados:
            return jsonify({"erro": f"Resultado {resultado_id} não encontrado"}), 404

        pipeline = dados["pipeline"]
        familia = pipeline.get("familia", "")
        tipo_sinal = pipeline.get("tipo_sinal", "") or dados.get("categoria", "")

        # Resumo do pipeline como contexto para o agente
        biomarcadores_ctx = {
            "fonte": "banco",
            "resultado_id": resultado_id,
            "familia": familia,
            "tipo_sinal": tipo_sinal,
            "modo": pipeline.get("modo", ""),
            "n_amostras": pipeline.get("n_imagens", 0),
            "melhor_modelo": dados.get("melhor_modelo", "N/A"),
        }
        # Anexa métricas se existirem
        if pipeline.get("metricas"):
            melhor = dados.get("melhor_modelo", "")
            m = pipeline["metricas"].get(melhor, {})
            biomarcadores_ctx["metricas_modelo"] = {
                "auc": m.get("auc"),
                "sensibilidade": m.get("sensibilidade"),
                "especificidade": m.get("especificidade"),
                "f1": m.get("f1"),
            }
        # Anexa biomarcadores do exemplo selecionado (ou o primeiro, por padrão)
        bio_list = pipeline.get("biomarcadores_sinal") or pipeline.get("biomarcadores") or []
        exemplo_idx_str = request.form.get("exemplo_idx", "").strip()
        exemplo_nome = ""
        if bio_list:
            idx = 0
            if exemplo_idx_str.isdigit() and 0 <= int(exemplo_idx_str) < len(bio_list):
                idx = int(exemplo_idx_str)
            exemplo = bio_list[idx]
            biomarcadores_ctx["exemplo_biomarcadores"] = exemplo.get("biomarcadores", {})
            biomarcadores_ctx["exemplo_idx"] = idx
            caminho_ex = exemplo.get("caminho", "")
            exemplo_nome = Path(caminho_ex).name if caminho_ex else f"exemplo_{idx}"
            biomarcadores_ctx["exemplo_nome"] = exemplo_nome
            biomarcadores_ctx["categoria_exemplo"] = exemplo.get("categoria", "")

        if exemplo_nome:
            descricao_selecao = (
                f"Exemplo '{exemplo_nome}' (#{biomarcadores_ctx.get('exemplo_idx', 0)}) "
                f"do resultado #{resultado_id} — {dados.get('dataset_path', '')}"
            )
        else:
            descricao_selecao = f"Análise do resultado #{resultado_id} — {dados.get('dataset_path', '')}"

    # ── Caso 2: upload de arquivo avulso ──────────────────────────────────
    elif arquivo and arquivo.filename:
        nome = arquivo.filename
        dest = UPLOAD_DIR / nome
        arquivo.save(str(dest))

        # Detecta estrutura do arquivo
        modo = detectar_estrutura(dest)
        familia = ""
        tipo_sinal = ""

        biomarcadores_ctx = {
            "fonte": "upload_avulso",
            "arquivo": nome,
            "modo": modo,
            "familia": familia,
        }

        pasta_run = criar_pasta_run()

        try:
            if eh_imagem(dest):
                from biostatusia.pipeline.extracao import extrair_biomarcadores_lote
                bio = extrair_biomarcadores_lote([str(dest)], {})
                biomarcadores_ctx["biomarcadores"] = bio[0] if bio else {}
                familia = "F3"

            elif eh_sinal_temporal(dest):
                from biostatusia.pipeline.io_sinais import carregar_sinal
                from biostatusia.pipeline.extracao_temporal import extrair_features_temporal
                sinal = carregar_sinal(str(dest))
                feats = extrair_features_temporal(sinal)
                biomarcadores_ctx["biomarcadores"] = feats
                familia = "F1"
                tipo_sinal = sinal.tipo

            elif eh_dicom(dest):
                from biostatusia.pipeline.extracao_dicom import extrair_features_dicom
                feats = extrair_features_dicom(dest)
                biomarcadores_ctx["biomarcadores"] = feats
                familia = "F3"
                tipo_sinal = "DICOM"

            elif eh_tabular(dest):
                from biostatusia.pipeline.dados_tabulares import (
                    carregar_csv, detectar_schema, extrair_features, analisar_tabular
                )
                res = carregar_csv(str(dest))
                if res:
                    header, data = res
                    schema = detectar_schema(header, data)
                    X, y, _ = extrair_features(data, schema)
                    stats = analisar_tabular(X, y, schema)
                    biomarcadores_ctx["tabular_stats"] = {
                        "n_amostras": stats.get("n_amostras", 0),
                        "n_features": stats.get("n_features", 0),
                    }

        except Exception as e:
            biomarcadores_ctx["erro_extracao"] = str(e)

        biomarcadores_ctx["familia"] = familia
        biomarcadores_ctx["tipo_sinal"] = tipo_sinal

        # ── Inferência individual: isola o vencedor do pódio e classifica ──
        bio_extraido = biomarcadores_ctx.get("biomarcadores")
        if isinstance(bio_extraido, dict) and bio_extraido:
            try:
                from biostatusia.pipeline.inferencia import (
                    achatar_biomarcadores, prever_exemplar,
                )
                vetor = achatar_biomarcadores(bio_extraido)
                if vetor.size:
                    biomarcadores_ctx["inferencia_modelo"] = prever_exemplar(
                        vetor, familia or "IMG"
                    )
            except Exception as e:
                biomarcadores_ctx["inferencia_erro"] = str(e)

        descricao_selecao = f"Amostra avulsa: {nome} (modo: {modo})"

    else:
        return jsonify({"erro": "Forneça resultado_id ou um arquivo para análise."}), 400

    # ── Chama o agente interativo ──────────────────────────────────────────
    try:
        crew_out = BioStatusIACrewInterativo().crew().kickoff(inputs={
            "dados_selecao": json.dumps({"descricao": descricao_selecao}, ensure_ascii=False),
            "tipo_sinal": biomarcadores_ctx.get("tipo_sinal", ""),
            "biomarcadores_trecho": json.dumps(biomarcadores_ctx, ensure_ascii=False),
        })
        laudo_foco = str(crew_out)
    except Exception as e:
        laudo_foco = f"Erro ao gerar laudo: {e}"

    laudo_id = salvar_laudo_interativo(
        resultado_id=int(resultado_id_str) if resultado_id_str and resultado_id_str.isdigit() else 0,
        laudo_foco=laudo_foco,
    )

    return jsonify({
        "laudo_html": md_.markdown(laudo_foco),
        "laudo_id": laudo_id,
    })



if __name__ == "__main__":
    app.run(debug=True, port=5000)
