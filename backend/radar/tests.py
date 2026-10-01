"""Regras do radar que dependem do banco: histórico de versões e o motor de coleta.

Rodam com `python manage.py test radar` (o Django cria um banco de teste no PostgreSQL).
"""
import hashlib
import json
import shutil
import sqlite3
import tempfile
from datetime import date
from decimal import Decimal
from unittest import mock

from django.test import TestCase, override_settings

from coletor.http import Http, Resposta
from leitor.rede import ESQUEMA, IndiceRede, resumir

from . import servicos
from .coleta import coletar
from .models import Captura, CelulaLida, ColunaLida, Documento, Evento, Fonte, ItemColetado, TabelaPublicada

FAIXAS = ["00-18", "19-23", "24-28", "29-33", "34-38", "39-43", "44-48", "49-53", "54-58", "59+"]
REGISTRO = "123456789"


def _precos(base: float) -> list[float]:
    return [round(base * (1.15 ** i), 2) for i in range(10)]


def _doc(fonte: Fonte, data: date, base: float, serie: str = "allcare_unimed_bh") -> Documento:
    doc = Documento.objects.create(
        nome_original=f"{serie}_{data}.pdf", serie=serie, fonte=fonte, data_versao=data, status=Documento.Status.EM_REVISAO,
        sha256=hashlib.sha256(f"{serie}{data}{base}".encode()).hexdigest())
    coluna = ColunaLida.objects.create(documento=doc, ordem=0, pagina=1, registro_ans=REGISTRO, plano_ans={"nome": "Plano Teste"})
    CelulaLida.objects.bulk_create([
        CelulaLida(coluna=coluna, faixa=f, valor_final=Decimal(str(v)), status_leitura="confirmado") for f, v in zip(FAIXAS, _precos(base))])
    return doc


def _historia() -> list[tuple[int, date, float, bool]]:
    """(versão, data do material, preço da 1ª faixa, ativa) na ordem da cadeia."""
    tabelas = list(TabelaPublicada.objects.filter(registro_ans=REGISTRO).select_related("documento"))
    seguinte = {t.substituida_por_id for t in tabelas if t.substituida_por_id}
    t = next(t for t in tabelas if t.id not in seguinte)
    por_id, cadeia = {x.id: x for x in tabelas}, []
    while t:
        cadeia.append((t.versao, t.documento.data_versao, t.precos["00-18"], t.ativa))
        t = por_id.get(t.substituida_por_id)
    assert len(cadeia) == len(tabelas), "todas as versões do produto numa cadeia só"
    return cadeia


class HistoricoTest(TestCase):
    def setUp(self):
        self.fonte = Fonte.objects.create(nome="Allcare", tipo=Fonte.Tipo.PDF_ADMINISTRADORA)

    def test_versao_antiga_nao_substitui_a_vigente(self):
        servicos.publicar(_doc(self.fonte, date(2026, 9, 8), 300))
        antiga = _doc(self.fonte, date(2024, 9, 3), 200)
        r = servicos.publicar(antiga)
        self.assertTrue(r["historico"])
        self.assertEqual(_historia(), [(1, date(2024, 9, 3), 200.0, False), (2, date(2026, 9, 8), 300.0, True)])
        antiga.refresh_from_db()
        self.assertEqual(antiga.status, Documento.Status.HISTORICO)
        self.assertEqual(servicos.cotar([30])[0]["total"], _precos(300)[3])
        evento = Evento.objects.get(tipo=Evento.Tipo.VERSAO_HISTORICA)
        self.assertIn("+50,0%", evento.titulo)

    def test_versao_do_meio_entra_entre_as_duas(self):
        servicos.publicar(_doc(self.fonte, date(2024, 9, 3), 200))
        servicos.publicar(_doc(self.fonte, date(2026, 9, 8), 300))
        servicos.publicar(_doc(self.fonte, date(2025, 8, 1), 250))
        self.assertEqual(_historia(), [(1, date(2024, 9, 3), 200.0, False), (2, date(2025, 8, 1), 250.0, False),
                                       (3, date(2026, 9, 8), 300.0, True)])

    def test_versao_nova_continua_o_historico_coletado(self):
        # As cópias antigas chegam antes de a versão atual ser publicada (ela está em revisão).
        atual = _doc(self.fonte, date(2026, 9, 8), 300)
        servicos.guardar_se_antiga(_doc(self.fonte, date(2025, 8, 1), 250).id)
        servicos.guardar_se_antiga(_doc(self.fonte, date(2024, 9, 3), 200).id)
        self.assertFalse(TabelaPublicada.objects.filter(ativa=True).exists())
        servicos.publicar(atual)
        self.assertEqual(_historia(), [(1, date(2024, 9, 3), 200.0, False), (2, date(2025, 8, 1), 250.0, False),
                                       (3, date(2026, 9, 8), 300.0, True)])
        self.assertTrue(Evento.objects.filter(tipo=Evento.Tipo.REAJUSTE, titulo__contains="+20,0%").exists())

    def test_versao_antiga_com_o_mesmo_preco_nao_vira_versao(self):
        servicos.publicar(_doc(self.fonte, date(2026, 9, 8), 300))
        r = servicos.publicar(_doc(self.fonte, date(2026, 3, 1), 300))
        self.assertEqual((r["publicadas"], r["sem_mudanca"]), (0, 1))
        self.assertEqual(len(_historia()), 1)


