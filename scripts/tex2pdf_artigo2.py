#!/usr/bin/env python
"""
Converte artigo2_automl.tex (subconjunto IEEEtran usado neste artigo) em HTML de
duas colunas e imprime em PDF via Chromium headless.

Fonte única da verdade: o .tex. Não há cópia paralela do texto.
"""
from __future__ import annotations

import base64
import html
import re
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
TEX = BASE / "artigo2_automl.tex"
HTML_OUT = BASE / "reports" / "artigo2_automl_render.html"
PDF_OUT = BASE / "artigo2_automl.pdf"
FIGDIR = BASE / "figuras_artigo2"

B = "\\"


# ─────────────────────────── extração do .tex ────────────────────────────────

def bloco(tex: str, nome: str) -> str:
    m = re.search(re.escape(B + "begin{" + nome + "}") + r"(.*?)"
                  + re.escape(B + "end{" + nome + "}"), tex, re.S)
    return m.group(1).strip() if m else ""


def chaves_pos(tex: str, cmd: str):
    """Devolve (conteudo, indice_apos_a_chave_de_fecho) do primeiro \\cmd{...}."""
    m = re.search(re.escape(B + cmd) + r"\{", tex)
    if not m:
        return "", -1
    i = m.end()
    prof, ini = 1, i
    while i < len(tex) and prof:
        if tex[i] == "{":
            prof += 1
        elif tex[i] == "}":
            prof -= 1
        i += 1
    return tex[ini:i - 1], i


def chaves(tex: str, cmd: str) -> str:
    return chaves_pos(tex, cmd)[0]


def bibliografia(tex: str) -> list[tuple[str, str]]:
    corpo = bloco(tex, "thebibliography")
    corpo = re.sub(r"^\{\d+\}", "", corpo).strip()
    itens = re.split(re.escape(B + "bibitem"), corpo)[1:]
    saida = []
    for it in itens:
        m = re.match(r"\s*\{([^}]+)\}(.*)", it, re.S)
        if m:
            saida.append((m.group(1), m.group(2).strip()))
    return saida


# ─────────────────────────── inline LaTeX → HTML ─────────────────────────────

def inline(txt: str, chave2num: dict[str, int]) -> str:
    formulas: list[str] = []

    def guardar(m):
        formulas.append(m.group(1))
        return f"\x00{len(formulas)-1}\x00"

    txt = re.sub(r"\$([^$]+)\$", guardar, txt)

    txt = re.sub(re.escape(B + "cite") + r"\{([^}]+)\}",
                 lambda m: "[" + ", ".join(
                     str(chave2num.get(k.strip(), "?")) for k in m.group(1).split(",")) + "]", txt)
    txt = re.sub(re.escape(B + "ref") + r"\{([^}]+)\}", lambda m: REFS.get(m.group(1), "?"), txt)
    txt = re.sub(re.escape(B + "texorpdfstring") + r"\{([^}]*)\}\{([^}]*)\}", r"\1", txt)
    for cmd, tag in (("textbf", "strong"), ("textit", "em"), ("emph", "em"), ("texttt", "code")):
        txt = re.sub(re.escape(B + cmd) + r"\{([^{}]*)\}", rf"<{tag}>\1</{tag}>", txt)
    txt = txt.replace(B + "%", "%").replace(B + "&", "&amp;").replace(B + "_", "_")
    txt = txt.replace("``", "\u201c").replace("''", "\u201d")
    txt = txt.replace("---", "\u2014").replace("--", "\u2013")
    txt = txt.replace(B + "\\", "<br>")
    txt = re.sub(r"\{" + re.escape(B) + r"'a\}", "\u00e1", txt)
    txt = re.sub(r"\{" + re.escape(B) + r"'u\}", "\u00fa", txt)
    txt = txt.replace("~", "\u00a0")

    def repor(m):
        return f'<span class="math">{html.escape(formulas[int(m.group(1))])}</span>'

    return re.sub(r"\x00(\d+)\x00", repor, txt)


REFS: dict[str, str] = {}


# ─────────────────────────────── conversão ───────────────────────────────────

