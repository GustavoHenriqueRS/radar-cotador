from dataclasses import replace
from pathlib import Path

import pytest

from leitor.faixas import RE_MOEDA, faixa_do_rotulo, formatar_registro
from leitor.geometrico import ler_documento
from leitor.pdf import Pagina, ler_paginas

AMOSTRAS = Path(__file__).resolve().parent.parent / "amostras" / "publicas"


def _tabelas(nome):
    caminho = AMOSTRAS / nome
    if not caminho.exists():
        pytest.skip(f"amostra ausente: {nome}")
    return ler_documento(ler_paginas(caminho))


@pytest.mark.parametrize("rotulo, faixa", [
    ("00 a 18", 0), ("0 a 18 anos", 0), ("0 - 18", 0), ("19 a 23 anos", 1), ("59 ou mais", 9),
    ("59 anos >", 9), ("59+", 9), ("59 ou +", 9), ("59 anos ou +", 9), ("59/ +", 9), ("+ de 59", 9),
    ("até 18", 0), ("00-18", 0), ("00 – 18", 0), ("5 a 10 vidas", None), ("02 - 29 VIDAS", None),
])
def test_rotulos_de_faixa(rotulo, faixa):
    assert faixa_do_rotulo(rotulo) == faixa


def _outro_layout(p: Pagina) -> Pagina:
    """A mesma página com as colunas de produto em ordem inversa, 20% menor e deslocada."""
    alturas = [w.yc for w in p.palavras if w.texto in {"00", "19", "24", "29", "34", "39", "44", "49", "54", "59"}]
    na_linha = [w for w in p.palavras if any(abs(w.yc - y) < 3 for y in alturas)]
    primeiro_preco = min(w.x0 for w in na_linha if RE_MOEDA.match(w.texto))
    inicio = max(w.x1 for w in na_linha if w.x1 < primeiro_preco and not w.texto.startswith("R$")) + 2

    def mover(w):
        x0, x1 = (inicio + p.largura - w.x1, inicio + p.largura - w.x0) if w.x0 >= inicio else (w.x0, w.x1)
        return replace(w, x0=x0 * 0.8 + 60, x1=x1 * 0.8 + 60, topo=w.topo * 0.8 + 90, base=w.base * 0.8 + 90)

    return Pagina(p.numero, p.largura, p.altura, [mover(w) for w in p.palavras])


def test_mudar_o_layout_nao_muda_a_leitura():
    """Nada no leitor depende de onde a tabela está nem da ordem dos produtos: não há template por operadora."""
    caminho = AMOSTRAS / "unimed_guarulhos_pme_2026.pdf"
    if not caminho.exists():
        pytest.skip("amostra ausente")
    paginas = ler_paginas(caminho)

    def por_registro(tabelas):
        return {(t.pagina, t.colunas[c].registro, f): t.valor(c, f) for t in tabelas for (c, f) in t.celulas}

    alteradas = [_outro_layout(p) for p in paginas]
    original, alterado = ler_documento(paginas), ler_documento(alteradas)
    assert [c.registro for c in alterado[0].colunas] == [c.registro for c in original[0].colunas][::-1]
    assert por_registro(alterado) == por_registro(original) and len(por_registro(original)) == 360


def test_unimed_guarulhos_cabecalho_quebrado_em_duas_linhas():
    tabelas = _tabelas("unimed_guarulhos_pme_2026.pdf")
    assert len(tabelas) == 3 and sum(len(t.celulas) for t in tabelas) == 360
    registros = [formatar_registro(c.registro) for c in tabelas[0].colunas]
    # O 6º e o 12º registros ficam numa segunda linha do cabeçalho; têm de cair na coluna certa.
    assert registros[5] == "505.139/25-8" and registros[11] == "503.061/25-7"
    assert tabelas[0].serie(0) == [178.43, 228.39, 242.55, 249.56, 272.57, 310.70, 436.04, 582.46, 653.46, 1065.14]


def test_allcare_duas_tabelas_na_mesma_pagina():
    tabelas = _tabelas("allcare_hapvida_adesao_df_2026-07-16.pdf")
    assert [len(t.celulas) for t in tabelas] == [30, 30]
    assert [formatar_registro(c.registro) for c in tabelas[1].colunas] == ["492.128/22-3", "491.923/22-8", "491.915/22-7"]


def test_notredame_tabelas_lado_a_lado_e_texto_girado():
    tabelas = _tabelas("gndi_pme_web_2023-03.pdf")
    assert all(v is not None for t in tabelas for c in t.colunas for v in t.serie(c.indice))
    assert sum(len(t.celulas) for t in tabelas) == 2440


def test_texto_escondido_no_pdf_nao_vira_coluna():
    # A página 8 carrega uma cópia dos preços da coluna "Basic Referência" na borda direita das grades de cima,
    # tapada no desenho: nenhuma pessoa a vê, e os dois LLMs testados também não a transcreveram.
    pdf = AMOSTRAS / "gndi_pme_web_2023-03.pdf"
    if not pdf.exists():
        pytest.skip("amostra ausente")
    def colunas_na_borda(paginas):
        return [c for t in ler_documento(paginas) if t.pagina == 8 for c in t.colunas if c.x > 1110]
    assert len(colunas_na_borda(ler_paginas(pdf, somente_visiveis=False))) == 2
    assert colunas_na_borda(ler_paginas(pdf)) == []
