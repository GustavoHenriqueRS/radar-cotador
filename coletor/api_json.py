"""Lista de materiais servida em JSON por uma API pública.

É o caso de quem tem a página de tabelas feita em JavaScript: o HTML não traz os links, e o navegador monta a
lista a partir de uma API aberta (CORPe: 152 materiais, um por operadora e praça). Ler a API é o mesmo que
ler a página, sem executar o JavaScript.
"""
import json
import re

from .base import PADRAO_DATA, Candidato, Coletor, data_no_nome


def _caminho(dados, caminho: str):
    for chave in filter(None, caminho.split(".")):
        dados = dados[int(chave)] if isinstance(dados, list) else dados[chave]
    return dados


class ApiJson(Coletor):
    """Configuração:

    - url: o endereço da API (GET, sem autenticação);
    - lista: o caminho até a lista de materiais, com pontos ("data", "resultado.itens"); vazio se a resposta já é a lista;
    - campo_url: o campo de cada item com o endereço do PDF (texto ou lista de textos);
    - campo_titulo: o campo com o nome do material (opcional);
    - incluir / excluir: expressões sobre o título e o endereço juntos (ex.: só uma operadora);
    - data_no_nome: como na página pública.
    """

    tipo = "api_json"
    rotulo = "API pública (JSON)"
    obrigatorios = ("url", "campo_url")

    def descobrir(self, config: dict, http, estado: dict) -> list[Candidato]:
        itens = _caminho(json.loads(http.get(config["url"]).conteudo), config.get("lista", ""))
        incluir = re.compile(config["incluir"], re.I) if config.get("incluir") else None
        excluir = re.compile(config["excluir"], re.I) if config.get("excluir") else None
        padrao_data = config.get("data_no_nome", PADRAO_DATA)
        vistos, candidatos = set(), []
        for item in itens:
            enderecos = item.get(config["campo_url"]) or []
            titulo = str(item.get(config.get("campo_titulo", ""), "") or "").strip()
            for url in [enderecos] if isinstance(enderecos, str) else enderecos:
                texto = f"{titulo} {url}"
                if not url or url in vistos or (incluir and not incluir.search(texto)) or (excluir and excluir.search(texto)):
                    continue
                vistos.add(url)
                candidatos.append(Candidato(url=url, titulo=titulo, data_versao=data_no_nome(url, padrao_data)))
        return candidatos
