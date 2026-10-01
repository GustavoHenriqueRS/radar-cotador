import io
import json
import urllib.robotparser
import zipfile
from datetime import date
from email.message import EmailMessage

import pytest

from coletor import TIPOS, Bloqueado, caixa_email, chave_da_serie
from coletor.base import data_no_nome
from coletor.http import Http, Resposta, regras_do_robots

AGENTE = "RadarCotador/0.1"

# Como no robots.txt real da Unimed: linha em branco logo depois de "User-Agent: *".
ROBOTS_UNIMED = "User-Agent: *\n\nsitemap: https://www.unimed.coop.br/site/sitemap.xml\n\nDisallow: /web/\nDisallow: /site/documents/\n"

# Como na página real da Allcare: os PDFs ficam em data-url de botões, misturados com aditivos e fichas.
PAGINA = """
<html><body>
<button class="btn" data-titulo="Tabela - Distrito Federal" data-url="/arquivos/tabelas/adesao/df/tabela_adesao_hapvida_distrito_feral_df_16_07_2026.pdf">Tabela</button>
<button disabled class="btn" data-titulo="Maceió - Tabela em atualização" data-url="/arquivos/pdf/tabelas/tabela_pme_hapvida_maceio_al.pdf">x</button>
<a href="#" data-titulo="Aditivo de Redução de Carência" data-url="/arquivos/pdf/arc/arc_adesao_hapvida.pdf">ARC</a>
<a href="/arquivos/pdf/fichas/ficha.pdf">Ficha</a>
<a href="https://outro.site/tabela.pdf">fora</a>
</body></html>
"""


class HttpFalso:
    def __init__(self, conteudo: str):
        self.conteudo = conteudo.encode()
        self.pedidos = []

    def get(self, url, etag="", modificado_em=""):
        self.pedidos.append(url)
        return Resposta(200, self.conteudo)


def test_linha_em_branco_no_robots_nao_libera_o_site():
    url = "https://www.unimed.coop.br/site/documents/20553837/tabela.pdf"
    padrao = urllib.robotparser.RobotFileParser()
    padrao.parse(ROBOTS_UNIMED.splitlines())
    assert padrao.can_fetch(AGENTE, url)  # o parser da biblioteca padrão libera
    assert not regras_do_robots(ROBOTS_UNIMED, AGENTE).permite(url)
    assert regras_do_robots(ROBOTS_UNIMED, AGENTE).permite("https://www.unimed.coop.br/site/web/guarulhos/tabela-de-vendas-corretor")


# Como no robots.txt real da NotreDame (gndi.com.br): curingas que o parser da biblioteca padrão ignora.
ROBOTS_GNDI = "User-agent: *\nDisallow: /*?version=*\nDisallow: /web*\nDisallow: /-/*\nAllow: /documents/\n"


def test_curingas_do_robots():
    regras = regras_do_robots(ROBOTS_GNDI, AGENTE)
    padrao = urllib.robotparser.RobotFileParser()
    padrao.parse(ROBOTS_GNDI.splitlines())
    proibido = "https://www.gndi.com.br/documents/tabela-pme.pdf?version=1.2"
    assert padrao.can_fetch(AGENTE, proibido)  # o parser da biblioteca padrão libera
    assert not regras.permite(proibido)
    assert regras.permite("https://www.gndi.com.br/documents/tabela-pme.pdf")
    assert not regras.permite("https://www.gndi.com.br/web/guest/corretor")


def test_regra_mais_longa_vence_e_allow_ganha_o_empate():
    texto = "User-agent: *\nDisallow: /tabelas/\nAllow: /tabelas/publicas/\nDisallow: /*.zip$\nAllow: /x\nDisallow: /x\n"
    regras = regras_do_robots(texto, AGENTE)
    assert not regras.permite("https://s.com/tabelas/interna.pdf")
    assert regras.permite("https://s.com/tabelas/publicas/adesao.pdf")
    assert not regras.permite("https://s.com/pacote.zip") and regras.permite("https://s.com/pacote.zip.html")
    assert regras.permite("https://s.com/x")


def test_grupo_do_nosso_robo_vale_mais_que_o_geral():
    texto = "User-agent: *\nDisallow: /\n\nUser-agent: OutroRobo\nUser-agent: RadarCotador\nAllow: /tabelas/\nDisallow: /\nCrawl-delay: 5\n"
    regras = regras_do_robots(texto, AGENTE)
    assert regras.permite("https://s.com/tabelas/a.pdf") and not regras.permite("https://s.com/outra.pdf") and regras.atraso == 5


