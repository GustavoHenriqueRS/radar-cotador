"""Leitura geométrica da grade faixa etária × coluna.

Não usa LLM: acha os rótulos de faixa etária da ANS, pega os valores em reais à
direita de cada rótulo e associa cada coluna ao registro ANS impresso no
cabeçalho pela posição horizontal. É determinístico, gratuito e aponta a
posição exata de cada número no PDF.
"""
import re
from dataclasses import dataclass, field
from statistics import median

from .condicoes import combinar, marcas
from .faixas import FAIXAS, RE_MOEDA, RE_REGISTRO_ANS, faixa_do_rotulo, formatar_registro, moeda
from .pdf import Pagina, Palavra


@dataclass
class Coluna:
    indice: int
    x: float
    registro: str | None = None  # CD_PLANO (9 dígitos)
    palavra_registro: Palavra | None = None
    cabecalho: str = ""


@dataclass
class TabelaGeometrica:
    pagina: int
    colunas: list[Coluna]
    # (índice da coluna, índice da faixa) -> palavra com o valor
    celulas: dict[tuple[int, int], Palavra] = field(default_factory=dict)
    contexto: str = ""
    titulo: str = ""
    condicao: list[str] = field(default_factory=list)
    topo: float = 0.0
    base: float = 0.0
    x0: float = 0.0
    x1: float = 0.0

    def valor(self, coluna: int, faixa: int) -> float | None:
        p = self.celulas.get((coluna, faixa))
        return moeda(_texto_moeda(p.texto)) if p else None

    def serie(self, coluna: int) -> list[float | None]:
        return [self.valor(coluna, f) for f in range(10)]

    def como_dict(self) -> dict:
        return {
            "pagina": self.pagina,
            "contexto": self.contexto,
            "colunas": [
                {
                    "coluna": c.indice,
                    "registro_ans": formatar_registro(c.registro) if c.registro else None,
                    "cabecalho": c.cabecalho,
                    "precos": {
                        FAIXAS[f]: {"valor": self.valor(c.indice, f), "caixa": self.celulas[(c.indice, f)].caixa()}
                        for f in range(10)
                        if (c.indice, f) in self.celulas
                    },
                }
                for c in self.colunas
            ],
        }


@dataclass
class _Segmento:
    faixa: int
    rotulo_x: float
    y: float
    topo: float
    base: float
    valores: list[Palavra]


def _texto_moeda(texto: str) -> str:
    # "R$ 178,43", "R$178,43" e, no OCR, "R$:490,57" ou "R$.259,04"
    return re.sub(r"^R\$\W*", "", texto.strip())


def _eh_moeda(p: Palavra) -> bool:
    return bool(RE_MOEDA.match(_texto_moeda(p.texto)))


_DIGITOS_SOLTOS = re.compile(r"^\d{1,3}(?:\.\d{3})*\.?$")


def _moedas(pagina: Pagina) -> list[Palavra]:
    """Os valores em reais da página, com o dígito que o PDF desenhou à parte colado de volta.

    Na NotreDame, "118,07" vem como "1" e "18,07" encostados (folga de -0,1 pt). Lido separado, o preço
    perde a centena, e o cálculo pelo padrão de faixas não salva: o erro se repete igual em várias colunas.
    """
    moedas = []
    for linha in pagina.linhas():
        for anterior, p in zip([None] + linha, linha):
            if not _eh_moeda(p):
                continue
            if (anterior is not None and _DIGITOS_SOLTOS.match(anterior.texto) and -1.0 <= p.x0 - anterior.x1 <= 1.0
                    and RE_MOEDA.match(anterior.texto + _texto_moeda(p.texto))):
                p = Palavra(anterior.texto + _texto_moeda(p.texto), anterior.x0, p.x1, min(anterior.topo, p.topo),
                            max(anterior.base, p.base), p.pagina, p.horizontal)
            moedas.append(p)
    return moedas


def _rotulos_na_linha(linha: list[Palavra]) -> list[tuple[int, int, int]]:
    """Rótulos de faixa na linha: (primeira palavra, palavra seguinte ao rótulo, índice da faixa)."""
    rotulos = []
    i = 0
    while i < len(linha):
        if _eh_moeda(linha[i]):
            i += 1
            continue
        achou = None
        # Rótulos têm de 1 a 4 palavras ("59+", "00 – 18", "59 ou +", "59 anos ou +"). Do mais curto para o
        # mais longo, senão "00 – 18 19" engole o começo do rótulo seguinte num cabeçalho transposto.
        for n in (1, 2, 3, 4):
            trecho = linha[i:i + n]
            if len(trecho) < n or any(_eh_moeda(p) for p in trecho):
                continue
            faixa = faixa_do_rotulo(" ".join(p.texto for p in trecho))
            if faixa is not None:
                achou = (i, i + n, faixa)
                break
        if achou:
            rotulos.append(achou)
            i = achou[1]
        else:
            i += 1
    return rotulos


