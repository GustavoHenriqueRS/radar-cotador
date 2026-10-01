from datetime import date

import pytest

from leitor import regras
from leitor.ans import NotaTecnica

# Unimed Guarulhos, Essencial I Enfermaria (503.058/25-7), tabela 1 vida, vigência jun–dez/2026.
ESSENCIAL_I = [178.43, 228.39, 242.55, 249.56, 272.57, 310.70, 436.04, 582.46, 653.46, 1065.14]


def test_tabela_real_no_limite_passa_com_tolerancia_de_arredondamento():
    assert regras.faixas_rn563(ESSENCIAL_I) == []


def test_erro_de_digitacao_na_ultima_faixa_viola_o_teto_de_6_vezes():
    digitado = ESSENCIAL_I[:9] + [1605.14]  # 1.065,14 digitado como 1.605,14
    regras_violadas = {a.regra for a in regras.faixas_rn563(digitado)}
    assert "RN 563 art. 3º I" in regras_violadas


def test_faixas_trocadas_geram_variacao_negativa():
    trocado = ESSENCIAL_I.copy()
    trocado[3], trocado[4] = trocado[4], trocado[3]
    assert any(a.regra == "RN 563 art. 3º III" for a in regras.faixas_rn563(trocado))


def test_preco_com_odonto_embutido_nao_vira_erro():
    # Hapvida adesão DF (Allcare), com odonto: a proporção 7ª→10ª passa da 1ª→7ª por causa do valor fixo somado.
    com_odonto = [124.09, 163.05, 185.71, 207.03, 217.82, 244.40, 298.61, 413.71, 557.29, 723.44]
    assert any(a.severidade == regras.ERRO for a in regras.faixas_rn563(com_odonto))
    assert all(a.severidade == regras.INFO for a in regras.faixas_rn563(com_odonto, preco_composto=True))


def test_plano_senior_sem_faixas_iniciais_nao_e_avaliado_pelas_regras_i_e_ii():
    senior = [None] * 6 + [723.14, 723.14, 867.77, 1136.78]
    assert [a.severidade for a in regras.faixas_rn563(senior)] == [regras.INFO]


# Nota técnica 409951 (23/12/2025) do Essencial III Enfermaria, 478.590/17-8, nos dados abertos da ANS.
NOTA_ESSENCIAL_III = NotaTecnica(
    "409951", "2025-12-23", "UNICA",
    [136.32, 174.5, 185.31, 190.67, 208.24, 237.38, 333.14, 444.99, 499.25, 813.77],
    [122.77, 122.15, 136.13, 147.22, 164.59, 186.05, 233.2, 311.49, 349.48, 569.64],
    [177.22, 226.85, 240.9, 247.87, 270.71, 308.59, 433.08, 578.49, 649.02, 1057.9],
)
# Tabela de 30 a 99 vidas da Unimed Guarulhos para esse produto: ~14,5% abaixo do VCM em todas as faixas.
ESSENCIAL_III_30_99 = [116.56, 149.20, 158.45, 163.03, 178.06, 202.97, 284.85, 380.50, 426.88, 695.81]


def test_preco_abaixo_da_despesa_assistencial_na_faixa_0_18():
    achados = regras.referencia_ntrp(ESSENCIAL_III_30_99, [NOTA_ESSENCIAL_III], hoje=date(2026, 9, 30))
    assert [(a.regra, a.faixas) for a in achados] == [("RN 564 art. 5º", ["00-18"])]


def test_reajuste_uniforme_nao_alarma_mas_digito_trocado_sim():
    reajustada = [round(v * 1.45, 2) for v in ESSENCIAL_III_30_99]  # tabela 45% acima: fora da banda em várias faixas
    achados = regras.referencia_ntrp(reajustada, [NOTA_ESSENCIAL_III], hoje=date(2027, 6, 1))  # nota com mais de 1 ano
    assert all(a.severidade == regras.INFO for a in achados)
    reajustada[5] = 249.32  # 294,31 digitado como 249,32
    achados = regras.referencia_ntrp(reajustada, [NOTA_ESSENCIAL_III], hoje=date(2027, 6, 1))
    assert [a.faixas for a in achados if a.severidade == regras.ALERTA] == [["39-43"]]


def test_carencia_acima_do_maximo_legal():
    assert regras.carencia("Parto a termo", 300) == []
    assert regras.carencia("Demais casos", 240)[0].severidade == regras.ERRO


@pytest.mark.parametrize("cobertura, dias", [
    # Textos reais lidos pelo LLM no acervo: 'cirurgia' contém 'urg' e não é urgência; CPT vai até 24 meses.
    ("Cirurgias ambulatoriais; Tomografia Computadorizada, Ressonância", 180),
    ("Odonto: Radiologia, Prevenção em Saúde Bucal, Dentística, Cirurgia, Periodontia", 60),
    ("Doenças ou lesões preexistentes — CPT", 730),
    ("Grupo 13 — Cobertura Parcial Temporária – CPT — Sem Plano Anterior", 730),
    ("Atendimentos de urgência/emergência.", 1),
])
def test_carencia_dentro_da_lei_nao_acusa(cobertura, dias):
    assert regras.carencia(cobertura, dias) == []


@pytest.mark.parametrize("cobertura, dias", [
    ("Atendimentos de urgência/emergência.", 30),
    ("Cirurgias eletivas ambulatoriais", 240),
    ("Cobertura parcial temporária para doenças e lesões preexistentes", 900),
])
def test_carencia_acima_da_lei_acusa(cobertura, dias):
    assert regras.carencia(cobertura, dias)[0].severidade == regras.ERRO