def test_bloqueio_acontece_antes_de_qualquer_download():
    http = Http(agente=AGENTE)
    http._robots["https://www.unimed.coop.br"] = regras_do_robots(ROBOTS_UNIMED)
    with pytest.raises(Bloqueado):
        http.get("https://www.unimed.coop.br/site/documents/20553837/tabela.pdf")


def test_pagina_publica_acha_so_as_tabelas():
    config = {"url": "https://www.corretorallcare.com.br/materiais-de-vendas", "atributos": ["data-url", "href"],
              "titulo": "data-titulo", "incluir": r"corretorallcare\.com\.br/arquivos/(pdf/)?tabelas/.*\.pdf$"}
    candidatos = TIPOS["pagina_publica"].descobrir(config, HttpFalso(PAGINA), {})
    assert [c.url for c in candidatos] == [
        "https://www.corretorallcare.com.br/arquivos/tabelas/adesao/df/tabela_adesao_hapvida_distrito_feral_df_16_07_2026.pdf",
        "https://www.corretorallcare.com.br/arquivos/pdf/tabelas/tabela_pme_hapvida_maceio_al.pdf",
    ]
    df, maceio = candidatos
    assert df.titulo == "Tabela - Distrito Federal" and df.data_versao == date(2026, 7, 16) and not df.observacoes
    assert maceio.data_versao is None and maceio.observacoes  # botão desabilitado: "em atualização"


def test_versoes_do_mesmo_material_tem_a_mesma_chave_de_serie():
    julho = "https://www.corretorallcare.com.br/arquivos/tabelas/adesao/df/tabela_adesao_hapvida_distrito_feral_df_16_07_2026.pdf"
    setembro = "https://corretorallcare.com.br/arquivos/tabelas/adesao/df/tabela_adesao_hapvida_distrito_feral_df_02_09_2026.pdf"
    outra = "https://www.corretorallcare.com.br/arquivos/tabelas/pme/df/tabela_pme_hapvida_distrito_feral_df_16_07_2026.pdf"
    assert chave_da_serie(julho) == chave_da_serie(setembro) != chave_da_serie(outra)
    assert data_no_nome(setembro) == date(2026, 9, 2)
    assert data_no_nome("https://x.com/tabela_20260716.pdf") == date(2026, 7, 16)


def test_url_direta():
    candidatos = TIPOS["url_direta"].descobrir({"urls": [{"url": "https://x.com/t.pdf", "titulo": "Tabela PME"}]}, None, {})
    assert [(c.url, c.titulo) for c in candidatos] == [("https://x.com/t.pdf", "Tabela PME")]


# ------------------------------------------------------------------ histórico no arquivo da web

def test_copia_arquivada_cai_na_serie_do_original():
    viva = "https://www.corretorallcare.com.br/arquivos/pdf/tabelas/tabela_adesao_unimed_bh_mg.pdf"
    copia = "https://web.archive.org/web/20240903120000id_/http://corretorallcare.com.br:80/arquivos/pdf/tabelas/tabela_adesao_unimed_bh_mg.pdf"
    assert chave_da_serie(copia) == chave_da_serie(viva)


# Como a API CDX responde: cabeçalho, a mesma versão sob duas variações do endereço e um arquivo que não é tabela.
CDX = [["timestamp", "original", "digest"],
       ["20240812162732", "https://www.corretorallcare.com.br/arquivos/pdf/tabelas/tabela_adesao_ameplan_sp.pdf", "AAA"],
       ["20240101000000", "https://corretorallcare.com.br/arquivos/pdf/tabelas/tabela_adesao_ameplan_sp.pdf?v=123", "AAA"],
       ["20250510000000", "https://www.corretorallcare.com.br/arquivos/pdf/tabelas/tabela_adesao_ameplan_sp.pdf", "BBB"],
       ["20240812162732", "https://www.corretorallcare.com.br/arquivos/pdf/tabelas/logo.png", "CCC"]]


def test_wayback_lista_cada_versao_uma_vez_pela_copia_mais_antiga():
    http = HttpFalso(json.dumps(CDX))
    candidatos = TIPOS["wayback"].descobrir({"enderecos": ["https://www.corretorallcare.com.br/arquivos/pdf/tabelas/"]}, http, {})
    assert "matchType=prefix" in http.pedidos[0] and "collapse=digest" in http.pedidos[0]
    assert [(c.url, c.data_versao) for c in candidatos] == [
        ("https://web.archive.org/web/20240101000000id_/https://corretorallcare.com.br/arquivos/pdf/tabelas/tabela_adesao_ameplan_sp.pdf?v=123", date(2024, 1, 1)),
        ("https://web.archive.org/web/20250510000000id_/https://www.corretorallcare.com.br/arquivos/pdf/tabelas/tabela_adesao_ameplan_sp.pdf", date(2025, 5, 10)),
    ]
    primeira = candidatos[0]
    assert primeira.url_original.startswith("https://corretorallcare.com.br/")
    assert primeira.nome_arquivo == "tabela_adesao_ameplan_sp_wayback_2024-01-01.pdf"
    assert chave_da_serie(primeira.url) == chave_da_serie("https://www.corretorallcare.com.br/arquivos/pdf/tabelas/tabela_adesao_ameplan_sp.pdf")
    assert TIPOS["wayback"].imutavel