def tabela_html(env: str, chave2num) -> str:
    legenda = chaves(env, "caption")
    rotulo = chaves(env, "label")
    corpo = bloco(env, "tabular")
    corpo = re.sub(r"^\s*\{(?:[^{}]|\{[^{}]*\})*\}", "", corpo, count=1)
    linhas = []
    for bruta in corpo.split(B + B):
        bruta = re.sub(re.escape(B) + r"(top|mid|bottom)rule", "", bruta)
        bruta = re.sub(re.escape(B) + r"cmidrule(\(lr\))?\{[^}]*\}", "", bruta)
        bruta = bruta.strip()
        if not bruta:
            continue
        celulas = []
        for c in bruta.split("&"):
            c = c.strip()
            mc = re.match(re.escape(B) + r"multicolumn\{(\d+)\}\{[^}]*\}\{(.*)\}$", c, re.S)
            if mc:
                celulas.append((int(mc.group(1)), mc.group(2)))
            else:
                celulas.append((1, c))
        linhas.append(celulas)
    if not linhas:
        return ""
    cabec = 1
    if linhas and any(B + "multicolumn" in " ".join(str(x) for x in l) for l in linhas[:1]):
        cabec = 2
    out = [f'<div class="tabela" id="{rotulo}">',
           f'<div class="cap"><strong>{TAB_NUM.get(rotulo, "TABLE")}</strong> '
           f'{inline(legenda, chave2num)}</div>', "<table>"]
    for i, l in enumerate(linhas):
        tag = "th" if i < cabec else "td"
        celdas = "".join(
            f'<{tag}{f" colspan={n}" if n > 1 else ""}>{inline(c, chave2num)}</{tag}>'
            for n, c in l)
        out.append(f"<tr>{celdas}</tr>")
    out += ["</table>", "</div>"]
    return "\n".join(out)


def figura_html(env: str, chave2num) -> str:
    legenda = chaves(env, "caption")
    rotulo = chaves(env, "label")
    m = re.search(re.escape(B + "includegraphics") + r"(\[[^\]]*\])?\{([^}]+)\}", env)
    if not m:
        return ""
    caminho = FIGDIR / m.group(2)
    if not caminho.exists():
        return ""
    b64 = base64.b64encode(caminho.read_bytes()).decode()
    largo = "figura larga" if env.strip().startswith(B + "begin{figure*}") else "figura"
    return (f'<div class="{largo}" id="{rotulo}">'
            f'<img src="data:image/png;base64,{b64}">'
            f'<div class="cap"><strong>{FIG_NUM.get(rotulo, "Fig.")}</strong> '
            f'{inline(legenda, chave2num)}</div></div>')


TAB_NUM: dict[str, str] = {}
FIG_NUM: dict[str, str] = {}


def numerar(tex: str):
    ti = 0
    for m in re.finditer(re.escape(B + "begin{table") + r"\*?\}(.*?)"
                         + re.escape(B + "end{table"), tex, re.S):
        rot = chaves(m.group(1), "label")
        if rot:
            ti += 1
            TAB_NUM[rot] = f"TABLE {'I'*ti if ti<4 else ti}"
            REFS[rot] = f"{'I'*ti if ti<4 else ti}"
    romanos = {1: "I", 2: "II", 3: "III", 4: "IV", 5: "V"}
    for i, (rot, _) in enumerate(list(TAB_NUM.items()), 1):
        TAB_NUM[rot] = f"TABLE {romanos.get(i, i)}."
        REFS[rot] = romanos.get(i, str(i))
    fi = 0
    for m in re.finditer(re.escape(B + "begin{figure") + r"\*?\}(.*?)"
                         + re.escape(B + "end{figure"), tex, re.S):
        rot = chaves(m.group(1), "label")
        if rot:
            fi += 1
            FIG_NUM[rot] = f"Fig. {fi}."
            REFS[rot] = str(fi)
    romanos_sec = {1: "I", 2: "II", 3: "III", 4: "IV", 5: "V", 6: "VI", 7: "VII"}
    n_sec = 0
    for m in re.finditer(re.escape(B) + r"(section|label)\{([^}]*)\}", tex):
        if m.group(1) == "section":
            n_sec += 1
        elif m.group(2).startswith("sec:"):
            REFS[m.group(2)] = romanos_sec.get(n_sec, str(n_sec))


def _partir_listas(txt: str):
    """Separa um paragrafo em trechos de texto e ambientes enumerate/itemize."""
    saida = []
    pos = 0
    padrao = re.compile(re.escape(B) + r"begin\{(enumerate|itemize)\}")
    while True:
        m = padrao.search(txt, pos)
        if not m:
            saida.append(("texto", txt[pos:]))
            return saida
        saida.append(("texto", txt[pos:m.start()]))
        env = m.group(1)
        mf = re.search(re.escape(B) + r"end\{" + env + r"\}", txt[m.end():])
        if not mf:
            saida.append(("texto", txt[m.start():]))
            return saida
        saida.append((env, txt[m.end():m.end() + mf.start()]))
        pos = m.end() + mf.end()


