"""Gera os PDFs da documentação a partir do Markdown: capa, sumário com links, número de página e a fonte da interface.

O PDF é a impressão do Chrome sem interface de um HTML montado aqui, então sai igual em qualquer máquina com o
Chrome e o `markdown-it-py`. A fonte vem do `frontend/node_modules` (rode `npm install` em `frontend/` antes).
Uso: python3 scripts/gerar_pdfs.py [nome ...]
"""
import html
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
from pathlib import Path

from markdown_it import MarkdownIt

RAIZ = Path(__file__).resolve().parent.parent
SAIDA = RAIZ / "docs" / "pdf"
FONTES = RAIZ / "frontend" / "node_modules" / "@fontsource"
REPOSITORIO = "https://github.com/GustavoHenriqueRS/radar-cotador"
DEMO = "https://gustavohenriquers.github.io/radar-cotador/"
VIDEO = DEMO + "video/radar-cotador-demo.mp4"
RESUMO = DEMO + "video/radar-cotador-motion.mp4"
OPERADORAS = ["bradesco_saude", "sulamerica_saude", "amil", "notredame_intermedica", "hapvida",
              "central_nacional_unimed", "smile_saude", "quallity_pro_saude", "saude_sim"]

DOCUMENTOS = {
    "proposta": {"arquivos": ["docs/proposta.md"], "titulo": "Proposta",
                 "subtitulo": "Dados do Cotador obtidos, conferidos e atualizados sem digitação", "sumario": True},
    "detalhes-tecnicos": {"arquivos": ["docs/detalhes-tecnicos.md"], "titulo": "Detalhes técnicos",
                          "subtitulo": "As medições, as regras e as tabelas por trás de cada número", "sumario": True},
    "como-evoluir": {"arquivos": ["docs/como-evoluir.md"], "titulo": "Como evoluir o Radar",
                     "subtitulo": "Princípios, receitas de extensão, escala e próximos passos", "sumario": True},
    "operadoras": {"arquivos": [f"docs/operadoras/{n}.md" for n in OPERADORAS], "titulo": "As 9 operadoras do Cotador",
                   "subtitulo": "Canais, robots.txt, termos de uso, amostras lidas e números da ANS, uma a uma", "sumario": True},
    "pesquisa": {"arquivos": ["docs/pesquisa/fontes-e-achados.md"], "titulo": "Pesquisa",
                 "subtitulo": "Fontes de dados, achados e embasamento regulatório", "sumario": True},
    "roteiro-demo": {"arquivos": ["docs/roteiro-demo.md"], "titulo": "Roteiro da demonstração",
                     "subtitulo": "O protótipo em cinco minutos", "sumario": False},
}

LARGURA_UTIL_PT = 462  # A4 menos as margens laterais de 18 mm e o recuo do bloco de código
AUTORIA = re.compile(r"^\*\*Gustavo Henrique\*\*.*$", re.M)


def ancora(texto: str, usadas: set) -> str:
    base = unicodedata.normalize("NFKD", re.sub(r"<[^>]+>", "", texto)).encode("ascii", "ignore").decode().lower()
    base = re.sub(r"[^a-z0-9]+", "-", base).strip("-") or "secao"
    nome, n = base, 2
    while nome in usadas:
        nome, n = f"{base}-{n}", n + 1
    usadas.add(nome)
    return nome


def quebras(html_texto: str) -> str:
    """Endereços e caminhos longos ganham pontos de quebra nas barras e nos pontos; palavras comuns ficam inteiras."""
    def no_texto(trecho: str) -> str:
        return re.sub(r"[^\s<>]{24,}", lambda m: re.sub(r"([/._?=&-])", r"\1<wbr>", m.group(0)), trecho)
    return "".join(parte if parte.startswith("<") else no_texto(parte) for parte in re.split(r"(<[^>]+>)", html_texto))


def imagens(html_texto: str, pasta: Path) -> str:
    """O HTML do PDF é montado numa pasta temporária: imagem com caminho relativo passa a apontar para o arquivo."""
    return re.sub(r'<img src="(?!https?:|data:)([^"]+)"', lambda m: f'<img src="{(pasta / m.group(1)).resolve().as_uri()}"', html_texto)


