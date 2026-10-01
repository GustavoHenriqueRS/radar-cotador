"""OCR para PDFs sem camada de texto (escaneados, prints, fotos).

Usa o RapidOCR (modelos ONNX, roda local e sem pacote do sistema). As palavras voltam
nas mesmas coordenadas em pontos do PDF, então o leitor geométrico funciona igual.
A inclinação típica de scanner é estimada pelas caixas de texto e desfeita antes.
"""
import logging
import math
from functools import lru_cache
from pathlib import Path
from statistics import median

import numpy as np
import pypdfium2 as pdfium

from .pdf import TRAVA_PDFIUM, Pagina, Palavra

DPI = 200


@lru_cache(maxsize=1)
def _motor():
    from rapidocr import RapidOCR

    logging.getLogger("RapidOCR").setLevel(logging.WARNING)
    return RapidOCR()


def _inclinacao(caixas) -> float:
    """Ângulo mediano (radianos) da borda superior das linhas de texto largas."""
    angulos = []
    for caixa in caixas:
        (x0, y0), (x1, y1) = caixa[0], caixa[1]
        if x1 - x0 > 80:
            angulos.append(math.atan2(y1 - y0, x1 - x0))
    return median(angulos) if angulos else 0.0


def paginas_por_ocr(caminho: Path, dpi: int = DPI) -> list[Pagina]:
    motor = _motor()
    escala = dpi / 72
    with TRAVA_PDFIUM:
        documento = pdfium.PdfDocument(str(caminho))
        try:
            renderizadas = [(page.get_size(), page.render(scale=escala).to_pil().convert("RGB")) for page in documento]
        finally:
            documento.close()
    paginas = []
    for numero, ((largura, altura), imagem) in enumerate(renderizadas, start=1):
        r = motor(np.asarray(imagem), return_word_box=True)
        if r.boxes is None:
            paginas.append(Pagina(numero, largura, altura, []))
            continue
        angulo = _inclinacao(r.boxes)
        cx, cy = imagem.width / 2, imagem.height / 2
        cos, sen = math.cos(-angulo), math.sin(-angulo)

        def endireitar(x, y):
            dx, dy = x - cx, y - cy
            return cx + dx * cos - dy * sen, cy + dx * sen + dy * cos

        palavras = []
        for linha_palavras, caixa_linha in zip(r.word_results or [], r.boxes):
            itens = linha_palavras or []
            if not itens:
                continue
            for texto, _score, caixa in itens:
                pontos = [endireitar(x, y) for x, y in caixa]
                xs, ys = [p[0] for p in pontos], [p[1] for p in pontos]
                x0, x1, y0, y1 = min(xs) / escala, max(xs) / escala, min(ys) / escala, max(ys) / escala
                horizontal = (x1 - x0) >= (y1 - y0) * 0.6 or len(texto) <= 2
                palavras.append(Palavra(texto, x0, x1, y0, y1, numero, horizontal))
        paginas.append(Pagina(numero, largura, altura, _juntar_moeda(palavras)))
    return paginas


def _juntar_moeda(palavras: list[Palavra]) -> list[Palavra]:
    """O OCR às vezes separa 'R$' de '178,43' ou quebra '1.065,14' em '1.065' ',14'; junta vizinhos colados."""
    ordenadas = sorted(palavras, key=lambda p: (p.pagina, round(p.yc / 3), p.x0))
    saida: list[Palavra] = []
    for p in ordenadas:
        anterior = saida[-1] if saida else None
        colado = anterior is not None and abs(anterior.yc - p.yc) < 3 and 0 <= p.x0 - anterior.x1 < 2.5
        if colado and (p.texto.startswith(",") or anterior.texto.endswith(",")):
            saida[-1] = Palavra(anterior.texto + p.texto, anterior.x0, p.x1, min(anterior.topo, p.topo),
                                max(anterior.base, p.base), p.pagina, anterior.horizontal)
        else:
            saida.append(p)
    return saida
