"""Mede a conferência por cálculo no acervo: quantas tabelas seguem um padrão único de faixas, quantos preços
o cálculo consegue refazer e quanto ele pega de erro de digitação plantado de propósito.

São os números de docs/detalhes-tecnicos.md (seção 3.4). Só leitura geométrica, sem API, e o sorteio dos erros
tem semente fixa: o resultado é sempre o mesmo.
Uso: PYTHONPATH=. .venv/bin/python scripts/medir_calculo.py
"""
import random
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from statistics import median

from leitor.calculo import bate, calcular

RAIZ = Path(__file__).resolve().parent.parent
PDFS = sorted((RAIZ / "amostras" / "publicas").glob("*.pdf"))
TENTATIVAS = 1500
GRUPOS = ("centavos (< 0,1%)", "0,1% a 1%", "> 1%")


def series_do_pdf(pdf: Path) -> tuple[str, list[list[list[float | None]]]]:
    from leitor.geometrico import ler_documento
    from leitor.pdf import ler_paginas

    return pdf.name, [[t.serie(c.indice) for c in t.colunas] for t in ler_documento(ler_paginas(pdf))]


def mesmo_padrao(tabela: list[list[float | None]]) -> bool | None:
    """Todas as colunas completas da tabela sobem pelo mesmo percentual em cada faixa (±0,05%)?"""
    completas = [s for s in tabela if all(v is not None for v in s)]
    if len(completas) < 3:
        return None
    razoes = [[s[f] / s[f - 1] for f in range(1, 10)] for s in completas]
    medianas = [median(r[f] for r in razoes) for f in range(9)]
    return max(abs(r[f] / medianas[f] - 1) for r in razoes for f in range(9)) < 0.0005


def erro_de_digito(valor: float, rng: random.Random) -> float:
    """Um dígito trocado por outro ou dois dígitos vizinhos invertidos, como na digitação."""
    texto = f"{valor:.2f}".replace(".", "")
    i = rng.randrange(len(texto))
    if rng.random() < 0.5:
        novo = texto[:i] + str((int(texto[i]) + rng.randint(1, 9)) % 10) + texto[i + 1:]
    else:
        i = min(i, len(texto) - 2)
        novo = texto[:i] + texto[i + 1] + texto[i] + texto[i + 2:]
    return int(novo) / 100


def conferir_plantado(caso) -> tuple[str, bool, bool]:
    series, c, f, errado = caso
    original = series[c][f]
    relativo = abs(errado / original - 1)
    grupo = GRUPOS[0] if relativo < 0.001 else GRUPOS[1] if relativo < 0.01 else GRUPOS[2]
    copia = [list(s) for s in series]
    copia[c][f] = errado
    calculado = calcular(copia).get((c, f))
    pego = bool(calculado) and not bate(errado, calculado[0])
    return grupo, pego, pego and abs(calculado[0] - original) < 0.005


if __name__ == "__main__":
    with ProcessPoolExecutor(max_workers=4) as executor:
        docs = list(executor.map(series_do_pdf, PDFS))

    padroes = [p for _, tabelas in docs for t in tabelas if (p := mesmo_padrao(t)) is not None]
    print(f"{len(PDFS)} PDFs; tabelas com 3 ou mais colunas completas: {len(padroes)}, "
          f"todas as colunas com o mesmo percentual de faixa: {sum(padroes)}")

    colunas = {nome: [s for t in tabelas for s in t if sum(v is not None for v in s) >= 7] for nome, tabelas in docs}
    calculados = {nome: [(c, f) for c, f in sorted(calcular(series)) if series[c][f] is not None] for nome, series in colunas.items()}
    total = sum(v is not None for series in colunas.values() for s in series for v in s)
    refeitos = sum(len(c) for c in calculados.values())
    print(f"preços que o cálculo refaz: {refeitos} de {total} ({refeitos / total:.0%})")

    rng = random.Random(5)
    candidatos = [(nome, celula) for nome in sorted(calculados) for celula in calculados[nome]]
    plantados = []
    for _ in range(TENTATIVAS):
        nome, (c, f) = rng.choice(candidatos)
        errado = erro_de_digito(colunas[nome][c][f], rng)
        if abs(errado / colunas[nome][c][f] - 1) >= 1e-9:
            plantados.append((colunas[nome], c, f, errado))
    with ProcessPoolExecutor(max_workers=4) as executor:
        resultados = list(executor.map(conferir_plantado, plantados, chunksize=20))
    contagem = {g: [0, 0, 0] for g in GRUPOS}
    for grupo, pego, exato in resultados:
        contagem[grupo][0] += 1
        contagem[grupo][1] += pego
        contagem[grupo][2] += exato
    print("erro de digitação plantado num preço que o cálculo refaz:")
    for grupo, (n, pegos, exatos) in contagem.items():
        print(f"   {grupo:18} {n:4} testes; apontado em {pegos / n:.0%}; valor original refeito ao centavo em {exatos / n:.0%}")
