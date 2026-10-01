"""Cliente HTTP educado: identifica-se, respeita o robots.txt, espaça os pedidos e baixa só o que mudou."""
import re
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from urllib.parse import quote, unquote, urlsplit, urlunsplit

from .base import Bloqueado

AGENTE = "RadarCotador/0.1 (coleta de tabelas de venda; respeita robots.txt)"
LIMITE_BYTES = 60 * 1024 * 1024


@dataclass
class Resposta:
    status: int
    conteudo: bytes = b""
    etag: str = ""
    modificado_em: str = ""
    tipo: str = ""


@dataclass
class Robots:
    """As regras de um robots.txt para o nosso robô, como a RFC 9309 manda.

    Duas diferenças para o parser da biblioteca padrão do Python, que importam na prática:
    - vale a regra que casa com o trecho mais longo do endereço (Allow ganha no empate), e não a primeira
      do arquivo;
    - "*" casa qualquer sequência e "$" marca o fim. Sem isso, "Disallow: /*?version=*" (NotreDame) não
      proíbe nada.
    """

    regras: list[tuple[bool, str]] = field(default_factory=list)
    atraso: float | None = None
    tudo: bool | None = None  # True ou False quando o robots.txt nem pôde ser lido

    def permite(self, url: str) -> bool:
        if self.tudo is not None:
            return self.tudo
        partes = urlsplit(url)
        caminho = unquote(partes.path or "/") + (f"?{unquote(partes.query)}" if partes.query else "")
        melhor: tuple[int, bool] | None = None
        for permite, padrao in self.regras:
            if padrao and _casa(padrao, caminho) and (melhor is None or (len(padrao), permite) > melhor):
                melhor = (len(padrao), permite)
        return True if melhor is None else melhor[1]


def _casa(padrao: str, caminho: str) -> bool:
    ancorado = padrao.endswith("$")
    corpo = unquote(padrao[:-1] if ancorado else padrao)
    return re.match("".join(".*" if c == "*" else re.escape(c) for c in corpo) + ("$" if ancorado else ""), caminho) is not None


def regras_do_robots(texto: str, agente: str = AGENTE) -> Robots:
    """O grupo do nosso robô (pelo nome do produto) ou, se não houver, o de "*". Linha em branco não encerra o grupo.

    O robots.txt da Unimed põe uma linha em branco logo depois de "User-agent: *", e o parser da biblioteca
    padrão descarta as regras que vêm depois: liberaria justamente /site/documents/, onde ficam as tabelas.
    """
    produto = agente.split("/")[0].strip().lower()
    grupos: list[dict] = []
    atual, lendo_agentes = None, False
    for linha in texto.splitlines():
        linha = linha.split("#", 1)[0].strip()
        if ":" not in linha:
            continue
        campo, valor = (parte.strip() for parte in linha.split(":", 1))
        campo = campo.lower()
        if campo == "user-agent":
            if atual is None or not lendo_agentes:
                atual = {"agentes": set(), "regras": [], "atraso": None}
                grupos.append(atual)
            atual["agentes"].add(valor.lower())
            lendo_agentes = True
            continue
        lendo_agentes = False
        if atual is None:
            continue
        if campo in ("allow", "disallow"):
            atual["regras"].append((campo == "allow", valor))
        elif campo == "crawl-delay":
            try:
                atual["atraso"] = float(valor)
            except ValueError:
                pass
    meus = [g for g in grupos if produto in g["agentes"]] or [g for g in grupos if "*" in g["agentes"]]
    return Robots([r for g in meus for r in g["regras"]], next((g["atraso"] for g in meus if g["atraso"] is not None), None))


def url_segura(url: str) -> str:
    """O endereço como o navegador o pede: espaço e acento codificados, o que já vem codificado fica como está.

    A API da CORPe devolve "TABELA HAPVIDA_ANAPOLIS_V.1.pdf", com espaço, e a biblioteca padrão recusa o pedido.
    """
    partes = urlsplit(url)
    return urlunsplit(partes._replace(path=quote(partes.path, safe="/%:@!$&'()*+,;=-._~"),
                                      query=quote(partes.query, safe="/%:@!$&'()*+,;=-._~?")))


class Http:
    def __init__(self, agente: str = AGENTE, intervalo: float = 1.0, timeout: float = 60):
        self.agente, self.intervalo, self.timeout = agente, intervalo, timeout
        self._robots: dict[str, Robots] = {}
        self._ultimo_pedido: dict[str, float] = {}

    def _robots_de(self, url: str) -> Robots:
        base = "{0.scheme}://{0.netloc}".format(urlsplit(url))
        if base not in self._robots:
            try:
                pedido = urllib.request.Request(f"{base}/robots.txt", headers={"User-Agent": self.agente})
                with urllib.request.urlopen(pedido, timeout=self.timeout) as r:
                    self._robots[base] = regras_do_robots(r.read(512 * 1024).decode("utf-8", "replace"), self.agente)
            except urllib.error.HTTPError as e:
                # Sem robots.txt (404, 410), não há restrição. Acesso negado ou erro do servidor: o lado
                # conservador, um passo além da RFC 9309, que liberaria o 401 e o 403.
                self._robots[base] = Robots(tudo=e.code in (404, 410))
            except (urllib.error.URLError, TimeoutError):
                self._robots[base] = Robots(tudo=False)
        return self._robots[base]

    def permitido(self, url: str) -> bool:
        return self._robots_de(url).permite(url)

    def _esperar_vez(self, url: str):
        host = urlsplit(url).netloc
        atraso = max(self._robots_de(url).atraso or 0, self.intervalo)
        espera = self._ultimo_pedido.get(host, 0) + atraso - time.monotonic()
        if espera > 0:
            time.sleep(espera)
        self._ultimo_pedido[host] = time.monotonic()

    def get(self, url: str, etag: str = "", modificado_em: str = "") -> Resposta:
        if not self.permitido(url):
            raise Bloqueado(f"robots.txt não autoriza {url}")
        self._esperar_vez(url)
        cabecalhos = {"User-Agent": self.agente}
        if etag:
            cabecalhos["If-None-Match"] = etag
        if modificado_em:
            cabecalhos["If-Modified-Since"] = modificado_em
        try:
            with urllib.request.urlopen(urllib.request.Request(url_segura(url), headers=cabecalhos), timeout=self.timeout) as r:
                conteudo = r.read(LIMITE_BYTES + 1)
                if len(conteudo) > LIMITE_BYTES:
                    raise ValueError(f"arquivo acima de {LIMITE_BYTES // 2**20} MB: {url}")
                return Resposta(r.status, conteudo, r.headers.get("ETag", ""), r.headers.get("Last-Modified", ""),
                                r.headers.get("Content-Type", ""))
        except urllib.error.HTTPError as e:
            if e.code == 304:
                return Resposta(304, etag=etag, modificado_em=modificado_em)
            raise
