"""Captura de materiais de venda: descobre tabelas novas nas fontes e baixa só o que mudou.

Igual ao leitor, o motor é genérico e cada fonte é configuração. Um tipo de captura (página pública
com links, URL direta, API pública em JSON, histórico no arquivo da web, caixa de e-mail) é uma classe
pequena que só sabe descobrir candidatos; robots.txt, intervalo entre pedidos, identificação, download
condicional e deduplicação são do motor e valem para todos.
"""
from .api_json import ApiJson
from .base import Bloqueado, Candidato, Coletor, chave_da_serie, original
from .caixa_email import CaixaEmail
from .pagina import PaginaPublica
from .url_direta import UrlDireta
from .wayback import Wayback

TIPOS: dict[str, Coletor] = {c.tipo: c for c in (PaginaPublica(), UrlDireta(), ApiJson(), Wayback(), CaixaEmail())}

__all__ = ["TIPOS", "Bloqueado", "Candidato", "Coletor", "chave_da_serie", "original"]
