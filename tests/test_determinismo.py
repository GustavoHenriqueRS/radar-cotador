"""O mesmo material dá sempre o mesmo resultado: é o que permite auditar uma publicação meses depois.

A leitura geométrica, o cálculo e as regras são determinísticos. A leitura por LLM não é, por isso cada
leitura fica gravada pelo hash do PDF e a conferência refeita com a gravação dá o mesmo resultado.
"""
import json
from pathlib import Path

import pytest

from leitor.ans import IndiceANS
from leitor.conferencia import conferir
from leitor.llm import ler_com_llm, tem_gravacao

RAIZ = Path(__file__).resolve().parent.parent
INDICE = RAIZ / "dados" / "ans" / "indice.sqlite"
PDFS = [RAIZ / "amostras" / "publicas" / "unimed_guarulhos_pme_2026.pdf",
        RAIZ / "amostras" / "publicas" / "qualicorp_sulamerica_adesao_sp_2026-06.pdf"]


@pytest.fixture(scope="module")
def indice():
    if not INDICE.exists():
        pytest.skip("índice da ANS não construído")
    return IndiceANS(INDICE)


def _resultado(pdf: Path, indice, leitura=None) -> str:
    conf = conferir(pdf, indice, leitura)
    return json.dumps({"resumo": conf.resumo(), "colunas": [c.como_dict() for c in conf.colunas],
                       "documento": [a.como_dict() for a in conf.achados_documento]}, sort_keys=True, default=str)


@pytest.mark.parametrize("pdf", PDFS, ids=lambda p: p.stem)
def test_mesma_leitura_duas_vezes(pdf, indice):
    assert _resultado(pdf, indice) == _resultado(pdf, indice)


@pytest.mark.parametrize("pdf", PDFS, ids=lambda p: p.stem)
def test_dupla_leitura_refeita_pela_gravacao(pdf, indice):
    if not tem_gravacao(pdf):
        pytest.skip("sem leitura por LLM gravada para este PDF")
    leitura = ler_com_llm(pdf, replay=True).leitura
    assert _resultado(pdf, indice, leitura) == _resultado(pdf, indice, ler_com_llm(pdf, replay=True).leitura)