CDX = [["timestamp", "original", "digest"],
       ["20240903120000", "https://www.corretorallcare.com.br/arquivos/pdf/tabelas/tabela_adesao_unimed_bh_mg.pdf", "AAA"],
       ["20240903120000", "https://www.corretorallcare.com.br/arquivos/pdf/tabelas/tabela_adesao_samel_am.pdf", "BBB"]]


def _pdf_minimo(marca: str) -> bytes:
    """Um PDF de verdade, de uma página em branco, diferente para cada marca."""
    import io

    import pypdfium2 as pdfium

    pdf, saida = pdfium.PdfDocument.new(), io.BytesIO()
    pdf.new_page(595, 842)
    pdf.save(saida)
    return saida.getvalue() + f"\n% {marca}\n".encode()


class HttpFalso:
    def __init__(self, permitidos=("web.archive.org", "www.corretorallcare.com.br")):
        self.permitidos, self.pedidos = permitidos, []

    def get(self, http, url, etag="", modificado_em=""):
        self.pedidos.append(url)
        if url.startswith("https://web.archive.org/cdx/"):
            return Resposta(200, json.dumps(CDX).encode())
        return Resposta(200, _pdf_minimo(url))

    def permitido(self, http, url):
        return any(f"//{h}/" in url for h in self.permitidos)


class ColetaTest(TestCase):
    def setUp(self):
        self.media = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.media, ignore_errors=True)
        override = override_settings(MEDIA_ROOT=self.media)
        override.enable()
        self.addCleanup(override.disable)
        self.fonte = Fonte.objects.create(nome="Allcare", tipo=Fonte.Tipo.PDF_ADMINISTRADORA)
        Documento.objects.create(
            nome_original="tabela_adesao_unimed_bh_mg.pdf", serie="allcare_unimed_bh_adesao_mg", fonte=self.fonte, data_versao=date(2026, 9, 8),
            url_origem="https://www.corretorallcare.com.br/arquivos/pdf/tabelas/tabela_adesao_unimed_bh_mg.pdf", sha256="0" * 64)
        self.captura = Captura.objects.create(fonte=self.fonte, tipo="wayback", config={
            "enderecos": ["https://www.corretorallcare.com.br/arquivos/pdf/tabelas/"], "somente_series_conhecidas": True, "intervalo_s": 0})

    def _coletar(self, http: HttpFalso):
        with mock.patch.object(Http, "get", lambda s, url, etag="", modificado_em="": http.get(s, url, etag, modificado_em)), \
             mock.patch.object(Http, "permitido", lambda s, url: http.permitido(s, url)), \
             mock.patch.object(servicos, "processar"), mock.patch.object(servicos, "guardar_se_antiga"):
            return coletar(self.captura, llm="nao", ler_em_segundo_plano=False)

    def test_copia_arquivada_entra_na_serie_da_tabela_viva_e_so_e_baixada_uma_vez(self):
        http = HttpFalso()
        c = self._coletar(http)
        self.assertEqual((c.situacao, c.encontrados, c.novos), ("ok", 1, 1))  # a tabela do Samel não é acompanhada
        copia = Documento.objects.get(nome_original="tabela_adesao_unimed_bh_mg_wayback_2024-09-03.pdf")
        self.assertEqual((copia.serie, copia.data_versao), ("allcare_unimed_bh_adesao_mg", date(2024, 9, 3)))
        self.assertTrue(copia.url_origem.startswith("https://web.archive.org/web/20240903120000id_/"))
        self.assertTrue(Evento.objects.filter(tipo=Evento.Tipo.VERSAO_COLETADA, titulo__contains="1 versão(ões) antiga(s)").exists())
        http.pedidos.clear()
        c = self._coletar(http)
        self.assertEqual((c.novos, c.sem_mudanca), (0, 1))
        self.assertEqual([u for u in http.pedidos if "id_/" in u], [], "cópia arquivada não muda: não se pede de novo")

    def test_robots_do_site_original_vale_para_a_copia(self):
        c = self._coletar(HttpFalso(permitidos=("web.archive.org",)))
        self.assertEqual((c.situacao, c.bloqueados, c.novos), ("bloqueada", 1, 0))
        self.assertEqual(ItemColetado.objects.get(captura=self.captura).situacao, "bloqueado pelo robots.txt")


