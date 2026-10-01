"""Endereço fixo de um material que a fonte substitui no lugar (ex.: link de tabela vigente da operadora)."""
from .base import PADRAO_DATA, Candidato, Coletor, data_no_nome


class UrlDireta(Coletor):
    """Configuração: urls (lista de endereços, ou de {"url", "titulo"})."""

    tipo = "url_direta"
    rotulo = "Endereço fixo do material"
    obrigatorios = ("urls",)

    def descobrir(self, config: dict, http, estado: dict) -> list[Candidato]:
        candidatos = []
        for item in config.get("urls", []):
            url, titulo = (item, "") if isinstance(item, str) else (item["url"], item.get("titulo", ""))
            candidatos.append(Candidato(url=url, titulo=titulo, data_versao=data_no_nome(url, config.get("data_no_nome", PADRAO_DATA))))
        return candidatos
