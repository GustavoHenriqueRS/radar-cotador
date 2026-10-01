import threading
from dataclasses import dataclass
from pathlib import Path

import pdfplumber

# O PDFium não é thread-safe, nem entre documentos diferentes: todo uso do pypdfium2 passa por esta trava.
TRAVA_PDFIUM = threading.Lock()
# Diferença mínima de tom (0–255) sob a palavra, na página desenhada, para ela contar como visível.
CONTRASTE_VISIVEL = 20


@dataclass(frozen=True)
class Palavra:
    texto: str
    x0: float
    x1: float
    topo: float
    base: float
    pagina: int  # 1-indexed
    horizontal: bool = True

    @property
    def xc(self) -> float:
        return (self.x0 + self.x1) / 2

    @property
    def yc(self) -> float:
        return (self.topo + self.base) / 2

    def caixa(self) -> list[float]:
        return [round(self.x0, 1), round(self.topo, 1), round(self.x1, 1), round(self.base, 1)]


@dataclass
class Pagina:
    numero: int
    largura: float
    altura: float
    palavras: list[Palavra]

    def linhas(self, tolerancia: float = 2.5) -> list[list[Palavra]]:
        """Agrupa palavras horizontais em linhas pela altura média; cada linha vem da esquerda para a direita.

        Texto girado (ex.: "COPARTICIPAÇÃO" na vertical ao lado da tabela) fica de fora,
        senão ele puxa a linha para cima e separa o rótulo da faixa dos seus valores.
        """
        linhas: list[list[Palavra]] = []
        medias: list[float] = []
        for p in sorted((p for p in self.palavras if p.horizontal), key=lambda p: (p.yc, p.x0)):
            if linhas and abs(medias[-1] - p.yc) <= tolerancia:
                linhas[-1].append(p)
                medias[-1] += (p.yc - medias[-1]) / len(linhas[-1])
            else:
                linhas.append([p])
                medias.append(p.yc)
        return [sorted(linha, key=lambda p: p.x0) for linha in linhas]


def ler_paginas(caminho: str | Path, somente_visiveis: bool = True) -> list[Pagina]:
    paginas = []
    with pdfplumber.open(caminho) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            if somente_visiveis:
                page = _sem_texto_coberto(page)
            palavras = [
                Palavra(w["text"], w["x0"], w["x1"], w["top"], w["bottom"], i, bool(w.get("upright", True)))
                for w in page.extract_words(keep_blank_chars=False, use_text_flow=False, x_tolerance=1.5)
            ]
            paginas.append(Pagina(i, float(page.width), float(page.height), palavras))
    if somente_visiveis:
        _descartar_invisiveis(caminho, paginas)
    return paginas


BALDE = 50


