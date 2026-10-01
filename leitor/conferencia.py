"""Dupla leitura: cruza a leitura geométrica com a do LLM, célula a célula, e aplica as regras da ANS.

As colunas das duas leituras são pareadas pelos próprios valores (quantas faixas batem), não por
rótulo: isso funciona mesmo quando o LLM nomeia a coluna de outro jeito ou erra um dígito.
Uma célula só dispensa revisão humana quando duas fontes independentes concordam (as duas leituras,
ou uma leitura e o valor recalculado pelo padrão de faixas da tabela) e nenhuma regra acusa.
"""
import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from . import regras
from .calculo import bate, calcular
from .ans import IndiceANS, PlanoANS
from .condicoes import combinar, marcas
from .esquema import LeituraDocumento, LinhaDePreco, TabelaDePreco
from .faixas import FAIXAS, formatar_registro, normalizar_registro
from .geometrico import TabelaGeometrica, ler_documento
from .pdf import ler_paginas, tem_camada_de_texto
from .vigencia import vigencia_impressa

CONFIRMADO, DIVERGENTE, SO_GEOMETRICO, SO_LLM = "confirmado", "divergente", "so_geometrico", "so_llm"
# Uma leitura e o cálculo pelo padrão de faixas concordam; a outra leitura divergiu ou não leu.
CONFIRMADO_CALCULO = "confirmado_calculo"
# O valor recalculado erra até 2 centavos quando a operadora arredonda em cadeia (medido no acervo).
RUIDO_DO_CALCULO = 0.025
DESVIO_MATERIAL = 0.10
RE_PRECO_COMPOSTO = re.compile(r"com\s+odonto|\+\s*odonto|odonto\s+inclu", re.IGNORECASE)


@dataclass
class Celula:
    faixa: str
    geometrico: float | None
    llm: float | None
    status: str
    caixa: list[float] | None = None
    revisar: bool = False
    calculado: float | None = None
    escolhido: float | None = None

    @property
    def valor(self) -> float | None:
        if self.escolhido is not None:
            return self.escolhido
        return self.geometrico if self.geometrico is not None else self.llm


@dataclass
class ColunaConferida:
    pagina: int
    tabela: str
    coluna: str
    registro: str | None
    registro_geometrico: str | None
    registro_llm: str | None
    plano: PlanoANS | None
    celulas: list[Celula]
    achados: list[regras.Achado] = field(default_factory=list)
    condicao: list[str] = field(default_factory=list)

    def como_dict(self) -> dict:
        return {
            "pagina": self.pagina,
            "tabela": self.tabela,
            "coluna": self.coluna,
            "registro_ans": formatar_registro(self.registro) if self.registro else None,
            "plano_ans": None if not self.plano else {
                "nome": self.plano.nome, "operadora": self.plano.operadora, "situacao": self.plano.situacao,
                "contratacao": self.plano.contratacao, "acomodacao": self.plano.acomodacao,
                "fator_moderador": self.plano.fator_moderador, "abrangencia": self.plano.abrangencia,
                "livre_escolha": self.plano.livre_escolha, "segmentacao": self.plano.segmentacao,
            },
            "celulas": [c.__dict__ for c in self.celulas],
            "achados": [a.como_dict() for a in self.achados],
            "condicao": self.condicao,
        }


@dataclass
class Conferencia:
    arquivo: str
    tem_texto: bool
    colunas: list[ColunaConferida]
    leitura_llm: LeituraDocumento | None
    achados_documento: list[regras.Achado]
    ocr: bool = False
    vigencia_impressa: tuple = (None, None)

    def resumo(self) -> dict:
        celulas = [c for col in self.colunas for c in col.celulas]
        por_status = {s: sum(c.status == s for c in celulas) for s in (CONFIRMADO, CONFIRMADO_CALCULO, DIVERGENTE, SO_GEOMETRICO, SO_LLM)}
        achados = [a for col in self.colunas for a in col.achados] + self.achados_documento
        com_produto = [c for col in self.colunas if col.registro for c in col.celulas]
        return {
            "celulas": len(celulas),
            **por_status,
            "revisar": sum(c.revisar for c in celulas),
            # Medido na leitura, antes de qualquer aprovação: é o número que mostra quanto a automação resolve.
            "celulas_com_produto": len(com_produto),
            "revisar_com_produto": sum(c.revisar for c in com_produto),
            "erros": sum(a.severidade == regras.ERRO for a in achados),
            "alertas": sum(a.severidade == regras.ALERTA for a in achados),
            "colunas": len(self.colunas),
            "colunas_com_registro_ans": sum(1 for c in self.colunas if c.registro),
        }


