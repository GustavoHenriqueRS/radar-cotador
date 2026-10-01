from dataclasses import replace
from pathlib import Path

import pytest

import leitor.conferencia as conferencia
from leitor.pdf import Pagina, ler_paginas

from leitor.ans import IndiceANS
from leitor.conferencia import conferir
from leitor.faixas import formatar_registro
from leitor.versoes import comparar

RAIZ = Path(__file__).resolve().parent.parent
AMOSTRAS = RAIZ / "amostras" / "publicas"
INDICE = RAIZ / "dados" / "ans" / "indice.sqlite"


@pytest.fixture(scope="module")
def indice():
    if not INDICE.exists():
        pytest.skip("índice da ANS não construído (python -m leitor.cli constrói na primeira execução)")
    return IndiceANS(INDICE)


def _comparar(indice, a, b):
    for nome in (a, b):
        if not (AMOSTRAS / nome).exists():
            pytest.skip(f"amostra ausente: {nome}")
    return comparar(conferir(AMOSTRAS / a, indice), conferir(AMOSTRAS / b, indice))


def test_colunas_trocadas_de_lugar_nao_sao_mudanca_de_preco(indice):
    c = _comparar(indice, "wayback_allcare_unimed_rio_preto_adesao_sp_2026-04-27.pdf",
                  "wayback_allcare_unimed_rio_preto_adesao_sp_2026-05-11.pdf")
    assert c.colunas_reordenadas and not c.mudancas and len(c.iguais) == 14


def test_produtos_retirados_da_tabela(indice):
    c = _comparar(indice, "wayback_allcare_unimed_rio_preto_adesao_sp_2026-05-11.pdf",
                  "allcare_unimed_rio_preto_adesao_sp_2026-08-14.pdf")
    assert sorted(formatar_registro(r) for r, _, _ in c.removidos) == ["478.730/17-7", "478.731/17-5"]


def test_reajuste_entre_versoes(indice):
    c = _comparar(indice, "wayback_allcare_unimed_bh_adesao_mg_2024-09-03.pdf", "allcare_unimed_bh_adesao_mg_2026-09-08.pdf")
    assert len(c.mudancas) == 9
    assert all(abs(m.variacao_mediana - 0.1846) < 0.001 for m in c.mudancas)


def test_administradora_com_tabela_antiga_do_mesmo_produto(indice):
    c = _comparar(indice, "allcare_hapvida_adesao_df_2026-07-16.pdf", "affix_hapvida_adesao_df_2025-08.pdf")
    assert len(c.mudancas) == 6 and all(m.variacao_mediana < -0.09 for m in c.mudancas)


def test_paginas_reordenadas_nao_viram_reajuste(indice, monkeypatch):
    """A versão nova traz as mesmas tabelas em outra ordem: a comparação é pela condição (vidas), não pela posição."""
    pdf = AMOSTRAS / "unimed_guarulhos_pme_2026.pdf"
    if not pdf.exists():
        pytest.skip("amostra ausente")
    original = conferir(pdf, indice)
    paginas = ler_paginas(pdf)
    ordem = [paginas[2], paginas[0], paginas[1]]
    reordenadas = [Pagina(i + 1, p.largura, p.altura, [replace(w, pagina=i + 1) for w in p.palavras]) for i, p in enumerate(ordem)]
    monkeypatch.setattr(conferencia, "ler_paginas", lambda caminho: reordenadas)
    c = comparar(original, conferir(pdf, indice))
    assert not c.mudancas and not c.novos and not c.removidos and len(c.iguais) == 36


def test_composicao_familiar_casa_com_a_mesma_composicao(indice):
    """Qualicorp 2024 → 2026: "Titular + 2 ou mais" só se compara com "Titular + 2 ou mais", mesmo em outra ordem."""
    c = _comparar(indice, "qualicorp_sulamerica_adesao_sp_2024-11.pdf", "qualicorp_sulamerica_adesao_sp_2026-06.pdf")
    capital_t2 = [m for m in c.mudancas if m.registro == "495735231" and "titular + 2" in m.condicao and "capital" in m.condicao]
    assert len(capital_t2) == 1 and abs(capital_t2[0].variacao_mediana - (498.22 / 558.66 - 1)) < 0.001