def corpo_html(tex: str, chave2num) -> str:
    inicio = tex.index(B + "section{Introduction}")
    fim = tex.index(B + "begin{thebibliography}")
    corpo = tex[inicio:fim]

    partes: list[str] = []
    pos = 0
    padrao = re.compile(re.escape(B) + r"begin\{(table\*?|figure\*?|equation|align)\}", re.S)
    while True:
        m = padrao.search(corpo, pos)
        if not m:
            partes.append(("texto", corpo[pos:]))
            break
        partes.append(("texto", corpo[pos:m.start()]))
        env = m.group(1)
        fechar = re.escape(B) + r"end\{" + re.escape(env) + r"\}"
        mf = re.search(fechar, corpo[m.start():])
        bloco_env = corpo[m.start(): m.start() + mf.end()]
        partes.append((env, bloco_env))
        pos = m.start() + mf.end()

    saida: list[str] = []
    sec = 0
    romanos = {1: "I", 2: "II", 3: "III", 4: "IV", 5: "V", 6: "VI", 7: "VII"}
    for tipo, conteudo in partes:
        if tipo.startswith("table"):
            saida.append(tabela_html(conteudo, chave2num))
        elif tipo.startswith("figure"):
            saida.append(figura_html(conteudo, chave2num))
        elif tipo in ("equation", "align"):
            f = bloco(conteudo, tipo)
            f = re.sub(re.escape(B) + r"nonumber", "", f)
            f = re.sub(re.escape(B) + r"label\{[^}]*\}", "", f).strip()
            if tipo == "align":
                f = B + "begin{aligned}" + f + B + "end{aligned}"
            saida.append(f'<div class="eqn math-block">{html.escape(f)}</div>')
        else:
            def emitir(txt: str):
                """Converte um trecho de texto, tratando listas onde quer que apareçam."""
                for modo, corpo_txt in _partir_listas(txt):
                    if modo == "texto":
                        corpo_txt = re.sub(re.escape(B) + r"label\{[^}]*\}", "", corpo_txt)
                        if corpo_txt.strip():
                            saida.append(f"<p>{inline(corpo_txt.strip(), chave2num)}</p>")
                    else:
                        tag = "ol" if modo == "enumerate" else "ul"
                        itens = re.split(re.escape(B + "item"), corpo_txt)[1:]
                        saida.append(f"<{tag}>" + "".join(
                            f"<li>{inline(i.strip(), chave2num)}</li>" for i in itens)
                            + f"</{tag}>")

            for linha in re.split(r"\n\s*\n", conteudo):
                linha = linha.strip()
                if not linha:
                    continue
                if linha.startswith(B + "section*{"):
                    titulo_sec, fim_sec = chaves_pos(linha, "section*")
                    saida.append(f'<h2>{inline(titulo_sec, chave2num)}</h2>')
                    emitir(linha[fim_sec:])
                    continue
                if linha.startswith(B + "section{"):
                    sec += 1
                    titulo_sec, fim_sec = chaves_pos(linha, "section")
                    saida.append(f'<h2>{romanos.get(sec, sec)}. '
                                 f'{inline(titulo_sec, chave2num).upper()}</h2>')
                    emitir(linha[fim_sec:])
                    continue
                if linha.startswith(B + "subsection{"):
                    titulo_sub, fim_sub = chaves_pos(linha, "subsection")
                    saida.append(f'<h3><em>{inline(titulo_sub, chave2num)}</em></h3>')
                    emitir(linha[fim_sub:])
                    continue
                emitir(linha)
    return "\n".join(x for x in saida if x)


CSS = """
@page { size: A4; margin: 16mm 14mm; }
body { font-family: "Times New Roman", Times, serif; font-size: 9.4pt; line-height: 1.32;
       margin: 0; color: #000; }
.titulo { text-align: center; font-size: 20pt; font-weight: 700; margin: 0 0 10px;
          line-height: 1.18; }
.autores { text-align: center; font-size: 9pt; margin-bottom: 14px; }
.autores .linha { display: flex; justify-content: center; gap: 34px; margin-bottom: 8px; }
.autores .a { width: 44%; }
.autores .nome { font-weight: 600; }
.autores .af { font-style: italic; }
.cols { column-count: 2; column-gap: 6mm; }
h2 { font-size: 10pt; font-variant: small-caps; text-align: center; margin: 11px 0 5px;
     font-weight: 600; }
h3 { font-size: 9.6pt; margin: 9px 0 4px; font-weight: 500; }
p { margin: 0 0 5px; text-align: justify; text-indent: 1.2em; }
h2 + p, h3 + p, .cap + p { text-indent: 0; }
ol, ul { margin: 0 0 6px 0; padding-left: 16px; text-align: justify; }
li { margin-bottom: 3px; }
.resumo { font-size: 8.8pt; font-weight: 600; text-align: justify; margin-bottom: 6px; }
.chaves { font-size: 8.8pt; font-style: italic; margin-bottom: 10px; text-align: justify; }
.eqn { text-align: center; margin: 7px 0; font-style: italic; }
.figura, .tabela { break-inside: avoid; margin: 8px 0 10px; }
.figura.larga, .tabela.larga { column-span: all; }
.figura img { width: 100%; }
.cap { font-size: 8.1pt; text-align: justify; margin-top: 4px; }
.tabela .cap { text-align: center; margin: 0 0 4px; font-variant: small-caps; }
table { width: 100%; border-collapse: collapse; font-size: 7.1pt; }
th, td { padding: 1.6px 3px; text-align: center; }
th { border-top: 0.9px solid #000; border-bottom: 0.6px solid #000; font-weight: 700; }
tr:last-child td { border-bottom: 0.9px solid #000; }
td:nth-child(2), th:nth-child(2) { text-align: left; }
.refs { font-size: 8.1pt; }
.refs ol { padding-left: 18px; }
.refs li { margin-bottom: 2px; text-align: justify; }
"""


