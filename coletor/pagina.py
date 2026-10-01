"""Página pública que lista os materiais (o caso das administradoras): links para PDF na própria página."""
import html
import re
from urllib.parse import urljoin

from .base import PADRAO_DATA, Candidato, Coletor, data_no_nome

# Leitura tolerante de tags: páginas reais têm HTML mal-formado que derruba parsers estritos
# (na Allcare, o html.parser da biblioteca padrão para na tag 181 de uma página de 151 KB).
_TAG = re.compile(r"<(a|button|area|link|option)\b([^>]*)>", re.I | re.S)
_ATRIBUTO = re.compile(r'([\w:-]+)\s*=\s*(?:"([^"]*)"|\'([^\']*)\'|([^\s"\'>]+))', re.S)


def links(pagina: str, base: str, atributos: list[str]) -> list[tuple[str, dict[str, str], bool]]:
    """(url absoluta, atributos da tag, desabilitado) para cada tag com um dos atributos de link."""
    encontrados = []
    for m in _TAG.finditer(pagina):
        bruto = m.group(2)
        attrs = {k.lower(): html.unescape(a or b or c) for k, a, b, c in _ATRIBUTO.findall(bruto)}
        destino = next((attrs[a] for a in atributos if attrs.get(a) and not attrs[a].startswith(("#", "javascript:"))), None)
        if destino:
            encontrados.append((urljoin(base, destino.strip()), attrs, bool(re.search(r"\bdisabled\b", bruto))))
    return encontrados


class PaginaPublica(Coletor):
    """Configuração:

    - url: a página que lista os materiais;
    - atributos: onde a página guarda o link (padrão: href; a Allcare usa data-url em botões);
    - titulo: atributo com o nome do material, se houver;
    - incluir / excluir: expressões sobre a URL (ex.: só tabelas, sem aditivos e fichas);
    - data_no_nome: expressão com dia/mês/ano da versão no nome do arquivo (há um padrão comum).
    """

    tipo = "pagina_publica"
    rotulo = "Página pública com links"
    obrigatorios = ("url",)

    def descobrir(self, config: dict, http, estado: dict) -> list[Candidato]:
        url = config["url"]
        pagina = http.get(url).conteudo.decode("utf-8", "replace")
        padrao_data = config.get("data_no_nome", PADRAO_DATA)
        incluir = re.compile(config.get("incluir", r"\.pdf(\?|$)"), re.I)
        excluir = re.compile(config["excluir"], re.I) if config.get("excluir") else None
        vistos, candidatos = set(), []
        for destino, attrs, desabilitado in links(pagina, url, config.get("atributos", ["href"])):
            if destino in vistos or not incluir.search(destino) or (excluir and excluir.search(destino)):
                continue
            vistos.add(destino)
            candidatos.append(Candidato(
                url=destino,
                titulo=attrs.get(config.get("titulo", ""), "").strip(),
                data_versao=data_no_nome(destino, padrao_data),
                observacoes=["a fonte marca este material como indisponível ou em atualização"] if desabilitado else [],
            ))
        return candidatos
