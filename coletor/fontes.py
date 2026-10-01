"""Fontes como configuração: cada arquivo JSON em fontes/ diz quem publica e por onde o material chega.

Fonte nova de um tipo de captura que já existe é um arquivo novo, revisado como código (diff, histórico),
sem nenhuma linha de Python. `python -m coletor.fontes` valida tudo sem tocar no banco.
"""
import json
import sys
from pathlib import Path

from . import TIPOS

PASTA = Path(__file__).resolve().parent.parent / "fontes"
TIPOS_DE_FONTE = {"dados_ans", "site_operadora", "pdf_operadora", "pdf_administradora", "envio_corretor", "parceria"}


def ler_fontes(pasta: Path = PASTA) -> dict[str, dict]:
    """As fontes de todos os arquivos, por nome.

    A mesma fonte citada em mais de um arquivo (uma administradora que publica tabelas de várias operadoras)
    junta as capturas; nos demais campos vale o arquivo da própria fonte, na raiz, antes dos de subpastas.
    """
    pasta = Path(pasta)
    fontes: dict[str, dict] = {}
    for arquivo in sorted(pasta.rglob("*.json"), key=lambda a: (len(a.relative_to(pasta).parts), str(a))):
        for f in json.loads(arquivo.read_text(encoding="utf-8")).get("fontes", []):
            atual = fontes.setdefault(f["nome"], {"capturas": [], "arquivos": []})
            for chave, valor in f.items():
                if chave != "capturas" and valor not in (None, "") and chave not in atual:
                    atual[chave] = valor
            atual["arquivos"].append(str(arquivo.relative_to(pasta)))
            vistas = {(c["tipo"], c.get("nome", "")) for c in atual["capturas"]}
            atual["capturas"] += [c for c in f.get("capturas", []) if (c.get("tipo"), c.get("nome", "")) not in vistas]
    return fontes


def ler_operadoras(pasta: Path = PASTA) -> dict[str, dict]:
    """O que o mapeamento de cada operadora concluiu (canal do preço, relatório), pelo registro ANS."""
    operadoras = {}
    for arquivo in sorted(Path(pasta).rglob("*.json")):
        if operadora := json.loads(arquivo.read_text(encoding="utf-8")).get("operadora"):
            operadoras[operadora["registro_ans"]] = operadora
    return operadoras


def validar(fontes: dict[str, dict]) -> list[str]:
    problemas = []
    for nome, f in fontes.items():
        onde = f"{nome} ({', '.join(f['arquivos'])})"
        if f.get("tipo") not in TIPOS_DE_FONTE:
            problemas.append(f"{onde}: tipo de fonte '{f.get('tipo')}' desconhecido (use {', '.join(sorted(TIPOS_DE_FONTE))})")
        if not isinstance(f.get("confiabilidade", 3), int) or not 1 <= f.get("confiabilidade", 3) <= 5:
            problemas.append(f"{onde}: confiabilidade vai de 1 a 5")
        for c in f["capturas"]:
            coletor = TIPOS.get(c.get("tipo"))
            if coletor is None:
                problemas.append(f"{onde}: tipo de captura '{c.get('tipo')}' desconhecido (use {', '.join(TIPOS)})")
                continue
            problemas += [f"{onde} · {c.get('nome') or c['tipo']}: {p}" for p in coletor.validar(c.get("config", {}))]
    return problemas


if __name__ == "__main__":
    pasta = Path(sys.argv[1]) if len(sys.argv) > 1 else PASTA
    fontes = ler_fontes(pasta)
    problemas = validar(fontes)
    print(f"{len(fontes)} fontes e {sum(len(f['capturas']) for f in fontes.values())} capturas em {pasta}")
    for p in problemas:
        print(f"  - {p}")
    sys.exit(1 if problemas else 0)