def _concordancia(geo: list[float | None], llm: list[float | None]) -> int:
    return sum(1 for a, b in zip(geo, llm) if a is not None and b is not None and abs(a - b) < 0.005)


def _parear(geo_tabs: list[TabelaGeometrica], leitura: LeituraDocumento):
    """Pareia (tabela geométrica, coluna) com (tabela do LLM, linha) pela quantidade de valores iguais."""
    geo = [(t, c.indice) for t in geo_tabs for c in t.colunas]
    llm = [(t, linha) for t in leitura.tabelas for linha in t.linhas]
    candidatos = []
    for gi, (gt, gc) in enumerate(geo):
        serie = gt.serie(gc)
        for li, (lt, linha) in enumerate(llm):
            distancia_pagina = abs(gt.pagina - lt.pagina)
            if distancia_pagina > 1:
                continue
            valores = (linha.valores + [None] * 10)[:10]
            iguais = _concordancia(serie, valores)
            minimo = 3 if distancia_pagina == 0 else 8
            if iguais >= minimo:
                candidatos.append((iguais, -distancia_pagina, gi, li))
    usados_g, usados_l, pares = set(), set(), []
    for _, _, gi, li in sorted(candidatos, reverse=True):
        if gi in usados_g or li in usados_l:
            continue
        usados_g.add(gi)
        usados_l.add(li)
        pares.append((geo[gi], llm[li]))
    sobras_g = [g for i, g in enumerate(geo) if i not in usados_g]
    # Coluna que o LLM repetiu (mesma página, mesmo rótulo, mesmos valores) é cópia, não preço novo para revisar.
    vistas = {_assinatura(lt, linha) for _, (lt, linha) in pares}
    sobras_l, repetidas = [], 0
    for i, (lt, linha) in enumerate(llm):
        if i in usados_l:
            continue
        if _assinatura(lt, linha) in vistas:
            repetidas += 1
            continue
        vistas.add(_assinatura(lt, linha))
        sobras_l.append((lt, linha))
    return pares, sobras_g, sobras_l, repetidas


def _assinatura(tabela: TabelaDePreco, linha: LinhaDePreco) -> tuple:
    return tabela.pagina, " ".join(linha.coluna.casefold().split()), tuple((linha.valores + [None] * 10)[:10])


def _celulas(geo_tab: TabelaGeometrica | None, geo_col: int | None, linha: LinhaDePreco | None) -> list[Celula]:
    llm_valores = (linha.valores + [None] * 10)[:10] if linha else [None] * 10
    celulas = []
    for f in range(10):
        g = geo_tab.valor(geo_col, f) if geo_tab is not None else None
        caixa = geo_tab.celulas[(geo_col, f)].caixa() if geo_tab is not None and (geo_col, f) in geo_tab.celulas else None
        l = llm_valores[f]
        if g is None and l is None:
            continue
        if g is not None and l is not None:
            status = CONFIRMADO if abs(g - l) < 0.005 else DIVERGENTE
        else:
            status = SO_GEOMETRICO if g is not None else SO_LLM
        celulas.append(Celula(FAIXAS[f], g, l, status, caixa))
    return celulas


