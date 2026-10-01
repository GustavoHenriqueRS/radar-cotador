import pytest

from leitor.condicoes import combinar, compativeis, marcas, parear


@pytest.mark.parametrize("titulo, esperado", [
    # Títulos reais do acervo.
    ("TABELA DE VENDAS 01 VIDA · VIGÊNCIA 01 DE JUNHO/26 A 31 DE DEZEMBRO/26", ["vidas: 1"]),
    ("Tabela de vendas 02 - 29 vidas — coparticipação parcial", ["coparticipação: parcial", "vidas: 2 a 29"]),
    ("Tabela de preços — Com coparticipação Total", ["coparticipação: total"]),
    ("Planos Direto - Capital com coparticipação — Titular ou Titular + 1 dependente",
     ["composição: titular", "composição: titular + 1", "coparticipação: com", "região: capital"]),
    ("DEMAIS PLANOS - INTERIOR 2 COM COPARTICIPAÇÃO — TITULAR + 2 ou MAIS DEPENDENTES",
     ["composição: titular + 2", "coparticipação: com", "região: interior 2"]),
    ("Plano de referência — PME Porte II Compulsório (Demais Empresas)", ["adesão: compulsória", "porte: II"]),
    ("Grupo 3 - Tabela Estudantil — Linha SBS Premium", ["grupo: 3", "tabela: estudantil"]),
    ("COPARTICIPAÇÃO PARCIAL COPARTICIPAÇÃO TOTAL", []),
])
def test_marcas_de_condicao(titulo, esperado):
    assert marcas(titulo) == esperado


def test_rotulo_da_coluna_vence_o_cabecalho_compartilhado():
    cabecalho = marcas("PME I - 03 a 29 vidas · Compulsório Livre adesão")
    assert combinar(marcas("Compulsório"), cabecalho) == ["adesão: compulsória", "vidas: 3 a 29"]


def test_compatibilidade_e_pareamento():
    assert not compativeis(["composição: titular"], ["composição: titular + 2"])
    assert compativeis(["composição: titular + 1"], ["composição: titular", "composição: titular + 1"])
    assert compativeis(["vidas: 1"], ["coparticipação: parcial", "vidas: 1"])
    antigos = [["vidas: 1"], ["vidas: 2 a 29"], ["vidas: 30 a 99"]]
    novos = [["vidas: 30 a 99"], ["vidas: 1"], ["vidas: 2 a 29"]]
    pares = parear(antigos, novos, lambda m: m)
    assert all(a == b for a, b in pares)
