from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from coletor.fontes import PASTA, ler_fontes, ler_operadoras, validar
from radar.models import Captura, Fonte, Operadora


class Command(BaseCommand):
    help = "Carrega as fontes e os fluxos de captura descritos em fontes/*.json; nada é gravado se algum arquivo tiver problema."

    def add_arguments(self, parser):
        parser.add_argument("--pasta", default=str(PASTA))

    def handle(self, *args, pasta, **opts):
        fontes = ler_fontes(Path(pasta))
        if problemas := validar(fontes):
            raise CommandError("configuração de fontes com problema:\n" + "\n".join(f"  - {p}" for p in problemas))
        capturas = 0
        for nome, f in fontes.items():
            fonte, _ = Fonte.objects.update_or_create(nome=nome, defaults={
                "tipo": f["tipo"], "url": f.get("url", ""), "confiabilidade": f.get("confiabilidade", 3), "observacoes": f.get("observacoes", "")})
            for c in f["capturas"]:
                Captura.objects.update_or_create(fonte=fonte, tipo=c["tipo"], nome=c.get("nome", ""),
                                                 defaults={"config": c.get("config", {}), "ativa": c.get("ativa", False)})
                capturas += 1
        operadoras = ler_operadoras(Path(pasta))
        for registro, o in operadoras.items():
            Operadora.objects.update_or_create(registro_ans=registro, defaults={
                "nome": o["nome"], "canal": o.get("canal", ""), "relatorio": o.get("relatorio", "")})
        self.stdout.write(f"{len(fontes)} fontes, {capturas} capturas e {len(operadoras)} operadoras mapeadas, de {pasta}")
