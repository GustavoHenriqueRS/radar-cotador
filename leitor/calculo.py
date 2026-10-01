"""Recalcular cada preço pelo percentual de faixa das colunas que seguem o mesmo padrão.

A ANS exige que o contrato fixe o percentual de aumento em cada mudança de faixa etária (RN 563), e as
operadoras aplicam os mesmos percentuais a uma linha inteira de produtos (no acervo, todas as colunas de
88 das 115 tabelas com 3+ colunas). Então, deixando de lado uma faixa, as colunas que batem com esta em
todas as outras dizem quanto essa faixa deveria valer, ao centavo.

É uma terceira conferência, independente das duas leituras e da ANS: só aritmética sobre a própria tabela.
"""
from statistics import median

# Margem sobre o limite teórico de arredondamento no centavo.
FOLGA = 1.2
# As duas estimativas (pela faixa de baixo e pela de cima) precisam concordar entre si.
CONCORDANCIA = 0.03


def _bate(a: list[float | None], b: list[float | None], t: int) -> bool | None:
    """A razão entre as faixas t-1 e t é a mesma nas duas colunas, a menos do arredondamento no centavo?"""
    a0, a1, b0, b1 = a[t - 1], a[t], b[t - 1], b[t]
    if None in (a0, a1, b0, b1) or 0 in (a0, b0):
        return None
    limite = FOLGA * (0.005 / a0 + 0.005 / a1 + 0.005 / b0 + 0.005 / b1)
    return abs((a1 / a0) / (b1 / b0) - 1) <= limite


def calcular(series: list[list[float | None]]) -> dict[tuple[int, int], tuple[float, int]]:
    """Para cada preço verificável, o valor calculado e quantas colunas sustentam o cálculo.

    `series` são as colunas do documento inteiro (10 faixas cada): o mesmo padrão costuma se repetir em
    tabelas diferentes (1 vida, 2 a 29 vidas...). Uma coluna p serve de referência para a faixa f da
    coluna c quando as duas batem em todas as transições que não tocam f.
    """
    n = len(series)
    diferencas: dict[tuple[int, int], set[int]] = {}
    for c in range(n):
        for p in range(n):
            if p == c:
                continue
            resultado = [_bate(series[c], series[p], t) for t in range(1, 10)]
            if sum(r is not None for r in resultado) >= 6:
                diferencas[(c, p)] = {t for t, r in zip(range(1, 10), resultado) if r is False}

    calculados = {}
    for c in range(n):
        s = series[c]
        for f in range(10):
            toca = {t for t in (f, f + 1) if 1 <= t <= 9}
            pares = [p for p in range(n) if (c, p) in diferencas and diferencas[(c, p)] <= toca]
            if len(pares) < 2:
                continue
            estimativas = []
            if f > 0 and s[f - 1] is not None:
                razoes = [series[p][f] / series[p][f - 1] for p in pares if None not in (series[p][f], series[p][f - 1])]
                if razoes:
                    estimativas.append(s[f - 1] * median(razoes))
            if f < 9 and s[f + 1] is not None:
                razoes = [series[p][f + 1] / series[p][f] for p in pares if None not in (series[p][f + 1], series[p][f])]
                if razoes:
                    estimativas.append(s[f + 1] / median(razoes))
            if estimativas and max(estimativas) - min(estimativas) <= CONCORDANCIA:
                calculados[(c, f)] = (round(median(estimativas), 2), len(pares))
    return calculados


def bate(valor: float | None, calculado: float) -> bool:
    return valor is not None and abs(valor - calculado) < 0.015
