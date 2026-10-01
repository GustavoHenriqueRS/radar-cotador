from django.core.management.base import BaseCommand

from radar import servicos


class Command(BaseCommand):
    help = "Confere o que está publicado contra o cadastro atual da ANS (operadoras, planos, rede) e as vigências."

    def handle(self, *args, **opts):
        self.stdout.write(f"{servicos.sincronizar_com_ans()} aviso(s) novo(s) no radar")
