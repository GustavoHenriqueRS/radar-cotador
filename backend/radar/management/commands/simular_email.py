"""Envia ao servidor de e-mail local da demonstração (GreenMail) três mensagens simuladas.

Uma da operadora, autenticada, com a tabela dentro de um .zip; uma com o mesmo remetente sem
autenticação (From falsificado); uma de domínio fora da lista. A captura deve aceitar só a primeira.
O cabeçalho Authentication-Results é o que o servidor de entrada da empresa gravaria; aqui ele é simulado.
"""
import io
import os
import smtplib
import zipfile
from email.message import EmailMessage

from django.conf import settings
from django.core.management.base import BaseCommand

TABELA = settings.RAIZ / "amostras" / "publicas" / "unimed_guarulhos_pme_2026.pdf"
AUTENTICADO = ("mx.radar.test; dkim=pass header.i=@unimedguarulhos.exemplo header.s=s1; "
               "dmarc=pass (p=reject) header.from=unimedguarulhos.exemplo")


class Command(BaseCommand):
    help = "Envia mensagens simuladas com tabela anexa ao servidor de e-mail local da demonstração."

    def add_arguments(self, parser):
        parser.add_argument("--servidor", default=os.environ.get("COLETA_EMAIL_SERVIDOR") or "localhost")
        parser.add_argument("--porta", type=int, default=3025)

    def handle(self, *args, servidor, porta, **opts):
        pdf = TABELA.read_bytes()
        pacote = io.BytesIO()
        with zipfile.ZipFile(pacote, "w") as z:
            z.writestr("tabelas/Nova-tabela-pme-2026.pdf", pdf)
        mensagens = [
            ("Comercial <comercial@unimedguarulhos.exemplo>", AUTENTICADO, "Tabelas PME vigentes", ("tabelas_pme.zip", pacote.getvalue(), "zip")),
            ("Comercial <comercial@unimedguarulhos.exemplo>", "", "Tabela PME (remetente sem autenticação)", ("tabela.pdf", pdf, "pdf")),
            ("Vendas <vendas@outra.exemplo>", AUTENTICADO.replace("unimedguarulhos", "outra"), "Tabela de remetente fora da lista", ("tabela.pdf", pdf, "pdf")),
        ]
        with smtplib.SMTP(servidor, porta, timeout=30) as smtp:
            for remetente, autenticacao, assunto, (nome, conteudo, subtipo) in mensagens:
                m = EmailMessage()
                m["From"], m["To"], m["Subject"] = remetente, "tabelas@radar.test", f"[simulado] {assunto}"
                if autenticacao:
                    m["Authentication-Results"] = autenticacao
                m.set_content("Mensagem simulada para a demonstração do Radar.")
                m.add_attachment(conteudo, maintype="application", subtype=subtipo, filename=nome)
                smtp.send_message(m)
        self.stdout.write(f"3 mensagens simuladas enviadas para tabelas@radar.test em {servidor}:{porta}; a captura deve aceitar só a primeira")