def renderizar(markdown: str, usadas: set, sumario: list, nivel_capitulo: int) -> str:
    md = MarkdownIt("commonmark", {"html": False, "typographer": False}).enable("table")
    tokens = md.parse(markdown)
    for i, tok in enumerate(tokens):
        if tok.type == "heading_open":
            texto = tokens[i + 1].content
            tok.attrSet("id", ancora(texto, usadas))
            nivel = int(tok.tag[1])
            if nivel in (nivel_capitulo, nivel_capitulo + 1):
                sumario.append((nivel - nivel_capitulo, texto, tok.attrGet("id")))
        elif tok.type == "fence":
            maior = max((len(linha) for linha in tok.content.splitlines()), default=0)
            corpo = min(8.0, LARGURA_UTIL_PT / max(maior, 1) / 0.62)
            tok.attrSet("style", f"font-size:{corpo:.2f}pt")
    saida = md.renderer.render(tokens, md.options, {})
    return quebras(re.sub(r'<pre><code([^>]*)>', lambda m: "<pre" + m.group(1) + "><code>", saida))


def montar(nome: str, doc: dict) -> str:
    usadas, sumario, partes = set(), [], []
    autoria = ""
    for caminho in doc["arquivos"]:
        texto = (RAIZ / caminho).read_text(encoding="utf-8")
        if len(doc["arquivos"]) == 1:
            texto = re.sub(r"^# .+\n", "", texto, count=1)
            if m := AUTORIA.search(texto):
                autoria = m.group(0)
                texto = texto.replace(autoria, "", 1)
            partes.append(imagens(renderizar(texto, usadas, sumario, 2), (RAIZ / caminho).parent))
        else:
            partes.append('<section class="capitulo">' + imagens(renderizar(texto, usadas, sumario, 1), (RAIZ / caminho).parent) + "</section>")
    corpo = "\n".join(partes)
    linhas_sumario = "".join(
        f'<li class="n{nivel}"><a href="#{alvo}">{html.escape(re.sub(r"[*`]", "", texto))}</a></li>'
        for nivel, texto, alvo in sumario if nivel <= (0 if len(sumario) > 40 else 1))
    bloco_sumario = f'<nav class="sumario"><h2>Sumário</h2><ol>{linhas_sumario}</ol></nav>' if doc["sumario"] and sumario else ""
    autoria_html = MarkdownIt().renderInline(autoria) if autoria else "Radar do Cotador · proposta para o Cotador de Planos de Saúde"
    folhas = "".join(f'<link rel="stylesheet" href="{(FONTES / caminho).as_uri()}">' for caminho in (
        "fira-sans/400.css", "fira-sans/400-italic.css", "fira-sans/500.css", "fira-sans/600.css", "fira-sans/700.css",
        "fira-code/400.css", "fira-code/600.css"))
    return f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8">
<title>Radar do Cotador · {html.escape(doc["titulo"])}</title>
<meta name="author" content="Gustavo Henrique">
{folhas}
<style>{CSS.replace("%RODAPE%", "Radar do Cotador · " + doc["titulo"])}</style>
</head><body>
<section class="capa">
  <div class="marca"><span class="icone"></span>Radar do Cotador</div>
  <div class="titulo">
    <h1>{html.escape(doc["titulo"])}</h1>
    <p class="subtitulo">{html.escape(doc["subtitulo"])}</p>
  </div>
  <div class="rodape-capa">
    <p>{autoria_html}</p>
    <p>Código e documentação: <a href="{REPOSITORIO}">{REPOSITORIO.removeprefix("https://")}</a></p>
    <p>Protótipo no navegador: <a href="{DEMO}">{DEMO.removeprefix("https://").rstrip("/")}</a></p>
    <p>Resumo em vídeo (41 s): <a href="{RESUMO}">{RESUMO.removeprefix("https://")}</a></p>
    <p>Demonstração completa (1 min 36 s): <a href="{VIDEO}">{VIDEO.removeprefix("https://")}</a></p>
  </div>
