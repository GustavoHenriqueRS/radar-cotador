"""Carga de demonstração com o acervo de PDFs públicos reais (amostras/manifest.json).

Os materiais antigos são publicados em ordem cronológica para montar um histórico de versões
(reajustes, produtos retirados, fontes divergentes). Nessas versões antigas a aprovação humana é
simulada pela própria carga; os materiais mais recentes ficam "em revisão" para a demonstração.
"""
import json
import re
from datetime import date
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand

from radar import servicos
from radar.models import Captura, Documento, Fonte, Operadora

AMOSTRAS = settings.RAIZ / "amostras"

# (arquivo, ação): ordem cronológica; "publicar" simula a aprovação, "revisar" deixa para a demo.
ROTEIRO = [
    ("wayback_allcare_unimed_bh_adesao_mg_2024-09-03.pdf", "publicar"),
    ("qualicorp_sulamerica_adesao_sp_2024-11.pdf", "publicar"),
    ("affix_hapvida_adesao_df_2025-08.pdf", "publicar"),
    ("allcare_unimed_fortaleza_adesao_ce_2026-02.pdf", "publicar"),
    ("allcare_plamed_adesao_se_2026-08-07.pdf", "publicar"),
    ("wayback_allcare_unimed_rio_preto_adesao_sp_2026-04-27.pdf", "publicar"),
    ("wayback_allcare_unimed_rio_preto_adesao_sp_2026-05-11.pdf", "publicar"),
    ("qualicorp_sulamerica_adesao_sp_2026-06.pdf", "publicar"),
    ("allcare_hapvida_adesao_df_2026-07-16.pdf", "publicar"),
    ("allcare_sao_camilo_adesao_ce_2026-07-31.pdf", "publicar"),
    ("allcare_medsenior_adesao_df_2026-08-13.pdf", "publicar"),
    ("corpe_medsenior_adesao_pr_2026-08-10.pdf", "publicar"),
    ("allcare_unimed_vitoria_adesao_es_2026-08-13.pdf", "publicar"),
    ("allcare_unimed_rio_preto_adesao_sp_2026-08-14.pdf", "publicar"),
    ("allcare_unimed_natal_pme_rn_2026-08-21.pdf", "publicar"),
    ("allcare_unimed_bh_adesao_mg_2026-09-08.pdf", "publicar"),
    ("corpe_hapvida_adesao_df_2026-09-15.pdf", "publicar"),
    ("unimed_ferj_pme_rj_2026-08-17.pdf", "publicar"),
    ("unimed_guarulhos_pme_2026.pdf", "revisar"),
    ("allcare_hapvida_pme_df_2026-07-16.pdf", "revisar"),
    ("safe_unimed_jundiai_adesao_sp_2026-08.pdf", "revisar"),
    ("gndi_pme_web_2024-07.pdf", "revisar"),
    ("simuladas/unimed_guarulhos_pme_2026_ESCANEADA.pdf", "revisar"),
]

# As fontes e os fluxos de captura ficam em fontes/*.json (comando carregar_fontes).

# Operadoras citadas na página do Cotador (lp.cotadordeplanodesaude.com.br), com o registro na ANS.
OPERADORAS_DO_COTADOR = {
    "005711": "Bradesco Saúde", "006246": "SulAmérica Saúde", "339679": "Central Nacional Unimed",
    "326305": "Amil", "368253": "Hapvida", "359017": "NotreDame Intermédica", "395480": "Smile Saúde",
    "320111": "Saúde Sim", "418170": "Quallity Pró Saúde",
}

MESES = {m: i for i, m in enumerate(["janeiro", "fevereiro", "marco", "abril", "maio", "junho", "julho", "agosto",
                                      "setembro", "outubro", "novembro", "dezembro"], start=1)}


def _fonte_do_arquivo(arquivo: str, entrada: dict) -> str:
    if arquivo.startswith("simuladas/"):
        return "Simulação (escaneado)"
    adm = (entrada.get("administradora") or "").lower()
    for nome in ("Allcare", "CORPe Saúde", "Affix", "Qualicorp", "Safe"):
        if nome.split()[0].lower() in adm:
            return nome
    return {"unimed_guarulhos": "Unimed Guarulhos", "gndi": "NotreDame Intermédica",
            "unimed_ferj": "Unimed FERJ"}.get(next((k for k in ("unimed_guarulhos", "gndi", "unimed_ferj") if arquivo.startswith(k)), ""), "Allcare")