def _baldes(caixa) -> list[tuple[int, int]]:
    x0, y0, x1, y1 = caixa
    return [(bx, by) for bx in range(int(x0) // BALDE, int(x1) // BALDE + 1) for by in range(int(y0) // BALDE, int(y1) // BALDE + 1)]


def _sobrepoe(a, b) -> bool:
    largura = min(a.x1, b.x1) - max(a.x0, b.x0)
    altura = min(a.y1, b.y1) - max(a.y0, b.y0)
    menor = min((a.x1 - a.x0) * (a.y1 - a.y0), (b.x1 - b.x0) * (b.y1 - b.y0))
    return largura > 0 and altura > 0 and menor > 0 and largura * altura >= 0.3 * menor


def _sem_texto_coberto(page):
    """A página sem as letras que ninguém vê: cópia do negrito falso e camada de texto que ficou por baixo de outra.

    - Negrito falso: a mesma letra desenhada duas vezes no mesmo lugar vira "0000--1188" em vez de "00-18"
      (CORPe, Hapvida BH). Fica uma cópia.
    - Camadas (na CNU, a tabela de um ano embaixo, o fundo das células por cima e a do ano seguinte por cima
      de tudo): o texto das duas se mistura letra a letra ("R$ 1.217,09" e "R$ 1.264,01" viram
      "11..212667,0,419"), mas na página desenhada só a de cima aparece. Vale a ordem de desenho.

    O fundo desenhado depois do texto só conta como tampa quando a página tem mesmo camadas empilhadas
    (letras de outra fonte desenhadas por cima de letras): fundo com transparência, que o pdfminer não
    enxerga, aparece em página comum (faixas zebradas) e ali não esconde nada.
    """
    from pdfminer.layout import LTChar, LTCurve

    ordem: list[tuple[str, object]] = []

    def percorrer(objetos):
        for o in objetos:
            if isinstance(o, LTChar):
                ordem.append(("letra", o))
            elif isinstance(o, LTCurve) and o.fill:
                ordem.append(("fundo", o))
            elif hasattr(o, "__iter__"):
                percorrer(o)

    percorrer(page.layout)
    letras = [o for tipo, o in ordem if tipo == "letra"]
    chars = page.chars
    # As letras do pdfplumber são as mesmas do pdfminer, na mesma ordem; se não forem, melhor não mexer.
    if len(chars) != len(letras) or any(c["text"] != o.get_text() for c, o in zip(chars, letras)):
        return page
    indice = {id(o): i for i, o in enumerate(letras)}

    duplicadas: set[int] = set()
    vistas: dict[tuple, list] = {}
    for i, o in enumerate(letras):
        chave = (o.get_text(), o.fontname, round(o.size, 1))
        x, y = round(o.x0), round(o.y0)
        perto = [v for dx in (-1, 0, 1) for dy in (-1, 0, 1) for v in vistas.get((chave, x + dx, y + dy), [])]
        if any(abs(v.x0 - o.x0) <= 1 and abs(v.y0 - o.y0) <= 1 for v in perto):
            duplicadas.add(i)
        else:
            vistas.setdefault((chave, x, y), []).append(o)

    area_pagina = float(page.width) * float(page.height)
    letras_depois: dict[tuple[int, int], list] = {}
    fundos_depois: dict[tuple[int, int], list] = {}
    sob_letra, sob_fundo = set(), set()
    # De trás para frente: ao chegar numa letra, tudo o que já foi visto foi desenhado depois dela.
    for tipo, o in reversed(ordem):
        caixa = (o.x0, o.y0, o.x1, o.y1)
        if tipo == "fundo":
            # Fundo do tamanho da página costuma ser marca d'água, não tampa.
            if (o.x1 - o.x0) * (o.y1 - o.y0) < 0.5 * area_pagina:
                for b in _baldes(caixa):
                    fundos_depois.setdefault(b, []).append(o)
            continue
        i = indice[id(o)]
        if i in duplicadas:
            continue
        camada = (o.fontname, round(o.size, 1))
        if any(_sobrepoe(o, outra) and (outra.fontname, round(outra.size, 1)) != camada
               for b in _baldes(caixa) for outra in letras_depois.get(b, [])):
            sob_letra.add(i)
        x, y = (o.x0 + o.x1) / 2, (o.y0 + o.y1) / 2
        if any(f.x0 <= x <= f.x1 and f.y0 <= y <= f.y1 for f in fundos_depois.get((int(x) // BALDE, int(y) // BALDE), [])):
            sob_fundo.add(i)
        for b in _baldes(caixa):
            letras_depois.setdefault(b, []).append(o)
    remover = set(duplicadas)
    camadas = len(sob_letra) >= 0.05 * len(letras) and len(sob_letra | sob_fundo) <= 0.6 * len(letras)
    if camadas:
        remover |= sob_letra | sob_fundo
    if not remover:
        return page
    tirar = {id(chars[i]) for i in remover}
    return page.filter(lambda o: id(o) not in tirar)


def _descartar_invisiveis(caminho: str | Path, paginas: list[Pagina]):
    """Tira as palavras que não aparecem na página desenhada: texto tapado, recortado, branco ou invisível.

    O PDF pode carregar texto que ninguém vê (no acervo, uma coluna de preços copiada e escondida na
    borda da tabela). A leitura geométrica deve ler só o que uma pessoa leria.
    """
    import numpy as np
    import pypdfium2 as pdfium

    with TRAVA_PDFIUM:
        documento = pdfium.PdfDocument(str(caminho))
        try:
            for pagina in paginas:
                page = documento[pagina.numero - 1]
                largura, altura = page.get_size()
                # Página girada ou com coordenadas que não batem: melhor não filtrar do que filtrar errado.
                if not pagina.palavras or page.get_rotation() or abs(largura - pagina.largura) > 1 or abs(altura - pagina.altura) > 1:
                    continue
                pixels = np.asarray(page.render(scale=1).to_pil().convert("L"), dtype=np.int16)
                visiveis = [p for p in pagina.palavras if _contraste(pixels, p) >= CONTRASTE_VISIVEL]
                if len(visiveis) >= 0.7 * len(pagina.palavras):
                    pagina.palavras = visiveis
        finally:
            documento.close()


def _contraste(pixels, p: Palavra) -> int:
    regiao = pixels[max(0, int(p.topo)):int(p.base) + 1, max(0, int(p.x0)):int(p.x1) + 1]
    return int(regiao.max() - regiao.min()) if regiao.size else 0


def tem_camada_de_texto(paginas: list[Pagina]) -> bool:
    return sum(len(p.palavras) for p in paginas) >= 20 * max(1, len(paginas)) // 2