</section>
{bloco_sumario}
<main>{corpo}</main>
</body></html>"""


CSS = """
@page { size: A4; margin: 20mm 18mm 18mm 18mm;
  @bottom-left { content: "%RODAPE%"; font: 400 7.5pt 'Fira Sans', sans-serif; color: #64748b; }
  @bottom-right { content: counter(page) " de " counter(pages); font: 400 7.5pt 'Fira Sans', sans-serif; color: #64748b; } }
@page :first { margin: 0; @bottom-left { content: none; } @bottom-right { content: none; } }
* { box-sizing: border-box; }
html { font-family: 'Fira Sans', sans-serif; font-size: 9.6pt; line-height: 1.5; color: #1e293b; }
body { margin: 0; }
a { color: #0369a1; text-decoration: none; }
.capa { height: 297mm; padding: 26mm 22mm 22mm; display: flex; flex-direction: column; justify-content: space-between;
  background: #0f172a; color: #e2e8f0; break-after: page; }
.capa a { color: #7dd3fc; }
.marca { display: flex; align-items: center; gap: 10px; font-weight: 600; font-size: 12pt; color: #fff; }
.icone { width: 26px; height: 26px; border-radius: 6px; background: #0369a1 url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Cpath d='M27 16h-4.3l-3.2 9.5-6-19-3.2 9.5H5' fill='none' stroke='white' stroke-width='2.6' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E") center/18px no-repeat; }
.capa h1 { font-size: 34pt; line-height: 1.1; margin: 0 0 6mm; color: #fff; font-weight: 600; }
.subtitulo { font-size: 14pt; color: #cbd5e1; margin: 0; max-width: 140mm; }
.rodape-capa { font-size: 9.5pt; color: #94a3b8; border-top: 1px solid #334155; padding-top: 6mm; }
.rodape-capa p { margin: 1.5mm 0; }
.rodape-capa strong { color: #fff; font-weight: 600; }
.sumario { break-after: page; }
.sumario h2 { margin-top: 0; }
.sumario ol { list-style: none; padding: 0; margin: 0; columns: 1; }
.sumario li { margin: 1.6mm 0; }
.sumario li.n0 { font-weight: 500; }
.sumario li.n1 { padding-left: 6mm; color: #475569; }
.sumario a { color: inherit; }
h1, h2, h3, h4 { color: #0f172a; font-weight: 600; line-height: 1.25; break-after: avoid; }
main h1 { font-size: 19pt; margin: 0 0 5mm; padding-bottom: 2mm; border-bottom: 2px solid #0369a1; }
h2 { font-size: 14pt; margin: 9mm 0 3mm; padding-top: 2mm; border-top: 1px solid #e2e8f0; }
h3 { font-size: 11pt; margin: 6mm 0 2mm; }
h4 { font-size: 10pt; margin: 4mm 0 1.5mm; }
.capitulo { break-before: page; }
p { margin: 0 0 2.6mm; orphans: 3; widows: 3; }
ul, ol { margin: 0 0 3mm; padding-left: 5.5mm; }
li { margin: 0.8mm 0; }
li > ul, li > ol { margin: 0.8mm 0 1mm; }
strong { font-weight: 600; color: #0f172a; }
code { font-family: 'Fira Code', monospace; font-size: 0.86em; background: #f1f5f9; border-radius: 3px; padding: 0.2mm 1mm; overflow-wrap: break-word; }
pre { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 5px; padding: 3mm; margin: 2mm 0 4mm; overflow: hidden;
  white-space: pre; line-height: 1.35; break-inside: avoid; }
pre code { background: none; padding: 0; font-size: inherit; overflow-wrap: normal; }
blockquote { margin: 0 0 4mm; padding: 2.5mm 4mm; border-left: 3px solid #0369a1; background: #f0f9ff; color: #0c4a6e; break-inside: avoid; }
blockquote p:last-child, blockquote ul:last-child { margin-bottom: 0; }
table { width: 100%; border-collapse: collapse; margin: 2mm 0 5mm; font-size: 8.4pt; line-height: 1.4; }
thead { display: table-header-group; }
th { background: #0f172a; color: #fff; font-weight: 500; text-align: left; padding: 1.6mm 2mm; }
td { padding: 1.5mm 2mm; border-bottom: 1px solid #e2e8f0; vertical-align: top; overflow-wrap: break-word; }
th { overflow-wrap: break-word; }
tr { break-inside: avoid; }
tbody tr:nth-child(even) td { background: #f8fafc; }
hr { border: 0; border-top: 1px solid #e2e8f0; margin: 6mm 0; }
img { max-width: 100%; display: block; margin: 3mm auto 5mm; break-inside: avoid; }
"""


def imprimir(html_texto: str, destino: Path) -> None:
    chrome = shutil.which("google-chrome") or shutil.which("chromium") or shutil.which("chromium-browser")
    if not chrome:
        raise SystemExit("precisa do Chrome ou do Chromium para imprimir o PDF")
    with tempfile.TemporaryDirectory() as tmp:
        pagina = Path(tmp) / "documento.html"
        pagina.write_text(html_texto, encoding="utf-8")
        subprocess.run([chrome, "--headless=new", "--disable-gpu", "--no-first-run", f"--user-data-dir={tmp}/perfil",
                        "--no-pdf-header-footer", "--allow-file-access-from-files", "--virtual-time-budget=8000",
                        f"--print-to-pdf={destino}", pagina.as_uri()],
                       check=True, capture_output=True, timeout=180)


if __name__ == "__main__":
    nomes = sys.argv[1:] or list(DOCUMENTOS)
    SAIDA.mkdir(parents=True, exist_ok=True)
    for nome in nomes:
        destino = SAIDA / f"{nome}.pdf"
        imprimir(montar(nome, DOCUMENTOS[nome]), destino)
        print(f"{destino.relative_to(RAIZ)}: {destino.stat().st_size / 1024:.0f} KB")