def _segmentos(pagina: Pagina) -> list[_Segmento]:
    """Uma linha de preços por rótulo de faixa: os valores à direita dele, na altura dele.

    Ancorar no rótulo (e não no agrupamento em linhas) aguenta desalinhamentos de poucos pontos,
    comuns em OCR, e tabelas lado a lado: a linha termina no rótulo seguinte à direita.
    """
    ancoras = []  # (faixa, x0, x1, yc, altura)
    for linha in pagina.linhas():
        rotulos = _rotulos_na_linha(linha)
        if len({f for _, _, f in rotulos}) >= 8 and not any(_eh_moeda(p) for p in linha):
            continue  # cabeçalho de tabela transposta
        for i, j, faixa in rotulos:
            palavras = linha[i:j]
            ancoras.append((faixa, palavras[0].x0, palavras[-1].x1, sum(p.yc for p in palavras) / len(palavras),
                            max(p.base - p.topo for p in palavras)))
    moedas = _moedas(pagina)
    segmentos = []
    for faixa, x0, x1, yc, altura in ancoras:
        tolerancia = max(2.5, 0.6 * altura)
        vizinhos = [a[1] for a in ancoras if a[1] > x1 and abs(a[3] - yc) <= tolerancia]
        limite = min(vizinhos, default=float("inf"))
        valores = sorted((p for p in moedas if x1 < p.xc < limite and abs(p.yc - yc) <= tolerancia), key=lambda p: p.x0)
        if valores:
            segmentos.append(_Segmento(faixa, x0, yc, yc - altura / 2, yc + altura / 2, valores))
    return segmentos


def _agrupar(segmentos: list[_Segmento]) -> list[list[_Segmento]]:
    """Tabela = segmentos alinhados na mesma coluna de rótulos, com faixas crescentes e passo regular."""
    grupos: list[list[_Segmento]] = []
    for s in sorted(segmentos, key=lambda s: (s.y, s.rotulo_x)):
        destino = None
        for g in grupos:
            ult = g[-1]
            if abs(ult.rotulo_x - s.rotulo_x) > 25 or s.faixa <= ult.faixa:
                continue
            passos = [b.y - a.y for a, b in zip(g, g[1:])]
            passo_tipico = median(passos) if passos else 30
            if s.y - ult.y <= 3.5 * max(passo_tipico, 6) * (s.faixa - ult.faixa):
                destino = g
                break
        if destino is not None:
            destino.append(s)
        else:
            grupos.append([s])
    return [g for g in grupos if len(g) >= 3]


RE_REGISTRO_SOLTO = re.compile(r"^\d{9}$")


def _tabelas_transpostas(pagina: Pagina) -> list[TabelaGeometrica]:
    """Faixas no cabeçalho e um produto por linha (ex.: Amil): cada linha vira uma 'coluna' da tabela."""
    linhas = pagina.linhas()
    tabelas = []
    for k, linha in enumerate(linhas):
        rotulos = _rotulos_na_linha(linha)
        if len({f for _, _, f in rotulos}) < 8 or any(_eh_moeda(p) for p in linha):
            continue
        centros = {f: (linha[i].x0 + linha[j - 1].x1) / 2 for i, j, f in rotulos}
        passo_x = min((b - a for a, b in zip(sorted(centros.values()), sorted(centros.values())[1:])), default=40)
        tabela = TabelaGeometrica(pagina.numero, [], topo=linha[0].topo, base=linha[0].base,
                                  x0=min(p.x0 for p in linha), x1=max(p.x1 for p in linha))
        ultimo_y = linha[0].yc
        for seguinte in linhas[k + 1:]:
            valores = [p for p in seguinte if _eh_moeda(p)]
            if len({f for _, _, f in _rotulos_na_linha(seguinte)}) >= 8:
                break  # próximo cabeçalho
            if len(valores) < 5:
                if seguinte[0].yc - ultimo_y > 80:
                    break
                continue
            coluna = Coluna(len(tabela.colunas), seguinte[0].yc)
            for p in valores:
                faixa = min(centros, key=lambda f: abs(centros[f] - p.xc))
                if abs(centros[faixa] - p.xc) <= passo_x * 0.6:
                    tabela.celulas.setdefault((coluna.indice, faixa), p)
            for p in seguinte:
                m = RE_REGISTRO_ANS.search(p.texto)
                if m or RE_REGISTRO_SOLTO.match(p.texto):
                    coluna.registro = "".join(m.groups()) if m else p.texto
                    coluna.palavra_registro = p
            coluna.cabecalho = " ".join(p.texto for p in seguinte if p.x1 <= valores[0].x0)[-80:]
            tabela.colunas.append(coluna)
            tabela.base = seguinte[-1].base
            ultimo_y = seguinte[0].yc
        if tabela.colunas:
            tabela.contexto = " ".join(p.texto for p in linha)
            tabelas.append(tabela)
    return tabelas