class RedeTest(TestCase):
    def setUp(self):
        pasta = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, pasta, ignore_errors=True)
        caminho = f"{pasta}/rede.sqlite"
        db = sqlite3.connect(caminho)
        db.executescript(ESQUEMA)
        db.executemany("INSERT INTO rede VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", [
            (REGISTRO, "1", "HOSPITAL A", "Assistencia Hospitalar", 1, "Contratualizado", "Direto", "Total", "Campinas", "SP", "2020-01-01", ""),
            (REGISTRO, "2", "MATERNIDADE DE CAMPINAS", "Assistencia Hospitalar", 0, "Contratualizado", "Direto", "Total", "Campinas", "SP", "2020-01-01", ""),
            (REGISTRO, "3", "HOSPITAL ANTIGO", "Assistencia Hospitalar", 1, "Contratualizado", "Direto", "Total", "Campinas", "SP", "2010-01-01", "2019-01-01"),
        ])
        base = [REGISTRO, "PLANO TESTE", "OPERADORA"]
        meio = ["Redimensionamento por redução", "Rescisão contratual", "MATERNIDADE DE CAMPINAS", "2", "Campinas", "SP", "", "", "", ""]
        db.executemany("INSERT INTO alteracao VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", [
            [*base, "P1", "2026-08-21", *meio, "Deferida", "2026-10-10"],
            [*base, "P2", "2026-08-22", *meio, "Indeferida", ""],
            [*base, "P3", "2025-01-02", *meio, "Deferida", "2025-02-01"],  # já vale há mais de 90 dias
        ])
        resumir(db)
        db.commit()
        db.close()
        patcher = mock.patch.object(servicos, "_rede", IndiceRede(caminho))
        patcher.start()
        self.addCleanup(patcher.stop)
        servicos.publicar(_doc(Fonte.objects.create(nome="Allcare", tipo=Fonte.Tipo.PDF_ADMINISTRADORA), date(2026, 9, 8), 300))

    def test_resumo_conta_so_hospitais_com_vinculo_ativo(self):
        self.assertEqual(servicos.rede().resumo(REGISTRO), {"hospitais": 2, "por_uf": {"SP": {"hospitais": 2, "urgencia": 1}}})

    def test_mudanca_deferida_vira_aviso_uma_vez_so(self):
        with mock.patch.object(servicos.timezone, "localdate", return_value=date(2026, 10, 1)):
            self.assertEqual(servicos.sincronizar_rede(), 1)
            self.assertEqual(servicos.sincronizar_rede(), 0)
            mudancas = servicos.mudancas_de_rede(REGISTRO)
        evento = Evento.objects.get(tipo=Evento.Tipo.REDE_ALTERADA)
        self.assertEqual(evento.titulo, "Plano Teste: Maternidade de Campinas (Campinas/SP) sai da rede em 10/10/2026, sem substituto "
                                        "(redução deferida pela ANS)")
        self.assertEqual((evento.severidade, evento.data_efeito), ("alerta", date(2026, 10, 10)))
        self.assertEqual([m["protocolo"] for m in mudancas], ["P1"])
