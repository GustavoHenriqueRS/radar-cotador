"""Exporta o acervo de demonstração para a versão estática do protótipo, que abre no navegador sem servidor.

Grava as respostas da API que as telas leem, as páginas dos PDFs em WebP, os PDFs originais (para baixar) e o que
a cotação precisa para rodar no navegador com o mesmo cálculo de `servicos.cotar`. Só lê o banco.
"""
import json
import shutil
from pathlib import Path

import pypdfium2 as pdfium
from django.core.management.base import BaseCommand
from django.test import Client
from django.utils import timezone

from leitor.faixas import formatar_registro
from radar import servicos
from radar.models import Captura, Documento, TabelaPublicada

UFS = ("AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO", "MA", "MG", "MS", "MT", "PA", "PB", "PE", "PI", "PR",
       "RJ", "RN", "RO", "RR", "RS", "SC", "SE", "SP", "TO")


class Command(BaseCommand):
    help = "Exporta o acervo de demonstração (API, páginas e cotação) para a versão estática do protótipo."

    def add_arguments(self, parser):
        parser.add_argument("saida", help="pasta de destino; vira demo/ dentro do build estático")
        parser.add_argument("--largura", type=int, default=1100, help="largura das páginas em pixels")

    def handle(self, *args, saida, largura, **opts):
        destino = Path(saida)
        cliente = Client(HTTP_HOST="localhost")

        def gravar(nome: str, url: str):
            resposta = cliente.get(url)
            if resposta.status_code != 200:
                raise RuntimeError(f"{url} respondeu {resposta.status_code}")
            arquivo = destino / "api" / f"{nome}.json"
            arquivo.parent.mkdir(parents=True, exist_ok=True)
            arquivo.write_bytes(resposta.content)
            return json.loads(resposta.content)

        gravar("painel", "/api/painel")
        gravar("operadoras", "/api/operadoras")
        gravar("documentos", "/api/documentos")
        gravar("documentos_em_revisao", "/api/documentos?status=em_revisao")
        gravar("eventos", "/api/eventos?limite=500")
        gravar("fontes", "/api/fontes")
        tabelas = gravar("tabelas", "/api/tabelas")
        for doc in Documento.objects.all():
            gravar(f"documentos/{doc.pk}", f"/api/documentos/{doc.pk}")
        for t in tabelas:
            gravar(f"tabelas/{t['id']}/rede", f"/api/tabelas/{t['id']}/rede")
        registros = sorted({t.registro_ans for t in TabelaPublicada.objects.all()})
        for registro in registros:
            gravar(f"tabelas/historico/{registro}", f"/api/tabelas/historico/{registro}")
        for captura in Captura.objects.all():
            gravar(f"capturas/{captura.pk}/coletas", f"/api/capturas/{captura.pk}/coletas")

        (destino / "cotacao.json").write_text(json.dumps(self._cotacao(), ensure_ascii=False, default=str), encoding="utf-8")
        paginas = self._paginas(destino / "paginas", largura)
        (destino / "pdfs").mkdir(parents=True, exist_ok=True)
        for doc in Documento.objects.all():
            shutil.copyfile(doc.arquivo.path, destino / "pdfs" / f"{doc.pk}.pdf")
        self.stdout.write(f"{len(tabelas)} tabelas, {len(registros)} registros e {paginas} páginas exportados para {destino}")

    def _cotacao(self) -> dict:
        """Tudo o que `servicos.cotar` usa, já resolvido, para o navegador refazer a conta com qualquer idade e UF."""
        ativas = list(TabelaPublicada.objects.filter(ativa=True).select_related("documento", "fonte"))
        por_registro: dict[str, list[TabelaPublicada]] = {}
        for t in ativas:
            por_registro.setdefault(t.registro_ans, []).append(t)
        tabelas = [{
            "tabela_id": t.id, "registro": t.registro_ans, "registro_ans": formatar_registro(t.registro_ans),
            "plano": t.nome_plano, "operadora": t.operadora, "fonte": str(t.fonte) if t.fonte else "",
            "condicao": t.condicao, "tipo_contratacao": t.tipo_contratacao, "precos": t.precos,
            "vigencia_inicio": t.vigencia_inicio, "vigencia_fim": t.vigencia_fim, "versao": t.versao,
            "documento": t.documento.nome_original, "documento_id": t.documento_id,
            "referencia": t.confirmada_em or t.publicada_em,
            "dupla_leitura": t.documento.leitura_llm in ("ao_vivo", "gravada"),
            "data_material": t.documento.data_versao,
            "mesmas": [o.id for o in servicos._mesma_condicao(t, por_registro[t.registro_ans]) if o.id != t.id],
        } for t in ativas]
        ix = servicos.rede()
        registros = {}
        for registro in por_registro:
            mudancas = {"": servicos.mudancas_de_rede(registro, so_futuras=True)}
            for uf in UFS:
                if lista := servicos.mudancas_de_rede(registro, uf=uf):
                    mudancas[uf] = lista
            registros[registro] = {"ans": servicos.atributos_ans(registro), "rede": ix.resumo(registro) if ix else None,
                                   "mudancas": mudancas}
        return {"exportado_em": timezone.now(), "faixas": list(servicos.FAIXAS), "tabelas": tabelas, "registros": registros}

    def _paginas(self, pasta: Path, largura: int) -> int:
        total = 0
        for doc in Documento.objects.all():
            pdf = pdfium.PdfDocument(doc.arquivo.path)
            try:
                for numero, pagina in enumerate(pdf, start=1):
                    escala = largura / pagina.get_width()
                    imagem = pagina.render(scale=escala).to_pil()
                    arquivo = pasta / str(doc.pk) / f"{numero}.webp"
                    arquivo.parent.mkdir(parents=True, exist_ok=True)
                    imagem.save(arquivo, "WEBP", quality=72, method=6)
                    total += 1
            finally:
                pdf.close()
        return total
