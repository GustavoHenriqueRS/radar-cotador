"""Mede o acervo de demonstração: quantos preços cada leitura acha e quantos passam sem revisão humana.

São os números da proposta (seção 3) e de docs/detalhes-tecnicos.md (seção 2.3). Roda sem gastar API: a segunda leitura vem das gravações por hash.
Uso: PYTHONPATH=. .venv/bin/python scripts/medir_acervo.py
"""
import json
import re
import sys
from concurrent.futures import ProcessPoolExecutor
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PDFS = sorted((RAIZ / "amostras" / "publicas").glob("*.pdf")) + sorted((RAIZ / "amostras" / "simuladas").glob("*.pdf"))
CAMPOS = ("celulas", "celulas_com_produto", "revisar_com_produto", "confirmado", "confirmado_calculo", "divergente", "so_geometrico", "so_llm")


def _data(nome: str) -> date | None:
    m = re.search(r"(\d{4})-(\d{2})(?:-(\d{2}))?", nome)
    return date(int(m.group(1)), int(m.group(2)), int(m.group(3) or 1)) if m else None


def medir(pdf: Path) -> dict:
    from leitor.ans import IndiceANS
    from leitor.conferencia import conferir
    from leitor.llm import ler_com_llm, tem_gravacao

    indice = IndiceANS(RAIZ / "dados" / "ans" / "indice.sqlite")
    data = _data(pdf.name)
    uma = conferir(pdf, indice, data_material=data).resumo()
    dupla = conferir(pdf, indice, ler_com_llm(pdf, replay=True).leitura, data_material=data).resumo() if tem_gravacao(pdf) else None
    return {"arquivo": pdf.name, "uma": {c: uma.get(c, 0) for c in CAMPOS}, "dupla": {c: dupla.get(c, 0) for c in CAMPOS} if dupla else None}


def _taxa(soma: dict) -> str:
    total = soma["celulas_com_produto"]
    return f"{(total - soma['revisar_com_produto']) / total:.1%} ({total - soma['revisar_com_produto']} de {total})" if total else "-"


if __name__ == "__main__":
    with ProcessPoolExecutor(max_workers=4) as executor:
        resultados = list(executor.map(medir, PDFS))
    uma = {c: sum(r["uma"][c] for r in resultados) for c in CAMPOS}
    duplas = [r["dupla"] for r in resultados if r["dupla"]]
    dupla = {c: sum(d[c] for d in duplas) for c in CAMPOS}
    print(f"{len(PDFS)} PDFs, {len(duplas)} com leitura por LLM gravada")
    print(f"uma leitura:   {uma['celulas']} preços; sem revisão (produto identificado): {_taxa(uma)}; confirmados pelo cálculo: {uma['confirmado_calculo']}")
    print(f"dupla leitura: {dupla['celulas']} preços; sem revisão: {_taxa(dupla)}; confirmados pelas duas: {dupla['confirmado']}; "
          f"pelo cálculo: {dupla['confirmado_calculo']}; divergentes: {dupla['divergente']}; só geométrica: {dupla['so_geometrico']}; só LLM: {dupla['so_llm']}")
    if "--json" in sys.argv:
        print(json.dumps(resultados, ensure_ascii=False, indent=1))
