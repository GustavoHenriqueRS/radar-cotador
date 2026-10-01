import re
from dataclasses import dataclass, field
from datetime import date
from urllib.parse import urlsplit

# Datas que costumam marcar a versão no nome do arquivo: _16_07_2026, -2026-07-16, _20260716.
PADRAO_DATA = r"[_-](?P<dia>\d{2})[_-](?P<mes>\d{2})[_-](?P<ano>20\d{2})(?=\.pdf$)|[_-](?P<ano2>20\d{2})-?(?P<mes2>\d{2})-?(?P<dia2>\d{2})(?=\.pdf$)"

# Cópia no arquivo da web: https://web.archive.org/web/20240812162732id_/https://site/arquivo.pdf
_COPIA_ARQUIVADA = re.compile(r"^https?://web\.archive\.org/web/\d{1,14}[a-z_]*/(?P<original>https?://.+)$", re.I)


class Bloqueado(Exception):
    """A fonte não autoriza a coleta automática (robots.txt): a entrada é por upload ou parceria."""


@dataclass
class Candidato:
    url: str
    titulo: str = ""
    data_versao: date | None = None
    observacoes: list[str] = field(default_factory=list)
    # Cópia de material publicado em outro endereço: o robots.txt do endereço original também tem de permitir.
    url_original: str = ""
    # Material que o tipo de captura já trouxe junto (anexo de e-mail): não há o que baixar.
    conteudo: bytes | None = None
    nome_arquivo: str = ""
    # Sem endereço estável (e-mail), o tipo de captura diz o que identifica a série; senão vale o endereço.
    chave_serie: str = ""


class Coletor:
    """Um tipo de captura: só sabe descobrir o que a fonte oferece.

    robots.txt, intervalo entre pedidos, download condicional, deduplicação, a ligação com a versão
    anterior e os avisos são do motor e valem para todos os tipos.
    """

    tipo: str
    rotulo: str
    # Endereço cujo conteúdo nunca muda (cópia no arquivo da web, anexo de e-mail): baixa uma vez e não pede de novo.
    imutavel = False
    # A descoberta lista tudo o que a fonte oferece (página, arquivo da web). Na incremental (e-mail), lista vazia é o normal.
    lista_completa = True
    obrigatorios: tuple[str, ...] = ()

    def validar(self, config: dict) -> list[str]:
        """Problemas da configuração, apontados antes da primeira coleta e não no meio dela."""
        problemas = [f"falta '{c}'" for c in self.obrigatorios if not config.get(c)]
        for chave in ("incluir", "excluir", "data_no_nome", "assunto"):
            if config.get(chave):
                try:
                    re.compile(config[chave])
                except re.error as e:
                    problemas.append(f"'{chave}' não é uma expressão válida: {e}")
        return problemas

    def descobrir(self, config: dict, http, estado: dict) -> list[Candidato]:
        """Lista os materiais disponíveis agora, sem baixar.

        `estado` atravessa as coletas (ex.: o último e-mail lido); o motor só o grava se a coleta terminar bem.
        """
        raise NotImplementedError


def original(url: str) -> str:
    """O endereço em que a fonte publicou o material, também quando a URL é de uma cópia arquivada."""
    m = _COPIA_ARQUIVADA.match(url)
    return m.group("original") if m else url


def data_no_nome(url: str, padrao: str = PADRAO_DATA) -> date | None:
    m = re.search(padrao, urlsplit(original(url)).path, re.I)
    if not m:
        return None
    g = {k: v for k, v in m.groupdict().items() if v}
    ano, mes = int(g.get("ano") or g.get("ano2") or 0), int(g.get("mes") or g.get("mes2") or 0)
    # Há fonte que marca só mês e ano, às vezes com o ano em dois dígitos ("05-26"): vale o dia 1.
    try:
        return date(ano + 2000 if ano < 100 else ano, mes, int(g.get("dia") or g.get("dia2") or 1)) if ano and mes else None
    except ValueError:
        return None


def chave_da_serie(url: str, padrao: str = PADRAO_DATA) -> str:
    """O endereço sem o que muda de uma versão para outra: é o que liga a tabela nova à anterior.

    A cópia arquivada de um material cai na mesma série do original; www, protocolo e porta não contam.
    """
    partes = urlsplit(original(url))
    caminho = re.sub(padrao, "", partes.path, flags=re.I)
    return f"{(partes.hostname or '').removeprefix('www.')}{caminho.lower()}"