# ------------------------------------------------------------------ caixa de e-mail

PDF = b"%PDF-1.4 tabela de teste"
AUTENTICADO = ("mx.radar.test; dkim=pass header.i=@unimedguarulhos.coop.br header.s=s1; "
               "dmarc=pass (p=reject) header.from=unimedguarulhos.coop.br")


def _email(remetente: str, autenticacao: str, anexos: list[tuple[str, bytes]], assunto="Tabela PME"):
    m = EmailMessage()
    m["From"], m["To"], m["Subject"], m["Date"] = remetente, "tabelas@radar.test", assunto, "Mon, 14 Sep 2026 10:00:00 -0300"
    if autenticacao:
        m["Authentication-Results"] = autenticacao
    m.set_content("Segue a tabela.")
    for nome, conteudo in anexos:
        m.add_attachment(conteudo, maintype="application", subtype="zip" if nome.endswith(".zip") else "pdf", filename=nome)
    return m.as_bytes()


def _zip(arquivos: dict[str, bytes]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as z:
        for nome, conteudo in arquivos.items():
            z.writestr(nome, conteudo)
    return buffer.getvalue()


class ImapFalso:
    """O pedaço do protocolo IMAP que a captura usa, com as respostas no formato do imaplib."""

    caixa: dict[int, bytes] = {}
    validade = b"77"
    pedidos: list = []

    def __init__(self, host, port, timeout=None):
        pass

    def login(self, usuario, senha):
        return "OK", [b"logado"]

    def select(self, pasta, readonly=False):
        assert readonly, "a caixa deve ser aberta só para leitura"
        return "OK", [str(len(self.caixa)).encode()]

    def response(self, codigo):
        return codigo, [self.validade] if codigo == "UIDVALIDITY" else [None]

    def uid(self, comando, *args):
        ImapFalso.pedidos.append((comando, args))
        if comando == "SEARCH":
            inicio = int(args[1].split(":")[0])
            uids = [u for u in sorted(self.caixa) if u >= inicio] or sorted(self.caixa)[-1:]  # "N:*" devolve ao menos a última
            return "OK", [" ".join(map(str, uids)).encode()]
        uid, parte = int(args[0]), args[1]
        bruto = self.caixa[uid]
        if "HEADER.FIELDS" in parte:
            bruto = bruto.split(b"\n\n", 1)[0] + b"\n\n"
        return "OK", [(f"1 (UID {uid} BODY[] {{{len(bruto)}}}".encode(), bruto), b")"]

    def logout(self):
        return "BYE", []


CONFIG_EMAIL = {"servidor": "localhost", "porta": 3143, "ssl": False, "usuario": "tabelas@radar.test", "senha_env": "SENHA_TESTE",
                "remetentes": ["@unimedguarulhos.coop.br"], "autenticado_por": "mx.radar.test"}


@pytest.fixture
def caixa(monkeypatch):
    monkeypatch.setenv("SENHA_TESTE", "x")
    monkeypatch.setattr(caixa_email.imaplib, "IMAP4", ImapFalso)
    ImapFalso.caixa, ImapFalso.validade, ImapFalso.pedidos = {}, b"77", []
    return ImapFalso


def test_email_aceita_so_remetente_autorizado_e_autenticado(caixa):
    caixa.caixa = {
        1: _email("comercial@unimedguarulhos.coop.br", AUTENTICADO,
                  [("tabela_pme_2026-09-14.pdf", PDF), ("pacote.zip", _zip({"pasta/adesao.pdf": PDF, "leia.txt": b"x"}))]),
        # From falsificado: a assinatura é de outro domínio.
        2: _email("comercial@unimedguarulhos.coop.br",
                  "mx.radar.test; dkim=pass header.d=golpe.com; dmarc=fail header.from=unimedguarulhos.coop.br", [("falsa.pdf", PDF)]),
        # Resultado de autenticação escrito por quem enviou, não pelo servidor da caixa.
        3: _email("comercial@unimedguarulhos.coop.br", AUTENTICADO.replace("mx.radar.test", "mx.golpe.com"), [("falsa2.pdf", PDF)]),
        4: _email("vendas@outra-operadora.com.br", AUTENTICADO, [("outra.pdf", PDF)]),
    }
    estado = {}
    candidatos = TIPOS["caixa_email"].descobrir(CONFIG_EMAIL, None, estado)
    assert [c.nome_arquivo for c in candidatos] == ["tabela_pme_2026-09-14.pdf", "adesao.pdf"]
    pme, adesao = candidatos
    assert pme.conteudo == PDF and pme.data_versao == date(2026, 9, 14) and adesao.data_versao == date(2026, 9, 14)
    assert pme.chave_serie == "unimedguarulhos.coop.br/tabela_pme.pdf"
    assert pme.url.startswith("imap://tabelas%40radar.test@localhost/INBOX;UIDVALIDITY=77/;UID=1/")
    assert estado == {"uidvalidade": "77", "ultimo_uid": 4}
    # O corpo só é baixado das mensagens aceitas pelo cabeçalho.
    assert [a[0] for c, a in caixa.pedidos if c == "FETCH" and "BODY.PEEK[]" in a[1]] == ["1"]


def test_email_continua_de_onde_parou(caixa):
    caixa.caixa = {1: _email("comercial@unimedguarulhos.coop.br", AUTENTICADO, [("t.pdf", PDF)])}
    estado = {}
    assert len(TIPOS["caixa_email"].descobrir(CONFIG_EMAIL, None, estado)) == 1
    assert TIPOS["caixa_email"].descobrir(CONFIG_EMAIL, None, estado) == []  # "2:*" devolve a 1, que já foi lida
    caixa.caixa[2] = _email("comercial@unimedguarulhos.coop.br", AUTENTICADO, [("t2.pdf", PDF)])
    assert [c.nome_arquivo for c in TIPOS["caixa_email"].descobrir(CONFIG_EMAIL, None, estado)] == ["t2.pdf"]
    caixa.validade = b"78"  # a caixa foi recriada: os números das mensagens não valem mais
    assert len(TIPOS["caixa_email"].descobrir(CONFIG_EMAIL, None, estado)) == 2


def test_email_sem_senha_no_ambiente(monkeypatch):
    monkeypatch.delenv("SENHA_TESTE", raising=False)
    with pytest.raises(ValueError, match="SENHA_TESTE"):
        TIPOS["caixa_email"].descobrir(CONFIG_EMAIL, None, {})


# ------------------------------------------------------------------ API pública em JSON

API_CORPE = {"status": True, "data": [
    {"id": 1, "title": "Hapvida Manaus PME", "tables": "https://api.corpe.exemplo/storage/tables/24.02.2026_HAPVIDA_PME_AM.pdf"},
    {"id": 2, "title": "Ameplan", "tables": "https://api.corpe.exemplo/storage/tables/21.09.2026_TABELA_AMEPLAN_V.1.pdf"},
    {"id": 3, "title": "Hapvida Recife Adesão", "tables": None},
]}


def test_api_json_lista_os_pdfs_da_operadora():
    config = {"url": "https://api.corpe.exemplo/api/support_material/listSupportMaterial", "lista": "data", "campo_url": "tables",
              "campo_titulo": "title", "incluir": "hapvida", "data_no_nome": r"/(?P<dia>\d{2})\.(?P<mes>\d{2})\.(?P<ano>20\d{2})_"}
    candidatos = TIPOS["api_json"].descobrir(config, HttpFalso(json.dumps(API_CORPE)), {})
    assert [(c.titulo, c.data_versao) for c in candidatos] == [("Hapvida Manaus PME", date(2026, 2, 24))]
    assert not TIPOS["api_json"].validar(config) and TIPOS["api_json"].validar({"url": "x"}) == ["falta 'campo_url'"]


def test_data_so_com_mes_e_ano_curto():
    assert data_no_nome("https://affix.com.br/wp-content/uploads/manual-hapvida_05-26.pdf", r"[_-](?P<mes>\d{2})-(?P<ano>\d{2})(?=\.pdf$)") == date(2026, 5, 1)


def test_endereco_com_espaco_e_pedido_como_no_navegador():
    from coletor.http import url_segura
    assert url_segura("https://api.x.com/storage/tables/15.09.2026_TABELA HAPVIDA_ANÁPOLIS_V.1.pdf") == \
        "https://api.x.com/storage/tables/15.09.2026_TABELA%20HAPVIDA_AN%C3%81POLIS_V.1.pdf"
    assert url_segura("https://x.com/a%20b.pdf?v=1&q=2") == "https://x.com/a%20b.pdf?v=1&q=2"
