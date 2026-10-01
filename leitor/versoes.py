"""Comparação entre duas versões do mesmo material (o que mudou desde a última tabela).

A chave é o registro ANS mais a condição de venda da grade, não a posição da coluna: operadoras
reordenam colunas e páginas entre versões, e um diff por posição acusaria "mudança" em tudo ou,
pior, compararia a tabela de 1 vida de uma versão com a de 30 a 99 vidas da outra.
"""
from collections import defaultdict
from dataclasses import dataclass, field
from statistics import median

from .condicoes import parear
from .conferencia import ColunaConferida, Conferencia
from .faixas import FAIXAS, formatar_registro


@dataclass
class Mudanca:
    registro: str
    condicao: str
    tabela: str
    faixas: dict[str, tuple[float, float]]  # faixa -> (antes, depois)

    @property
    def variacao_mediana(self) -> float | None:
        vs = [depois / antes - 1 for antes, depois in self.faixas.values() if antes]
        return median(vs) if vs else None


@dataclass
class Comparacao:
    anterior: str
    nova: str
    iguais: list[tuple[str, str]] = field(default_factory=list)
    mudancas: list[Mudanca] = field(default_factory=list)
    novos: list[tuple[str, str, str]] = field(default_factory=list)
    removidos: list[tuple[str, str, str]] = field(default_factory=list)
    colunas_reordenadas: bool = False
    sem_registro: int = 0

    def resumo(self) -> str:
        partes = [f"{len(self.iguais)} colunas iguais", f"{len(self.mudancas)} com preço alterado"]
        variacoes = [m.variacao_mediana for m in self.mudancas if m.variacao_mediana is not None]
        if variacoes:
            partes[-1] += f" (variação mediana {median(variacoes):+.2%})"
        if self.novos:
            partes.append(f"{len(self.novos)} novas")
        if self.removidos:
            partes.append(f"{len(self.removidos)} removidas")
        if self.colunas_reordenadas:
            partes.append("colunas trocaram de lugar (ignorado: a comparação é pelo registro ANS e pela condição)")
        if self.sem_registro:
            partes.append(f"{self.sem_registro} colunas sem registro ANS não comparadas")
        return "; ".join(partes)

    def como_dict(self) -> dict:
        return {
            "anterior": self.anterior,
            "nova": self.nova,
            "resumo": self.resumo(),
            "mudancas": [
                {"registro_ans": formatar_registro(m.registro), "condicao": m.condicao, "tabela": m.tabela,
                 "variacao_mediana": m.variacao_mediana,
                 "faixas": {f: {"antes": a, "depois": d} for f, (a, d) in m.faixas.items()}}
                for m in self.mudancas
            ],
            "novos": [{"registro_ans": formatar_registro(r), "tabela": t} for r, _, t in self.novos],
            "removidos": [{"registro_ans": formatar_registro(r), "tabela": t} for r, _, t in self.removidos],
        }


def _por_registro(conf: Conferencia) -> tuple[dict[str, list[ColunaConferida]], list[str], int]:
    """As colunas de cada registro em ordem de leitura; a coluna lida só pelo LLM vem por último."""
    def posicao(c: ColunaConferida):
        caixa = next((x.caixa for x in c.celulas if x.caixa), None)
        return (caixa is None, c.pagina, caixa[1] if caixa else 0, caixa[0] if caixa else 0)

    grupos: dict[str, list[ColunaConferida]] = defaultdict(list)
    ordem, sem = [], 0
    for col in sorted(conf.colunas, key=posicao):
        if not col.registro:
            sem += 1
            continue
        grupos[col.registro].append(col)
        ordem.append(col.registro)
    return grupos, ordem, sem


def _condicao(col: ColunaConferida) -> list[str]:
    return col.condicao


def _serie(col: ColunaConferida) -> dict[str, float]:
    return {c.faixa: c.valor for c in col.celulas if c.valor is not None}


def comparar(anterior: Conferencia, nova: Conferencia) -> Comparacao:
    antes, ordem_antes, sem_a = _por_registro(anterior)
    depois, ordem_depois, sem_d = _por_registro(nova)
    comp = Comparacao(anterior.arquivo, nova.arquivo, sem_registro=max(sem_a, sem_d))
    for registro in antes.keys() | depois.keys():
        for a, d in parear(antes.get(registro, []), depois.get(registro, []), _condicao):
            condicao = " · ".join(_condicao(d or a))
            if d is None:
                comp.removidos.append((registro, condicao, a.tabela))
                continue
            if a is None:
                comp.novos.append((registro, condicao, d.tabela))
                continue
            sa, sd = _serie(a), _serie(d)
            diferencas = {f: (sa[f], sd[f]) for f in FAIXAS if f in sa and f in sd and abs(sa[f] - sd[f]) >= 0.005}
            if diferencas:
                comp.mudancas.append(Mudanca(registro, condicao, d.tabela, diferencas))
            else:
                comp.iguais.append((registro, condicao))
    comuns = [r for r in dict.fromkeys(ordem_antes) if r in set(ordem_depois)]
    comp.colunas_reordenadas = comuns != [r for r in dict.fromkeys(ordem_depois) if r in set(ordem_antes)]
    comp.mudancas.sort(key=lambda m: (m.registro, m.condicao))
    return comp
