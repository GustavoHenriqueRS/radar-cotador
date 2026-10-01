"""Casos que o mapeamento das operadoras do Cotador trouxe, cada um com o PDF real em que apareceu."""
from datetime import date
from pathlib import Path

import pytest

from leitor import regras
from leitor.ans import IndiceANS
from leitor.conferencia import conferir
from leitor.faixas import faixa_do_rotulo
from leitor.geometrico import ler_documento
from leitor.pdf import Pagina, Palavra, ler_paginas
from leitor.vigencia import vigencia_impressa

RAIZ = Path(__file__).resolve().parent.parent
OPERADORAS = RAIZ / "amostras" / "operadoras"
INDICE = RAIZ / "dados" / "ans" / "indice.sqlite"


@pytest.fixture(scope="module")
def indice():
    if not INDICE.exists():
        pytest.skip("índice da ANS não construído")
    return IndiceANS(INDICE)


@pytest.mark.parametrize("rotulo", ["&gt; 59 anos", "> 59 anos", "≥ 59", "+59", "+ de 59 anos", "a partir de 59 anos"])
def test_rotulos_da_ultima_faixa(rotulo):
    assert faixa_do_rotulo(rotulo) == 9


@pytest.mark.parametrize("rotulo", ["> 5 vidas", "590", "5 a 10 vidas"])
def test_o_que_nao_e_faixa(rotulo):
    assert faixa_do_rotulo(rotulo) is None


def _pagina(*linhas: str) -> Pagina:
    palavras = [Palavra(texto, 10.0 + 40 * j, 45.0 + 40 * j, 20.0 * i, 20.0 * i + 10, 0, True)
                for i, linha in enumerate(linhas) for j, texto in enumerate(linha.split())]
    return Pagina(1, 600.0, 800.0, palavras)


def test_vigencia_impressa_so_colada_a_palavra_de_vigencia():
    assert vigencia_impressa([_pagina("Tabela atual vigente: 08/2022")]) == (date(2022, 8, 1), None)
    assert vigencia_impressa([_pagina("VÁLIDO DE 17/08/2026 A 30/09/2026")]) == (date(2026, 8, 17), date(2026, 9, 30))
    assert vigencia_impressa([_pagina("Última atualização: 01/09/2026", "Nascido em 10/05/1990")]) == (None, None)


def test_condicao_escrita_na_vertical_ao_lado_da_grade():
    # Smile DF: "Com coparticipação" e "Sem coparticipação" girados à esquerda das duas grades da página 4.
    pdf = OPERADORAS / "smile_saude" / "allcare_smile_adesao_df_2023-06.pdf"
    if not pdf.exists():
        pytest.skip("amostra da Smile ausente")
    grades = [t for t in ler_documento(ler_paginas(pdf)) if t.pagina == 4]
    assert [t.condicao for t in sorted(grades, key=lambda t: t.topo)] == [["coparticipação: com"], ["coparticipação: sem"]]


def test_material_sem_grade_avisa(indice):
    pdf = OPERADORAS / "quallity_pro_saude" / "quallity_coparticipacao_2026-09-01.pdf"
    if not pdf.exists():
        pytest.skip("amostra da Quallity ausente")
    conf = conferir(pdf, indice)
    assert not conf.colunas and any("nenhuma tabela de preço" in a.mensagem for a in conf.achados_documento)


def test_nota_tecnica_da_epoca_do_material():
    # Preço de 2023 comparado com a nota de 2026 parecia "abaixo da despesa"; com a nota posterior, é só informação.
    assert regras.nota_mais_nova("2026-08-25", date(2026, 6, 1))[0].severidade == regras.INFO
    assert regras.nota_mais_nova("2026-06-20", date(2026, 6, 1)) == []
    assert regras.nota_mais_nova(None, date(2026, 6, 1)) == []


def _grades(pdf: Path) -> list:
    if not pdf.exists():
        pytest.skip(f"amostra ausente: {pdf.name}")
    return ler_documento(ler_paginas(pdf))


def test_tabela_tapada_por_outra_camada_fica_de_fora():
    # CNU DF: a tabela de outro ano fica sob o fundo das células, e o texto das duas se misturava letra a letra.
    grades = [t for t in _grades(OPERADORAS / "central_nacional_unimed" / "allcare_cnu_pme_df_2022-05.pdf") if t.pagina == 6]
    valores = {round(t.valor(c.indice, 6), 2) for t in grades for c in t.colunas if t.valor(c.indice, 6)}
    assert {589.11, 676.52, 866.80, 1167.61} <= valores  # "De 44 a 48 anos", como aparece na página


def test_digito_desenhado_a_parte_volta_para_o_numero():
    # NotreDame: "118,07" vem como "1" e "18,07" encostados.
    grades = _grades(OPERADORAS / "notredame_intermedica" / "gndi_super_simples_pme_sp_2025-07.pdf")
    primeiras = [t.valor(c.indice, 0) for t in grades for c in t.colunas if t.valor(c.indice, 0)]
    assert 118.07 in primeiras and min(primeiras) > 60  # sem a centena, sobravam valores como 18,07


def test_negrito_falso_nao_esconde_a_grade():
    # CORPe, Hapvida BH: a segunda grade da página 2 desenha cada letra duas vezes ("0000--1188" em vez de "00-18").
    grades = [t for t in _grades(OPERADORAS / "hapvida" / "corpe_hapvida_adesao_bh_2026-09-15.pdf") if t.pagina == 2]
    assert sorted(c.registro for t in grades for c in t.colunas) == ["490173218", "490173218", "490180211", "493094221"]
