"""Gera os slides em PDF (16:9) a partir de docs/slides.md: um slide por bloco separado por ---.

Cada bloco pode começar com <!-- classe: capa|numeros|figura --> e <!-- rotulo: texto -->. A impressão é a mesma
dos outros PDFs (scripts/gerar_pdfs.py).
Uso: python3 scripts/gerar_slides.py
"""
import html
import re
import sys
from pathlib import Path

from markdown_it import MarkdownIt

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gerar_pdfs import FONTES, RAIZ, SAIDA, imagens, imprimir  # noqa: E402

ORIGEM = RAIZ / "docs" / "slides.md"
MARCA = re.compile(r"^<!--\s*(classe|rotulo):\s*(.+?)\s*-->\s*$", re.M)
GRADE = ("url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='40' height='40'%3E%3Cpath d='M.5 40V.5H40' "
         "fill='none' stroke='%237dd3fc' stroke-opacity='.12'/%3E%3C/svg%3E\")")

CSS = """
@page { size: 1280px 720px; margin: 0; }
html { font-family: 'Fira Sans', sans-serif; color: #1e293b; }
body { margin: 0; }
.slide { width: 1280px; height: 720px; padding: 60px 84px 64px; box-sizing: border-box; position: relative; overflow: hidden;
  break-after: page; background: #fff; display: flex; flex-direction: column; }
.rotulo { font-family: 'Fira Code', monospace; font-size: 15px; text-transform: uppercase; letter-spacing: .14em; color: #0369a1; margin: 0; }
.slide h2 { font-size: 40px; line-height: 1.15; margin: 10px 0 30px; color: #0f172a; font-weight: 600; letter-spacing: -.01em; max-width: 1040px; }
.slide p, .slide li { font-size: 24px; line-height: 1.42; }
.slide p { margin: 0 0 16px; }
.slide ul, .slide ol { margin: 0 0 20px; padding-left: 30px; }
.slide li { margin: 0 0 12px; padding-left: 4px; }
.slide li::marker { color: #0369a1; font-weight: 600; }
.slide strong { color: #0f172a; font-weight: 600; }
.slide code { font-family: 'Fira Code', monospace; background: #f1f5f9; padding: 2px 8px; border-radius: 6px; font-size: .88em; }
.slide table { border-collapse: collapse; width: 100%; font-size: 20px; line-height: 1.35; margin-bottom: 22px; }
.slide th { background: #0f172a; color: #fff; text-align: left; padding: 12px 16px; font-weight: 500; }
.slide td { padding: 12px 16px; border-bottom: 1px solid #e2e8f0; vertical-align: top; }
.slide tbody tr:nth-child(even) td { background: #f8fafc; }
footer { position: absolute; left: 84px; right: 84px; bottom: 26px; display: flex; justify-content: space-between; font-size: 14px; color: #94a3b8; }
.capa { background: #0f172a %GRADE%; color: #cbd5e1; justify-content: center; }
.capa h1 { font-size: 76px; line-height: 1.05; color: #fff; margin: 0 0 18px; font-weight: 600; letter-spacing: -.02em; }
.capa p { font-size: 28px; color: #cbd5e1; margin: 0 0 14px; }
.capa p:last-child { font-size: 20px; color: #94a3b8; margin-top: 30px; }
.capa strong { color: #fff; }
.capa code { background: #1e293b; color: #e2e8f0; }
.numeros ul { list-style: none; padding: 0; display: grid; grid-template-columns: 1fr 1fr; gap: 22px; }
.numeros li { border: 1px solid #e2e8f0; border-radius: 16px; padding: 22px 28px; font-size: 20px; line-height: 1.4; color: #475569; margin: 0; }
.numeros li strong { display: block; font-size: 54px; line-height: 1.1; color: #0f172a; margin-bottom: 6px; letter-spacing: -.01em; }
.figura img { width: 100%; max-height: 500px; object-fit: contain; margin-top: 4px; }
"""


def montar() -> str:
    md = MarkdownIt("commonmark", {"html": False}).enable("table")
    blocos = [b for b in re.split(r"^---\s*$", ORIGEM.read_text(encoding="utf-8"), flags=re.M) if b.strip()]
    slides = []
    for numero, bloco in enumerate(blocos, start=1):
        meta = dict(MARCA.findall(bloco))
        classe = meta.get("classe", "conteudo")
        corpo = imagens(md.render(MARCA.sub("", bloco).strip()), ORIGEM.parent)
        rotulo = f'<p class="rotulo">{html.escape(meta["rotulo"])}</p>' if "rotulo" in meta else ""
        rodape = "" if classe == "capa" else f"<footer><span>Radar do Cotador</span><span>{numero} de {len(blocos)}</span></footer>"
        slides.append(f'<section class="slide {classe}">{rotulo}{corpo}{rodape}</section>')
    folhas = "".join(f'<link rel="stylesheet" href="{(FONTES / c).as_uri()}">' for c in (
        "fira-sans/400.css", "fira-sans/500.css", "fira-sans/600.css", "fira-code/400.css"))
    return (f'<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><title>Radar do Cotador · Apresentação</title>'
            f'<meta name="author" content="Gustavo Henrique">{folhas}<style>{CSS.replace("%GRADE%", GRADE)}</style></head>'
            f'<body>{"".join(slides)}</body></html>')


if __name__ == "__main__":
    destino = SAIDA / "slides.pdf"
    SAIDA.mkdir(parents=True, exist_ok=True)
    imprimir(montar(), destino)
    print(f"{destino.relative_to(RAIZ)}: {destino.stat().st_size / 1024:.0f} KB")