def ler_tabelas(pagina: Pagina) -> list[TabelaGeometrica]:
    tabelas = _tabelas_transpostas(pagina)
    transpostas = list(tabelas)
    for grupo in sorted(_agrupar(_segmentos(pagina)), key=lambda g: (g[0].y, g[0].rotulo_x)):
        contagem = [len(s.valores) for s in grupo]
        n_colunas = max(set(contagem), key=contagem.count)
        completas = [s.valores for s in grupo if len(s.valores) == n_colunas]
        xs = [median(v[i].xc for v in completas) for i in range(n_colunas)]
        colunas = [Coluna(i, x) for i, x in enumerate(xs)]
        passo = min((b - a for a, b in zip(xs, xs[1:])), default=120)
        tabela = TabelaGeometrica(
            pagina.numero, colunas,
            topo=grupo[0].topo, base=grupo[-1].base,
            x0=grupo[0].rotulo_x - 5, x1=xs[-1] + passo / 2,
        )
        for s in grupo:
            for p in s.valores:
                c = min(colunas, key=lambda c: abs(c.x - p.xc))
                tabela.celulas.setdefault((c.indice, s.faixa), p)
        tabelas.append(tabela)

    for tabela in tabelas:
        if tabela in transpostas:
            continue
        # O cabeçalho de uma tabela fica entre ela e a tabela anterior na mesma faixa horizontal.
        acima = [t.base for t in tabelas if t is not tabela and t.base <= tabela.topo and t.x0 < tabela.x1 and tabela.x0 < t.x1]
        limite = max(acima, default=0.0)
        _associar_cabecalho(pagina, tabela, limite)
    return tabelas


def _associar_cabecalho(pagina: Pagina, tabela: TabelaGeometrica, limite_superior: float):
    """Liga cada coluna ao registro ANS mais próximo na horizontal e guarda o texto do cabeçalho."""
    espacamento = min((b.x - a.x for a, b in zip(tabela.colunas, tabela.colunas[1:])), default=200)
    no_cabecalho = [
        p for p in pagina.palavras
        if limite_superior - 2 <= p.yc < tabela.topo and tabela.x0 - 10 <= p.xc <= tabela.x1 + 10
    ]
    for p in sorted(no_cabecalho, key=lambda p: tabela.topo - p.yc):  # do mais perto para o mais longe
        m = RE_REGISTRO_ANS.search(p.texto)
        coluna = min(tabela.colunas, key=lambda c: abs(c.x - p.xc))
        if abs(coluna.x - p.xc) > espacamento * 0.6:
            continue
        if m and not coluna.registro:
            coluna.registro = "".join(m.groups())
            coluna.palavra_registro = p
    for coluna in tabela.colunas:
        perto = [p for p in no_cabecalho if abs(p.xc - coluna.x) <= espacamento * 0.5 and not RE_REGISTRO_ANS.search(p.texto)]
        coluna.cabecalho = " ".join(p.texto for p in sorted(perto, key=lambda p: (round(p.yc), p.x0)))[-80:]
    linhas = _linhas(no_cabecalho)
    cabecalho = " ".join(linhas)
    tabela.contexto = cabecalho[-600:]
    tabela.titulo = _titulo(linhas)
    tabela.condicao = combinar(_rotulo_lateral(pagina, tabela), marcas(cabecalho))


def _rotulo_lateral(pagina: Pagina, tabela: TabelaGeometrica) -> list[str]:
    """Condição escrita na vertical ao lado da grade, como "Com coparticipação" girado à esquerda.

    O texto girado sai na ordem em que as letras foram desenhadas, às vezes de baixo para cima; das duas
    leituras possíveis vale a que forma uma condição do vocabulário fechado, e a outra não forma nenhuma.
    """
    ao_lado = [p for p in pagina.palavras
               if not p.horizontal and tabela.topo - 20 <= p.yc <= tabela.base + 20
               and (tabela.x0 - 70 <= p.xc < tabela.x0 or tabela.x1 < p.xc <= tabela.x1 + 70)]
    if not ao_lado:
        return []
    de_cima = " ".join(p.texto for p in sorted(ao_lado, key=lambda p: p.yc))
    de_baixo = " ".join(p.texto[::-1] for p in sorted(ao_lado, key=lambda p: -p.yc))
    return marcas(de_cima) or marcas(de_baixo)


_RE_TITULO = re.compile(r"tabela|vidas|copartic|ades[aã]o|\bpme\b|\bmei\b|empresarial|vig[eê]ncia|regi[aã]o|capital|interior|\bporte\b|\bgrupo\b|compuls|familiar|titular|dependente", re.I)


def _linhas(palavras: list[Palavra]) -> list[str]:
    """O texto em linhas de leitura (pela altura média, como as linhas da tabela), de cima para baixo."""
    return [" ".join(p.texto for p in linha) for linha in Pagina(0, 0.0, 0.0, palavras).linhas()]


def _titulo(linhas: list[str]) -> str:
    """As linhas do cabeçalho que dizem a condição da tabela (vidas, coparticipação, vigência...)."""
    textos = []
    for texto in linhas:
        if _RE_TITULO.search(texto) and not RE_REGISTRO_ANS.search(texto) and texto not in textos and len(texto) > 6:
            textos.append(texto)
    return " · ".join(textos[:2])[:160]


def ler_documento(paginas: list[Pagina]) -> list[TabelaGeometrica]:
    return [t for pagina in paginas for t in ler_tabelas(pagina)]