def conferir(caminho_pdf: Path, indice: IndiceANS, leitura: LeituraDocumento | None = None,
             data_material: date | None = None) -> Conferencia:
    """`data_material`: a data da versão do material, para comparar o preço com a nota técnica que valia então."""
    paginas = ler_paginas(caminho_pdf)
    tem_texto = tem_camada_de_texto(paginas)
    if not tem_texto:
        from .ocr import paginas_por_ocr  # carrega o modelo de OCR só quando precisa

        paginas = paginas_por_ocr(caminho_pdf)
    vigencia = vigencia_impressa(paginas)
    referencia = data_material or _data_iso(leitura.vigencia_inicio if leitura else None) or vigencia[0]
    geo_tabs = ler_documento(paginas)
    produtos = {p.id: p for p in leitura.produtos} if leitura else {}
    colunas: list[ColunaConferida] = []
    # O que está no topo da página (ex.: "Capital com coparticipação") vale para as grades de baixo que não dizem o contrário.
    marcas_da_pagina: dict[int, list[str]] = {}
    for gt in sorted(geo_tabs, key=lambda t: (t.pagina, t.topo)):
        marcas_da_pagina.setdefault(gt.pagina, gt.condicao)

    def nova_coluna(gt: TabelaGeometrica | None, gc: int | None, lt: TabelaDePreco | None, linha: LinhaDePreco | None):
        geo_coluna = gt.colunas[gc] if gt is not None else None
        produto = produtos.get(linha.produto_id) if linha else None
        reg_geo = geo_coluna.registro if geo_coluna else None
        reg_llm = normalizar_registro(produto.registro_ans) if produto and produto.registro_ans else None
        coluna = ColunaConferida(
            pagina=gt.pagina if gt is not None else lt.pagina,
            tabela=lt.titulo if lt else ((gt.titulo or gt.contexto[:120]) if gt is not None else ""),
            coluna=(linha.coluna if linha else geo_coluna.cabecalho) or f"coluna {gc}",
            registro=reg_geo or reg_llm,
            registro_geometrico=reg_geo,
            registro_llm=reg_llm,
            plano=None,
            celulas=_celulas(gt, gc, linha),
        )
        coluna.condicao = combinar(
            marcas(linha.coluna if linha else "", geo_coluna.cabecalho if geo_coluna else ""),
            marcas(lt.titulo) if lt else [],
            gt.condicao if gt is not None else [],
            marcas_da_pagina.get(coluna.pagina, []),
        )
        if reg_geo and reg_llm and reg_geo != reg_llm:
            coluna.achados.append(regras.Achado(
                "Dupla leitura", regras.ERRO,
                f"registro diverge entre leituras: geométrica {formatar_registro(reg_geo)} × LLM {formatar_registro(reg_llm)}",
            ))
        coluna.plano, achados = regras.situacao_plano(indice, coluna.registro)
        coluna.achados += achados
        serie = [None] * 10
        for c in coluna.celulas:
            serie[FAIXAS.index(c.faixa)] = c.valor
        lidas = [i for i, v in enumerate(serie) if v is not None]
        # Faltar só o começo é normal (plano sênior); faltar faixa no meio ou no fim é falha de leitura.
        faltando = [FAIXAS[i] for i in range(lidas[0], 10) if serie[i] is None] if lidas else []
        if faltando:
            # Sem lista de faixas de propósito: a faixa que falta não tem célula para marcar, então a coluna inteira vai para revisão.
            coluna.achados.append(regras.Achado("Leitura", regras.ALERTA, f"faixas não lidas: {', '.join(faltando)}"))
        # O LLM marca preço composto; sem ele, o cabeçalho impresso ('+ ODONTO', 'Com Odonto') também denuncia.
        cabecalho = f"{gt.contexto if gt is not None else ''} {geo_coluna.cabecalho if geo_coluna else ''}"
        composto = bool(lt and lt.preco_inclui) or bool(RE_PRECO_COMPOSTO.search(cabecalho))
        coluna.achados += regras.faixas_rn563(serie, preco_composto=composto)
        if coluna.plano:
            coluna.achados += regras.referencia_na_epoca(serie, indice.notas_por_data(coluna.plano.id_plano), referencia,
                                                         preco_composto=composto)
            coluna.achados += regras.nota_mais_nova(indice.ultima_nota(coluna.plano.id_plano), referencia)
            coluna.achados += regras.atributos(
                coluna.plano,
                acomodacao=produto.acomodacao if produto else None,
                coparticipacao=lt.coparticipacao if lt else None,
                contratacao=leitura.tipo_contratacao if leitura else None,
            )
        _marcar_revisao(coluna, dupla=leitura is not None)
        colunas.append(coluna)

    achados_doc = []
    if leitura is None:
        for gt in geo_tabs:
            for c in gt.colunas:
                nova_coluna(gt, c.indice, None, None)
    else:
        pares, sobras_g, sobras_l, repetidas = _parear(geo_tabs, leitura)
        for (gt, gc), (lt, linha) in pares:
            nova_coluna(gt, gc, lt, linha)
        for gt, gc in sobras_g:
            nova_coluna(gt, gc, None, None)
        for lt, linha in sobras_l:
            if any(v is not None for v in linha.valores):
                nova_coluna(None, None, lt, linha)
        if repetidas:
            achados_doc.append(regras.Achado(
                "Dupla leitura", regras.INFO,
                f"a leitura por LLM repetiu {repetidas} coluna(s) com o mesmo rótulo e os mesmos valores na mesma página; "
                "as cópias foram descartadas",
            ))

    _conferir_pelo_calculo(colunas, dupla=leitura is not None, ocr=not tem_texto)
    if not colunas:
        achados_doc.append(regras.Achado(
            "Leitura", regras.ALERTA,
            "nenhuma tabela de preço por faixa etária encontrada: material sem preço (manual, guia, regras) "
            "ou um layout que o leitor ainda não reconhece",
        ))
    if leitura:
        for carencia in leitura.carencias:
            achados_doc += regras.carencia(carencia.cobertura, carencia.prazo_dias)
    colunas.sort(key=lambda c: (c.pagina, c.tabela, c.coluna))
    return Conferencia(caminho_pdf.name, tem_texto, colunas, leitura, achados_doc, ocr=not tem_texto, vigencia_impressa=vigencia)


