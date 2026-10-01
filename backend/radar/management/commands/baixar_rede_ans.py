from django.conf import settings
from django.core.management.base import BaseCommand

from leitor.rede import construir
from radar import servicos
from radar.models import ColunaLida, TabelaPublicada


class Command(BaseCommand):
    help = ("Baixa dos dados abertos da ANS a rede hospitalar e os pedidos de mudança de rede dos planos acompanhados "
            "(só o trecho de cada UF, por HTTP Range) e avisa no radar as mudanças deferidas.")

    def add_arguments(self, parser):
        parser.add_argument("--ufs", help="só estas UFs (ex.: DF,SP); padrão: todas")
        parser.add_argument("--anos", help="anos de pedidos de mudança de rede; padrão: os dois últimos publicados")

    def handle(self, *args, ufs, anos, **opts):
        planos = set(ColunaLida.objects.exclude(registro_ans="").values_list("registro_ans", flat=True))
        planos |= set(TabelaPublicada.objects.values_list("registro_ans", flat=True))
        contagem = construir(settings.DADOS_ANS / "rede.sqlite", planos, set(ufs.upper().split(",")) if ufs else None,
                             [int(a) for a in anos.split(",")] if anos else None, avisar=self.stdout.write)
        avisos = servicos.sincronizar_rede()
        self.stdout.write(f"{len(planos)} planos: {contagem['rede']} vínculos de hospital, {contagem['alteracoes']} pedidos de mudança de rede; "
                          f"{avisos} aviso(s) novo(s) no radar")
