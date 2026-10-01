from pathlib import Path

import pytest

from leitor import ocr
from leitor.ans import IndiceANS
from leitor.calculo import calcular
from leitor.conferencia import CONFIRMADO_CALCULO, DIVERGENTE, conferir
from leitor.geometrico import ler_documento
from leitor.llm import ler_com_llm
from leitor.pdf import ler_paginas

RAIZ = Path(__file__).resolve().parent.parent
GUARULHOS = RAIZ / "amostras" / "publicas" / "unimed_guarulhos_pme_2026.pdf"
ESCANEADA = RAIZ / "amostras" / "simuladas" / "unimed_guarulhos_pme_2026_ESCANEADA.pdf"
INDICE = RAIZ / "dados" / "ans" / "indice.sqlite"


def _exigir(*caminhos):
    for caminho in caminhos:
        if not caminho.exists():
            pytest.skip(f"ausente: {caminho.name}")


@pytest.fixture(scope="module")
def indice():
    _exigir(INDICE)
    return IndiceANS(INDICE)


@pytest.fixture(scope="module")
def paginas_do_ocr():
    _exigir(ESCANEADA)
    return ocr.paginas_por_ocr(ESCANEADA)


def test_erro_de_digito_plantado_e_recalculado():
    _exigir(GUARULHOS)
    series = [t.serie(c.indice) for t in ler_documento(ler_paginas(GUARULHOS)) for c in t.colunas]
    original = series[5][6]
    series[5][6] = round(original + 90, 2)  # um dígito trocado: 1.159,85 → 1.249,85
    calculado, pares = calcular(series)[(5, 6)]
    assert calculado == original and pares >= 2


def test_calculo_corrige_os_digitos_que_o_llm_errou_no_escaneado():
    _exigir(ESCANEADA)
    leitura = ler_com_llm(ESCANEADA, modelo="gpt-6-luna", replay=True).leitura
    colunas = [(t.pagina, linha) for t in leitura.tabelas for linha in t.linhas]
    calculados = calcular([(linha.valores + [None] * 10)[:10] for _, linha in colunas])
    errados = {(p, linha.valores[f], calculados[(i, f)][0])
               for i, (p, linha) in enumerate(colunas) for f in range(10)
               if (i, f) in calculados and abs(calculados[(i, f)][0] - linha.valores[f]) > 0.015}
    # O LLM leu 474,74, 892,48 e 767,67 onde o PDF original diz 474,77, 892,23 e 767,05.
    assert errados == {(1, 474.74, 474.77), (1, 892.48, 892.23), (2, 767.67, 767.05)}


def test_duas_leituras_e_calculo_fecham_o_escaneado(indice, paginas_do_ocr, monkeypatch):
    monkeypatch.setattr(ocr, "paginas_por_ocr", lambda caminho: paginas_do_ocr)
    leitura = ler_com_llm(ESCANEADA, modelo="gpt-6-luna", replay=True).leitura
    conf = conferir(ESCANEADA, indice, leitura)
    r = conf.resumo()
    assert r["divergente"] == 0 and r["so_llm"] == 0 and r["confirmado_calculo"] == 11
    assert r["revisar"] == 1  # só o preço abaixo da despesa assistencial da ANS, que é achado real
    resolvidas = [c for col in conf.colunas for c in col.celulas if c.status == CONFIRMADO_CALCULO and c.geometrico and c.llm]
    assert sorted(c.valor for c in resolvidas) == [474.77, 767.05, 892.23]
    assert not any(c.status == DIVERGENTE for col in conf.colunas for c in col.celulas)


def test_faixa_nao_lida_vem_com_o_valor_calculado(indice, paginas_do_ocr, monkeypatch):
    monkeypatch.setattr(ocr, "paginas_por_ocr", lambda caminho: paginas_do_ocr)
    conf = conferir(ESCANEADA, indice)
    mensagens = [a.mensagem for col in conf.colunas for a in col.achados if a.mensagem.startswith("faixas não lidas")]
    assert "faixas não lidas: 24-28 (pelo padrão da tabela: 24-28 R$ 645.28)" in mensagens
