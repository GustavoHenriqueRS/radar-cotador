from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from leitor.ans import IndiceANS
from leitor.conferencia import conferir
from leitor.esquema import LeituraDocumento, LinhaDePreco, Produto, TabelaDePreco
from leitor.geometrico import ler_documento
from leitor.pdf import ler_paginas

RAIZ = Path(__file__).resolve().parent.parent
GUARULHOS = RAIZ / "amostras" / "publicas" / "unimed_guarulhos_pme_2026.pdf"
INDICE = RAIZ / "dados" / "ans" / "indice.sqlite"


@pytest.fixture(scope="module")
def indice():
    if not INDICE.exists():
        pytest.skip("índice da ANS não construído (python -m leitor.cli constrói na primeira execução)")
    return IndiceANS(INDICE)


def test_indice_da_ans_atende_varias_threads(indice):
    # Uploads e coleta processam documentos em paralelo; uma conexão SQLite compartilhada quebrava a segunda thread.
    with ThreadPoolExecutor(4) as executor:
        operadoras = list(executor.map(lambda _: indice.operadora("333051"), range(8)))
    assert all(o and o["registro"] == "333051" for o in operadoras)


def _leitura_espelho(repetir_primeira: bool) -> LeituraDocumento:
    """Uma leitura por LLM que transcreve exatamente o que a geométrica leu, opcionalmente com uma coluna repetida."""
    tabelas = []
    for gt in ler_documento(ler_paginas(GUARULHOS)):
        linhas = [LinhaDePreco(produto_id="P1", coluna=c.cabecalho or f"coluna {c.indice}", valores=gt.serie(c.indice))
                  for c in gt.colunas]
        tabelas.append(TabelaDePreco(pagina=gt.pagina, titulo=gt.titulo or "", vidas_minimo=None, vidas_maximo=None,
                                     coparticipacao="nao_informado", regiao=None, preco_inclui=[], linhas=linhas))
    if repetir_primeira:
        copia = tabelas[0].linhas[0].model_copy(update={"coluna": tabelas[0].linhas[0].coluna.upper()})
        tabelas.append(tabelas[0].model_copy(update={"titulo": "condição inventada", "linhas": [copia]}))
    return LeituraDocumento(
        operadora=None, administradora=None, tipo_contratacao="coletivo_empresarial", ufs=["SP"],
        vigencia_inicio=None, vigencia_fim=None,
        produtos=[Produto(id="P1", nome="x", registro_ans=None, acomodacao="nao_informado", segmentacao=None, abrangencia=None)],
        tabelas=tabelas, coparticipacao=[], carencias=[], elegibilidade=[], avisos=[],
    )


def test_coluna_repetida_pelo_llm_nao_vira_preco_para_revisar(indice):
    if not GUARULHOS.exists():
        pytest.skip("amostra ausente")
    sem_copia = conferir(GUARULHOS, indice, _leitura_espelho(repetir_primeira=False)).resumo()
    conf = conferir(GUARULHOS, indice, _leitura_espelho(repetir_primeira=True))
    r = conf.resumo()
    assert r["so_llm"] == 0 and r["confirmado"] == sem_copia["confirmado"] == r["celulas"]
    assert r["revisar"] == sem_copia["revisar"]
    assert any("repetiu 1 coluna" in a.mensagem for a in conf.achados_documento)
