from django.core.management.base import BaseCommand

from radar.coleta import coletar
from radar.models import Captura


class Command(BaseCommand):
    help = "Coleta as capturas automáticas: é o que o agendador (cron, Celery beat) chama."

    def add_arguments(self, parser):
        parser.add_argument("--fonte", help="nome da fonte: todas as capturas dela, ativas ou não")
        parser.add_argument("--captura", type=int, help="id de uma captura")
        parser.add_argument("--limite", type=int, help="no máximo N materiais por captura (teste: não avança o marcador do e-mail)")
        parser.add_argument("--llm", default="auto", choices=["auto", "gravada", "nao"], help="leitura por LLM dos materiais novos")

    def handle(self, *args, fonte, captura, limite, llm, **opts):
        capturas = Captura.objects.select_related("fonte")
        if captura:
            capturas = capturas.filter(pk=captura)
        elif fonte:
            capturas = capturas.filter(fonte__nome=fonte)
        else:
            capturas = capturas.filter(ativa=True)
        for c in capturas:
            r = coletar(c, limite=limite, llm=llm, ler_em_segundo_plano=False)
            self.stdout.write(
                f"{c}: {r.get_situacao_display()} | {r.encontrados} encontrados, {r.novos} novos, {r.conhecidos} já no acervo, "
                f"{r.sem_mudanca} sem mudança, {r.bloqueados} bloqueados, {len(r.erros)} com erro"
                + (f" | {r.mensagem}" if r.mensagem else ""))
