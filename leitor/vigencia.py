"""Vigência impressa no material, para quando a leitura por LLM não roda.

Só vale data colada a uma palavra de vigência ("vigência", "vigente", "válido de", "a partir de"): a mesma
página traz data de atualização do site, de reajuste e até de nascimento em exemplo, e nenhuma delas é vigência.
"""
import calendar
import re
from datetime import date

from .pdf import Pagina

_DATA = r"(\d{1,2}/\d{1,2}/\d{4}|\d{1,2}/\d{4})"
_VIGENCIA = re.compile(
    r"(?:vig[eê]ncia|vigente|v[aá]lid[ao]s?\s+(?:de|a\s+partir\s+de|para|at[eé])|a\s+partir\s+de)\D{0,25}?"
    + _DATA + r"(?:\s*(?:a|at[eé]|-|–)\s*" + _DATA + r")?",
    re.I,
)


def _data(texto: str, fim: bool = False) -> date | None:
    partes = [int(p) for p in texto.split("/")]
    try:
        if len(partes) == 3:
            return date(partes[2], partes[1], partes[0])
        mes, ano = partes
        return date(ano, mes, calendar.monthrange(ano, mes)[1] if fim else 1)
    except ValueError:
        return None


def vigencia_impressa(paginas: list[Pagina], primeiras: int = 3) -> tuple[date | None, date | None]:
    """(início, fim) da primeira menção de vigência nas primeiras páginas; mês sem dia vale do dia 1 ao último."""
    for pagina in paginas[:primeiras]:
        for linha in pagina.linhas():
            m = _VIGENCIA.search(" ".join(p.texto for p in linha))
            if m and (inicio := _data(m.group(1))):
                return inicio, _data(m.group(2), fim=True) if m.group(2) else None
    return None, None