def _data_versao(arquivo: str) -> date | None:
    m = re.search(r"(\d{4})-(\d{2})(?:-(\d{2}))?", arquivo)
    return date(int(m.group(1)), int(m.group(2)), int(m.group(3) or 1)) if m else None


def _vigencia(texto: str) -> tuple[date | None, date | None]:
    """'VÁLIDO DE 17/08/2026 A 30/09/2026' ou 'VIGÊNCIA 01 DE JUNHO/26 A 31 DE DEZEMBRO/26'."""
    texto = (texto or "").lower().replace("ç", "c")
    datas = [date(int(a), int(m), int(d)) for d, m, a in re.findall(r"(\d{2})/(\d{2})/(\d{4})", texto)]
    if len(datas) >= 2:
        return datas[0], datas[1]
    extenso = re.findall(r"(\d{1,2}) de (\w+)/(\d{2})", texto)
    if len(extenso) >= 2:
        return tuple(date(2000 + int(a), MESES.get(m, 1), int(d)) for d, m, a in extenso[:2])
    return None, None


class Command(BaseCommand):
    help = "Carrega o acervo de demonstração (PDFs públicos) e monta o histórico de versões."

    def add_arguments(self, parser):
        parser.add_argument("--llm", default="gravada", choices=["auto", "gravada", "nao"],
                            help="gravada: as leituras por LLM gravadas no acervo, sem gastar API; "
                                 "auto: LLM ao vivo se houver chave, senão a gravada; nao: só a geométrica")
        parser.add_argument("--limpar", action="store_true", help="apaga documentos, tabelas e eventos antes de carregar")

    def handle(self, *args, llm, limpar, **opts):
        if limpar:
            import shutil

            from radar.models import Coleta, Evento, ItemColetado, TabelaPublicada

            ItemColetado.objects.all().delete()
            Coleta.objects.all().delete()
            Captura.objects.update(estado={})
            Evento.objects.all().delete()
            TabelaPublicada.objects.all().delete()
            Documento.objects.all().delete()
            shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        self.stdout.write("Índice da ANS...")
        ix = servicos.indice()
        for registro, nome in OPERADORAS_DO_COTADOR.items():
            dados = ix.operadora(registro) or {}
            Operadora.objects.update_or_create(registro_ans=registro, defaults={
                "nome": nome, "no_cotador": True, "ativa": bool(dados.get("ativa", True))})
        call_command("carregar_fontes", stdout=self.stdout)
        fontes = {f.nome: f for f in Fonte.objects.all()}

        manifesto = {e["arquivo"]: e for e in json.loads((AMOSTRAS / "manifest.json").read_text())}
        for arquivo, acao in ROTEIRO:
            caminho = AMOSTRAS / ("publicas" if "/" not in arquivo else "") / arquivo
            if not caminho.exists():
                self.stdout.write(self.style.WARNING(f"  ausente: {arquivo}"))
                continue
            entrada = manifesto.get(Path(arquivo).name, {})
            doc, novo = servicos.registrar(caminho.read_bytes(), Path(arquivo).name, fontes[_fonte_do_arquivo(arquivo, entrada)],
                                           entrada.get("url_origem") or "")
            if not novo and doc.status == Documento.Status.PUBLICADO:
                continue
            inicio, fim = _vigencia(entrada.get("vigencia", ""))
            doc.operadora = entrada.get("operadora") or ""
            doc.administradora = entrada.get("administradora") or ""
            doc.tipo_contratacao = {"adesao": "Coletivo por adesão", "pme": "Coletivo empresarial"}.get(entrada.get("tipo_contratacao"), "")
            doc.data_versao, doc.vigencia_inicio, doc.vigencia_fim = _data_versao(arquivo), inicio, fim
            doc.save()
            servicos.processar(doc.id, llm)
            doc.refresh_from_db()
            linha = f"  {doc.nome_original}: {doc.resumo.get('celulas', 0)} preços, {doc.resumo.get('revisar', 0)} para revisar"
            if acao == "publicar" and doc.status == Documento.Status.EM_REVISAO:
                for coluna in doc.colunas.all():
                    servicos.aprovar_coluna(coluna)
                r = servicos.publicar(doc)
                linha += f" → publicado ({r['publicadas']} versões novas, {r['sem_mudanca']} sem mudança, {r['retiradas']} retiradas)"
            self.stdout.write(linha)
        novos = servicos.sincronizar_com_ans()
        self.stdout.write(self.style.SUCCESS(f"Pronto. Sincronização com a ANS gerou {novos} alerta(s)."))
