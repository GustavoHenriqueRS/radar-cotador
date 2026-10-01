"""Condição de venda de uma grade: o que separa as várias tabelas de um mesmo registro ANS.

O mesmo plano aparece em várias grades de um material: 1 vida, 2 a 29 e 30 a 99 vidas; capital e
interior; titular e titular com dependentes; coparticipação parcial e total. Para comparar versões e
fontes, cada grade é casada pela condição escrita no título e no rótulo, e não pela posição no PDF,
que muda quando a operadora reorganiza o material.
"""
import re
import unicodedata

_VIDAS = re.compile(r"(\d{1,3})\s*(?:a|-|ate)\s*(\d{1,3})\s*vidas")
_VIDAS_A_PARTIR = re.compile(r"(?:a partir de|acima de|mais de)\s*(\d{1,3})\s*vidas")
_UMA_VIDA = re.compile(r"\b0*1\s*vida\b")
_TITULAR_MAIS = re.compile(r"\btitular\s*\+\s*(\d)")
_INTERIOR = re.compile(r"\binterior\s*(\d)")
_PORTE = re.compile(r"\bporte\s*(iii|ii|i|\d)\b")
_GRUPO = re.compile(r"\bgrupo\s*(\d+)")
_TABELA = re.compile(r"\btabela\s+(aberta|fechada|estudantil)")
_COPART = re.compile(r"copart\w*\s+(parcial|total)(?:\s*(?:ou|e|/|,)?\s*(parcial|total))?")


def _simples(texto: str) -> str:
    decomposto = unicodedata.normalize("NFKD", texto.lower().replace("–", "-").replace("—", "-"))
    return "".join(c for c in decomposto if not unicodedata.combining(c))


def marcas(*textos: str) -> list[str]:
    """As marcas de condição ('dimensão: valor') escritas nos textos da grade, em ordem estável."""
    t = " ".join(_simples(x) for x in textos if x)
    m = set()
    m.update(f"vidas: {int(a)} a {int(b)}" for a, b in _VIDAS.findall(t))
    m.update(f"vidas: {int(a)} ou mais" for a in _VIDAS_A_PARTIR.findall(t))
    if _UMA_VIDA.search(t):
        m.add("vidas: 1")
    # "com coparticipação total ou parcial" lista as opções do produto, não diz a condição da grade.
    copart = {v for m in _COPART.finditer(t) for v in m.groups() if v}
    if len(copart) == 1:
        m.add(f"coparticipação: {copart.pop()}")
    elif not copart and re.search(r"\bsem\s+copart", t):
        m.add("coparticipação: sem")
    elif not copart and re.search(r"\bcom\s+copart", t):
        m.add("coparticipação: com")
    if "compuls" in t:
        m.add("adesão: compulsória")
    if "livre ades" in t:
        m.add("adesão: livre")
    if re.search(r"\btitular\b(?!\s*\+)", t):
        m.add("composição: titular")
    m.update(f"composição: titular + {n}" for n in _TITULAR_MAIS.findall(t))
    if re.search(r"\bcapital\b", t):
        m.add("região: capital")
    m.update(f"região: interior {n}" for n in _INTERIOR.findall(t))
    m.update(f"porte: {n.upper()}" for n in _PORTE.findall(t))
    m.update(f"grupo: {n}" for n in _GRUPO.findall(t))
    m.update(f"tabela: {n}" for n in _TABELA.findall(t))
    return sorted(m)


def _por_dimensao(marcas_: list[str]) -> dict[str, set[str]]:
    dimensoes: dict[str, set[str]] = {}
    for marca in marcas_:
        dimensao, _, valor = marca.partition(": ")
        dimensoes.setdefault(dimensao, set()).add(valor)
    return dimensoes


def combinar(*fontes: list[str]) -> list[str]:
    """Junta marcas de várias fontes; em cada dimensão vale a fonte mais específica (a primeira que diz algo).

    A ordem esperada é: rótulo da coluna, título da grade, cabeçalho da grade, topo da página. Assim uma
    coluna "Compulsório" não herda o "livre adesão" da coluna vizinha que está no mesmo cabeçalho.
    """
    escolhidas: dict[str, set[str]] = {}
    for fonte in fontes:
        for dimensao, valores in _por_dimensao(fonte).items():
            escolhidas.setdefault(dimensao, valores)
    return sorted(f"{d}: {v}" for d, valores in escolhidas.items() for v in valores)


# "Com coparticipação" vale para a parcial e para a total: não contradiz nenhuma das duas.
_ABRANGE = {("coparticipação", "com"): {"com", "parcial", "total"}}


def _valores(dimensao: str, valores: set[str]) -> set[str]:
    return set().union(*(_ABRANGE.get((dimensao, v), {v}) for v in valores))


def compativeis(a: list[str], b: list[str]) -> bool:
    """Nenhuma dimensão em conflito: onde as duas grades dizem algo, dizem algo em comum."""
    da, db = _por_dimensao(a), _por_dimensao(b)
    return all(_valores(d, da[d]) & _valores(d, db[d]) for d in da.keys() & db.keys())


def parear(antigos: list, novos: list, marcas_de) -> list[tuple]:
    """Casa as grades de um mesmo registro entre duas versões ou duas fontes.

    Só casa condições compatíveis; entre as compatíveis, as de mais marcas em comum primeiro e,
    no empate, as que aparecem na mesma ordem. O que sobra vira (antigo, None) ou (None, novo).
    """
    candidatos = []
    for i, a in enumerate(antigos):
        for j, b in enumerate(novos):
            ma, mb = marcas_de(a), marcas_de(b)
            if compativeis(ma, mb):
                candidatos.append((-len(set(ma) & set(mb)), abs(i - j), i, j))
    usados_a, usados_b, pares = set(), set(), []
    for _, _, i, j in sorted(candidatos):
        if i not in usados_a and j not in usados_b:
            usados_a.add(i)
            usados_b.add(j)
            pares.append((antigos[i], novos[j]))
    pares += [(a, None) for i, a in enumerate(antigos) if i not in usados_a]
    pares += [(None, b) for j, b in enumerate(novos) if j not in usados_b]
    return pares
