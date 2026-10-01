import html
import re

# As 10 faixas etárias da RN 563/2022 (antiga RN 63/2003), na ordem legal.
FAIXAS = ["00-18", "19-23", "24-28", "29-33", "34-38", "39-43", "44-48", "49-53", "54-58", "59+"]
FAIXAS_ANS = [
    "00 a 18 anos", "19 a 23 anos", "24 a 28 anos", "29 a 33 anos", "34 a 38 anos",
    "39 a 43 anos", "44 a 48 anos", "49 a 53 anos", "54 a 58 anos", "59 anos ou mais",
]
_INICIO_FAIXA = {0: 0, 19: 1, 24: 2, 29: 3, 34: 4, 39: 5, 44: 6, 49: 7, 54: 8, 59: 9}

# "0 a 18", "00-18", "até 18", "19 – 23", "59 ou mais", "59 anos ou +", "59/ +", "59 anos >", "59+", "acima de 59", "> 59 anos", "≥ 59"
_RE_FAIXA = re.compile(
    r"^\s*(?:de\s+)?(\d{1,2})\s*(?:a|-|–|até)\s*(\d{2})\b"
    r"|^\s*(59)\s*(?:anos?\s*)?(?:\+|>|/\s*\+|ou\s*(?:mais|\+|acima)|em\s+diante|e\s+acima|acima)"
    r"|^\s*(?:acima\s+(?:de\s+)?|a\s+partir\s+de\s+|\+\s*de\s+|mais\s+de\s+|>=?\s*|≥\s*|\+\s*)(59)\b"
    r"|^\s*(?:até|ate)\s+(18)\b"
    # "59" sozinho, com o "ou +" na linha de baixo (Amil, Linha Especial): a coluna de rótulos já diz que é a última faixa.
    r"|^\s*(59)\s*(?:anos)?\s*$",
    re.IGNORECASE,
)
RE_MOEDA = re.compile(r"^\d{1,3}(?:\.\d{3})*,\d{2}$")
RE_REGISTRO_ANS = re.compile(r"\b(\d{3})\.?(\d{3})/(\d{2})-?(\d)\b")


def faixa_do_rotulo(texto: str) -> int | None:
    # Há PDF gerado de HTML que traz a entidade no texto: "&gt; 59 anos".
    m = _RE_FAIXA.match(html.unescape(texto))
    if not m:
        return None
    if m.group(5) is not None:  # "até 18"
        return 0
    inicio = next(int(g) for g in m.groups() if g is not None)
    if m.group(1) is not None:
        fim = int(m.group(2))
        # "0 a 18" / "19 a 23": o fim precisa ser coerente com o início (evita "5 a 10 vidas").
        esperado = {0: 18, 19: 23, 24: 28, 29: 33, 34: 38, 39: 43, 44: 48, 49: 53, 54: 58}
        if esperado.get(inicio) != fim:
            return None
    return _INICIO_FAIXA.get(inicio)


def moeda(texto: str) -> float:
    return float(texto.replace(".", "").replace(",", "."))


def normalizar_registro(texto: str) -> str | None:
    """'503.058/25-7' ou '503058257' -> '503058257' (CD_PLANO da ANS)."""
    m = RE_REGISTRO_ANS.search(texto)
    if m:
        return "".join(m.groups())
    so_digitos = re.sub(r"\D", "", texto)
    return so_digitos if len(so_digitos) == 9 else None


def formatar_registro(cd_plano: str) -> str:
    return f"{cd_plano[:3]}.{cd_plano[3:6]}/{cd_plano[6:8]}-{cd_plano[8]}" if len(cd_plano) == 9 else cd_plano
