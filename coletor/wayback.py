"""Histórico no arquivo da web (Wayback Machine): as versões que a fonte publicou e já tirou do ar.

A API CDX lista as cópias guardadas de um endereço (ou de tudo sob um prefixo); com collapse=digest,
só as que mudaram de conteúdo. Cada cópia é baixada pelo endereço "id_", que devolve o arquivo original
sem a moldura do arquivo, e uma vez só: cópia arquivada não muda. O robots.txt do site original também
tem de permitir o endereço, porque o arquivo não serve para contornar a recusa de uma fonte.
"""
import json
import re
from datetime import date
from pathlib import PurePosixPath
from urllib.parse import unquote, urlencode, urlsplit

from .base import PADRAO_DATA, Candidato, Coletor, data_no_nome

CDX = "https://web.archive.org/cdx/search/cdx"
LIMITE_CDX = 5000


def _data(timestamp: str) -> date:
    return date(int(timestamp[:4]), int(timestamp[4:6]), int(timestamp[6:8]))


class Wayback(Coletor):
    """Configuração:

    - enderecos: endereços de material ou prefixos (terminados em /) cujo histórico interessa;
    - incluir / excluir: expressões sobre o endereço original (padrão: PDFs);
    - desde / ate: limites das cópias (AAAA ou AAAAMMDD);
    - data_no_nome: como em página pública; sem data no nome, vale o dia da primeira cópia daquele conteúdo.
    """

    tipo = "wayback"
    rotulo = "Histórico no arquivo da web"
    obrigatorios = ("enderecos",)
    imutavel = True

    def descobrir(self, config: dict, http, estado: dict) -> list[Candidato]:
        incluir = re.compile(config.get("incluir", r"\.pdf(\?|$)"), re.I)
        excluir = re.compile(config["excluir"], re.I) if config.get("excluir") else None
        padrao_data = config.get("data_no_nome", PADRAO_DATA)
        # A mesma versão aparece sob variações do endereço (www, ?v=...): vale a cópia mais antiga de cada conteúdo.
        primeira_copia: dict[str, tuple[str, str]] = {}
        for endereco in config["enderecos"]:
            for timestamp, url_original, digest in self._copias(endereco, config, http):
                if not incluir.search(url_original) or (excluir and excluir.search(url_original)):
                    continue
                if digest not in primeira_copia or timestamp < primeira_copia[digest][0]:
                    primeira_copia[digest] = (timestamp, url_original)
        candidatos = []
        for timestamp, url_original in sorted(primeira_copia.values()):
            copia = _data(timestamp)
            nome = unquote(PurePosixPath(urlsplit(url_original).path).name)
            candidatos.append(Candidato(
                url=f"https://web.archive.org/web/{timestamp}id_/{url_original}",
                url_original=url_original,
                titulo=nome,
                nome_arquivo=f"{PurePosixPath(nome).stem}_wayback_{copia:%Y-%m-%d}.pdf",
                data_versao=data_no_nome(url_original, padrao_data) or copia,
                observacoes=[f"cópia guardada pelo arquivo da web em {copia:%d/%m/%Y}"],
            ))
        return candidatos

    def _copias(self, endereco: str, config: dict, http) -> list[list[str]]:
        parametros = {"url": endereco, "output": "json", "fl": "timestamp,original,digest",
                      "filter": "statuscode:200", "collapse": "digest", "limit": LIMITE_CDX}
        if endereco.endswith("/"):
            parametros["matchType"] = "prefix"
        if config.get("desde"):
            parametros["from"] = str(config["desde"])
        if config.get("ate"):
            parametros["to"] = str(config["ate"])
        resposta = http.get(f"{CDX}?{urlencode(parametros)}")
        linhas = json.loads(resposta.conteudo or b"[]")
        return linhas[1:]  # a primeira linha é o cabeçalho
