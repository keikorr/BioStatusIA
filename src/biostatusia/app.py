import json
import zipfile
from pathlib import Path

import markdown as md
from flask import Flask, jsonify, redirect, render_template, request, url_for

from biostatusia.pipeline.io_utils import (
    criar_pasta_run,
    eh_audio_biomedico,
    eh_dicom,
    eh_imagem,
    eh_sinal_temporal,
    eh_tabular,
    eh_video,
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
    Retorna o modo de operação detectado.
    Modos originais: imagem_unica | tabular | multimodal | dataset_rotulado | imagens_soltas
    Novos modos:     sinal_temporal | audio_biomedico | imagem_dicom_2d | volume_3d | video_medico
    Modo inválido:   invalido
    """
    if caminho.is_file():
        if eh_imagem(caminho):
            return "imagem_unica"
        if eh_tabular(caminho):
            return "tabular"
        if eh_sinal_temporal(caminho):
            return "sinal_temporal"
        if eh_audio_biomedico(caminho):
            return "audio_biomedico"
        if eh_dicom(caminho):
            return "imagem_dicom_2d"
        if eh_volumetrico(caminho):
            return "volume_3d"
        if eh_video(caminho):
            return "video_medico"
        return "invalido"

    if not caminho.is_dir():
        return "invalido"

    # Inventariar conteúdo da pasta
    tem_tab = tem_img = tem_temporal = tem_audio = tem_dicom = tem_vol = tem_video = False
    for arq in caminho.rglob("*"):
        if not arq.is_file():
            continue
        if eh_tabular(arq):        tem_tab = True
        elif eh_imagem(arq):       tem_img = True
        elif eh_sinal_temporal(arq): tem_temporal = True
        elif eh_audio_biomedico(arq): tem_audio = True
        elif eh_dicom(arq):        tem_dicom = True
        elif eh_volumetrico(arq):  tem_vol = True
        elif eh_video(arq):        tem_video = True

    # ── Multimodal expandido ─────────────────────────────────────────────────
    n_tipos = sum([tem_tab, tem_img, tem_temporal, tem_audio, tem_dicom, tem_vol, tem_video])
    if n_tipos > 1 and not (tem_tab and tem_img and n_tipos == 2):
        return "multimodal_expandido"

    # ── Modos originais ──────────────────────────────────────────────────────
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
    if tem_audio:      return "audio_biomedico"
    if tem_vol:        return "volume_3d"
    if tem_video:      return "video_medico"
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

    if metricas and "metricas" in metricas:
        pipeline_data.update(metricas)
    elif metricas and "aviso" in metricas:
        pipeline_data["aviso_classificador"] = metricas["aviso"]

    return pipeline_data


def _consolidar_sinal(pasta_run: Path, modo: str, familia: str) -> dict:
    """Consolida JSONs das novas crews de sinal (F1–F5)."""
    _mapa_json = {
        "F1": "biomarcadores_temporal.json",
        "F2": "biomarcadores_audio.json",
        "F3": "biomarcadores_dicom.json",
        "F4": "biomarcadores_volumetrico.json",
        "F5": "biomarcadores_video.json",
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
        BioStatusIACrewVideo,
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
            "CSV/TXT, ZIP, .edf/.mat/.dat/.hea (sinais), .wav/.mp3/.flac (áudio), "
            ".dcm (DICOM), .nii/.nii.gz/.mha (volume), .mp4/.avi/.mov (vídeo), "
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

    # ── MODO ÁUDIO BIOMÉDICO (F2) ──────────────────────────────────────────────
    if modo == "audio_biomedico":
        try:
            crew_out = BioStatusIACrewSinal().crew().kickoff(inputs={
                "caminho_dataset": dataset_path,
                "pasta_run": str(pasta_run),
                "tipo_sinal": "auto",
            })
            laudo = str(crew_out)
        except Exception as e:
            laudo = f"Erro no pipeline de áudio: {e}"

        pipeline_data = _consolidar_sinal(pasta_run, modo, "F2")
        melhor = pipeline_data.get("melhor_modelo", "N/A")
        analise_id = salvar(dataset_path, "AUDIO_BIOMEDICO", laudo)
        resultado_id = salvar_resultado(
            dataset_path=dataset_path, n_imagens=pipeline_data["n_imagens"],
            pipeline_data=pipeline_data, melhor_modelo=melhor, analise_id=analise_id,
            familia_sinal="F2", sinal_tipo=pipeline_data.get("tipo_sinal", ""),
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

    # ── MODO VÍDEO MÉDICO (F5) ─────────────────────────────────────────────────
    if modo == "video_medico":
        try:
            crew_out = BioStatusIACrewVideo().crew().kickoff(inputs={
                "caminho_dataset": dataset_path,
                "pasta_run": str(pasta_run),
            })
            laudo = str(crew_out)
        except Exception as e:
            laudo = f"Erro no pipeline de vídeo: {e}"

        pipeline_data = _consolidar_sinal(pasta_run, modo, "F5")
        melhor = pipeline_data.get("melhor_modelo", "N/A")
        analise_id = salvar(dataset_path, "VIDEO_MEDICO", laudo)
        resultado_id = salvar_resultado(
            dataset_path=dataset_path, n_imagens=pipeline_data["n_imagens"],
            pipeline_data=pipeline_data, melhor_modelo=melhor, analise_id=analise_id,
            familia_sinal="F5", sinal_tipo=pipeline_data.get("tipo_sinal", ""),
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


# ── Rota: Laudo Interativo ────────────────────────────────────────────────────

@app.route("/laudo_interativo", methods=["POST"])
def laudo_interativo():
    """
    Recebe seleção do médico (trecho de sinal ou ROI de imagem) e gera laudo focado.
    Payload JSON:
    {
      "resultado_id": 42,
      "tipo_sinal": "ECG",
      "dados_selecao": {
        "inicio_s": 10.5, "fim_s": 13.2, "canal": "II"      // para F1/F2
        "roi": {"x":120,"y":80,"w":60,"h":60}, "slice_idx":45 // para F3/F4
        "frame_inicio": 300, "frame_fim": 360                  // para F5
      }
    }
    """
    from biostatusia.crew import BioStatusIACrewInterativo
    from biostatusia.database import buscar_resultado, salvar_laudo_interativo
    import markdown as md_

    payload = request.get_json(force=True) or {}
    resultado_id = payload.get("resultado_id")
    tipo_sinal = payload.get("tipo_sinal", "")
    selecao = payload.get("dados_selecao", {})

    if not resultado_id:
        return jsonify({"erro": "resultado_id obrigatório"}), 400

    dados = buscar_resultado(resultado_id)
    if not dados:
        return jsonify({"erro": "Resultado não encontrado"}), 404

    pipeline = dados["pipeline"]
    familia = pipeline.get("familia", "")

    # Extrair biomarcadores do trecho selecionado
    biomarcadores_trecho = _extrair_biomarcadores_selecao(
        dados, selecao, familia, tipo_sinal
    )
    dados_selecao_str = json.dumps(selecao, ensure_ascii=False)

    try:
        crew_out = BioStatusIACrewInterativo().crew().kickoff(inputs={
            "dados_selecao": dados_selecao_str,
            "tipo_sinal": tipo_sinal or pipeline.get("tipo_sinal", ""),
            "biomarcadores_trecho": json.dumps(biomarcadores_trecho, ensure_ascii=False),
        })
        laudo_foco = str(crew_out)
    except Exception as e:
        laudo_foco = f"Erro ao gerar laudo interativo: {e}"

    # Persistir no banco
    roi_json = json.dumps(selecao.get("roi")) if selecao.get("roi") else None
    laudo_id = salvar_laudo_interativo(
        resultado_id=resultado_id,
        laudo_foco=laudo_foco,
        trecho_inicio=selecao.get("inicio_s"),
        trecho_fim=selecao.get("fim_s"),
        roi_json=roi_json,
        canal=selecao.get("canal"),
        slice_idx=selecao.get("slice_idx"),
    )

    return jsonify({
        "laudo_html": md_.markdown(laudo_foco),
        "laudo_id": laudo_id,
    })


def _extrair_biomarcadores_selecao(dados: dict, selecao: dict, familia: str, tipo_sinal: str) -> dict:
    """Extrai biomarcadores do trecho/região selecionado para enviar ao agente."""
    bio: dict = {"familia": familia, "tipo": tipo_sinal}

    try:
        # F1/F2 — trecho de sinal temporal
        if familia in ("F1", "F2") and "inicio_s" in selecao:
            bio_list = dados["pipeline"].get("biomarcadores_sinal", [])
            if bio_list:
                bio["exemplo_biomarcadores"] = bio_list[0].get("biomarcadores", {})
            bio["trecho_inicio_s"] = selecao.get("inicio_s")
            bio["trecho_fim_s"] = selecao.get("fim_s")
            bio["canal_selecionado"] = selecao.get("canal", "todos")

        # F3/F4 — ROI de imagem
        elif familia in ("F3", "F4") and "roi" in selecao:
            roi = selecao["roi"]
            dataset_path = dados.get("dataset_path", "")
            if dataset_path and Path(dataset_path).is_file():
                bio.update(_bio_roi_dicom(Path(dataset_path), roi, selecao.get("slice_idx")))
            bio["roi"] = roi

        # F5 — trecho de vídeo
        elif familia == "F5" and "frame_inicio" in selecao:
            bio["frames"] = f"{selecao.get('frame_inicio')} – {selecao.get('frame_fim')}"

        # Existente: imagem PNG/JPG
        elif familia in ("F3", "") and dados.get("imagem"):
            bio["categoria_global"] = dados.get("categoria", "")

    except Exception as e:
        bio["erro_extracao"] = str(e)

    return bio


def _bio_roi_dicom(path: Path, roi: dict, slice_idx: int | None) -> dict:
    """Extrai biomarcadores de uma ROI em uma imagem DICOM ou PNG."""
    import cv2
    import numpy as np
    from scipy.stats import skew, kurtosis

    ext = path.suffix.lower()
    x, y, w, h = int(roi.get("x", 0)), int(roi.get("y", 0)), int(roi.get("w", 64)), int(roi.get("h", 64))

    try:
        if ext == ".dcm":
            from biostatusia.pipeline.leitura_dicom import ler_dicom
            sinal = ler_dicom(path)
            arr = sinal.dados
        elif ext in {".nii", ".mha"} or "".join(path.suffixes).lower() == ".nii.gz":
            from biostatusia.pipeline.io_sinais import carregar_sinal
            sinal = carregar_sinal(path)
            arr = sinal.dados[slice_idx or sinal.dados.shape[0] // 2]
        else:
            from PIL import Image
            img = Image.open(str(path)).convert("L")
            arr = np.array(img).astype(np.float32) / 255.0

        roi_arr = arr[y:y+h, x:x+w]
        if roi_arr.size == 0:
            return {}

        flat = roi_arr.flatten()
        return {
            "roi_media": round(float(np.mean(flat)), 4),
            "roi_desvio": round(float(np.std(flat)), 4),
            "roi_max": round(float(np.max(flat)), 4),
            "roi_min": round(float(np.min(flat)), 4),
            "roi_assimetria": round(float(skew(flat)), 4),
            "roi_curtose": round(float(kurtosis(flat)), 4),
            "roi_shape": list(roi_arr.shape),
        }
    except Exception:
        return {}


# ── Rota: Histórico para Aba 4 ───────────────────────────────────────────────

@app.route("/api/historico")
def api_historico():
    """Retorna JSON com os últimos 30 resultados do banco para o seletor da Aba 4."""
    from biostatusia.database import listar_resultados_completo
    return jsonify(listar_resultados_completo())


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
        # Anexa biomarcadores de sinal se existirem
        bio_list = pipeline.get("biomarcadores_sinal", [])
        if bio_list:
            biomarcadores_ctx["exemplo_biomarcadores"] = bio_list[0].get("biomarcadores", {})

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

            elif eh_sinal_temporal(dest) or eh_audio_biomedico(dest):
                from biostatusia.pipeline.io_sinais import carregar_sinal
                from biostatusia.pipeline.extracao_temporal import extrair_features_temporal
                sinal = carregar_sinal(str(dest))
                feats = extrair_features_temporal(sinal)
                biomarcadores_ctx["biomarcadores"] = feats
                familia = "F1" if eh_sinal_temporal(dest) else "F2"
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



@app.route("/slice/<int:resultado_id>/<int:idx>")
def volume_slice(resultado_id: int, idx: int):
    """Retorna um slice axial de um volume 3D como PNG base64."""
    from biostatusia.database import buscar_resultado
    from biostatusia.pipeline.leitura_volumetrica import slice_para_png_base64
    from biostatusia.pipeline.io_sinais import carregar_sinal

    dados = buscar_resultado(resultado_id)
    if not dados:
        return jsonify({"erro": "Resultado não encontrado"}), 404

    dataset_path = dados.get("dataset_path", "")
    path = Path(dataset_path)
    if not path.exists():
        return jsonify({"erro": "Arquivo não encontrado"}), 404

    try:
        sinal = carregar_sinal(str(path))
        b64 = slice_para_png_base64(sinal.dados, idx)
        n_slices = sinal.dados.shape[0]
        return jsonify({"imagem_b64": b64, "n_slices": n_slices, "idx": idx})
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


# ── Rota: Frame de vídeo ────────────────────────────────────────────────────

@app.route("/frame/<int:resultado_id>/<int:idx>")
def video_frame(resultado_id: int, idx: int):
    """Retorna um frame específico de um vídeo como PNG base64."""
    from biostatusia.database import buscar_resultado
    from biostatusia.pipeline.leitura_video import extrair_frame, frame_para_png_base64

    dados = buscar_resultado(resultado_id)
    if not dados:
        return jsonify({"erro": "Resultado não encontrado"}), 404

    path = Path(dados.get("dataset_path", ""))
    if not path.exists():
        return jsonify({"erro": "Vídeo não encontrado"}), 404

    try:
        frame = extrair_frame(path, idx)
        b64 = frame_para_png_base64(frame)
        return jsonify({"imagem_b64": b64, "frame_idx": idx})
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