def _data_iso(texto: str | None) -> date | None:
    try:
        return date.fromisoformat(texto) if texto else None
    except ValueError:
        return None


def _conferir_pelo_calculo(colunas: list[ColunaConferida], dupla: bool, ocr: bool):
    """Terceira conferência: o preço recalculado pelo padrão de faixas das colunas iguais no resto.

    Desempata a divergência e confirma o preço que só uma leitura pegou. Quando o cálculo discorda de um
    preço que as duas leituras confirmaram num PDF com texto, quem foge do padrão é a própria tabela da
    operadora: fica registrado como informação, sem revisão.
    """
    series = []
    for col in colunas:
        serie = [None] * 10
        for c in col.celulas:
            serie[FAIXAS.index(c.faixa)] = c.valor
        series.append(serie)
    calculados = calcular(series)
    for i, col in enumerate(colunas):
        por_faixa = {FAIXAS.index(c.faixa): c for c in col.celulas}
        sugestoes, mudou = [], False
        for f in range(10):
            if (i, f) not in calculados:
                continue
            valor_calculado, n = calculados[(i, f)]
            c = por_faixa.get(f)
            if c is None:
                sugestoes.append(f"{FAIXAS[f]} R$ {valor_calculado:.2f}")
                continue
            c.calculado = valor_calculado
            if c.status in (DIVERGENTE, SO_GEOMETRICO, SO_LLM):
                certo = next((v for v in (c.geometrico, c.llm) if bate(v, valor_calculado)), None)
                if certo is not None:
                    c.status, c.escolhido, mudou = CONFIRMADO_CALCULO, certo, True
                    continue
            desvio = abs(c.valor - valor_calculado)
            if c.status == CONFIRMADO or not (dupla or ocr):
                # Lido certo (duas leituras, ou texto do PDF): centavos de diferença são arredondamento da planilha
                # da operadora; acima disso, a própria tabela foge do padrão e vale perguntar.
                if desvio > DESVIO_MATERIAL:
                    col.achados.append(regras.Achado("Cálculo", regras.INFO, (
                        f"{c.faixa}: a própria tabela foge do padrão de faixas: R$ {c.valor:.2f} impresso, "
                        f"R$ {valor_calculado:.2f} pelo percentual das outras colunas"), [c.faixa]))
            elif desvio > RUIDO_DO_CALCULO:
                col.achados.append(regras.Achado("Cálculo", regras.ALERTA, (
                    f"{c.faixa}: pelo percentual de faixa de {n} colunas iguais no resto, seria R$ {valor_calculado:.2f} "
                    f"(lido R$ {c.valor:.2f})"), [c.faixa]))
                mudou = True
        for a in col.achados:
            if sugestoes and a.mensagem.startswith("faixas não lidas"):
                a.mensagem += f" (pelo padrão da tabela: {', '.join(sugestoes)})"
        if mudou:
            _marcar_revisao(col, dupla)


def _marcar_revisao(coluna: ColunaConferida, dupla: bool):
    """Revisa-se a célula divergente, a lida por um leitor só (na dupla leitura) e a apontada por regra."""
    graves = [a for a in coluna.achados if a.severidade in (regras.ERRO, regras.ALERTA)]
    coluna_toda = any(not a.faixas for a in graves)
    faixas_apontadas = {f for a in graves for f in a.faixas}
    for c in coluna.celulas:
        c.revisar = (
            c.status == DIVERGENTE
            or (dupla and c.status in (SO_GEOMETRICO, SO_LLM))
            or coluna_toda
            or c.faixa in faixas_apontadas
        )