def main():
    tex = TEX.read_text(encoding="utf-8")
    numerar(tex)
    bib = bibliografia(tex)
    chave2num = {k: i for i, (k, _) in enumerate(bib, 1)}

    titulo = chaves(tex, "title")
    resumo = bloco(tex, "abstract")
    palavras = bloco(tex, "IEEEkeywords")

    autores = [
        ("Kaio Emanuel Lima de Matos", "Graduate Program in Electrical Engineering (PPGEE)",
         "Federal University of Cear\u00e1 (UFC), Fortaleza, Cear\u00e1, Brazil",
         "kaio.emanuel@alu.ufc.br"),
        ("Francisco Soares da Silva J\u00fanior", "Graduate Program in Electrical Engineering (PPGEE)",
         "Federal University of Cear\u00e1 (UFC), Fortaleza, Cear\u00e1, Brazil",
         "juniorsoares@alu.ufc.br"),
        ("Daniel Santos da Silva", "Department of Teleinformatics Engineering (DETI)",
         "Federal University of Cear\u00e1 (UFC), Fortaleza, Brazil", "danielssilva@alu.ufc.br"),
        ("Victor Hugo C. de Albuquerque", "Department of Teleinformatics Engineering (DETI)",
         "Federal University of Cear\u00e1 (UFC), Fortaleza, Brazil", "victor.albuquerque@ieee.org"),
    ]
    blocos_autor = ""
    for i in (0, 2):
        blocos_autor += '<div class="linha">'
        for j in (i, i + 1):
            n, af1, af2, mail = autores[j]
            blocos_autor += (f'<div class="a"><div class="nome">{j+1}<sup>'
                             f'{["st","nd","rd","th"][min(j,3)]}</sup> {n}</div>'
                             f'<div class="af">{af1}</div><div class="af">{af2}</div>'
                             f'<div>{mail}</div></div>')
        blocos_autor += "</div>"

    refs = "".join(f"<li>{inline(t, chave2num)}</li>" for _, t in bib)

    doc = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><title>{html.escape(titulo)}</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"></script>
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js"
 onload="document.querySelectorAll('.math').forEach(e=>{{try{{katex.render(e.textContent,e,{{throwOnError:false}});}}catch(x){{}}}});
         document.querySelectorAll('.math-block').forEach(e=>{{try{{katex.render(e.textContent,e,{{displayMode:true,throwOnError:false}});}}catch(x){{}}}});"></script>
<style>{CSS}</style></head><body>
<div class="titulo">{inline(titulo, chave2num)}</div>
<div class="autores">{blocos_autor}</div>
<div class="cols">
<div class="resumo"><em>Abstract</em>&mdash;{inline(resumo, chave2num)}</div>
<div class="chaves"><strong>Index Terms</strong>&mdash;{inline(palavras, chave2num)}</div>
{corpo_html(tex, chave2num)}
<h2>References</h2>
<div class="refs"><ol>{refs}</ol></div>
</div></body></html>"""

    HTML_OUT.parent.mkdir(parents=True, exist_ok=True)
    HTML_OUT.write_text(doc, encoding="utf-8")
    print(f"[1/2] HTML: {HTML_OUT}")

    navegadores = [
        Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
        Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
        Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
        Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
    ]
    nav = next((n for n in navegadores if n.exists()), None)
    if nav is None:
        print("[2/2] nenhum navegador headless encontrado; PDF não gerado.")
        return 1
    cmd = [str(nav), "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
           "--virtual-time-budget=15000",
           f"--print-to-pdf={PDF_OUT}", f"file:///{HTML_OUT.as_posix()}"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode == 0 and PDF_OUT.exists():
        print(f"[2/2] PDF: {PDF_OUT} ({PDF_OUT.stat().st_size/1024:.0f} KB)")
        return 0
    print("[2/2] falha:", r.stderr[:500])
    return 1


if __name__ == "__main__":
    sys.exit(main())
