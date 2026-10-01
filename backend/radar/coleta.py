"""Captura das fontes: descobre, baixa só o que mudou, registra na série certa e manda ler.

O motor HTTP (robots.txt, intervalo entre pedidos, download condicional) e os tipos de captura ficam no
pacote `coletor`; aqui ficam o histórico de cada coleta, a ligação com as versões anteriores e os avisos
no radar. Captura nova de um tipo que já existe é só configuração (Captura.config).
"""
import hashlib
import logging
import re
import threading
from datetime import date
from email.utils import parsedate_to_datetime
from pathlib import PurePosixPath
from urllib.parse import unquote, urlsplit

import pypdfium2 as pdfium
from django.db import connection
from django.utils import timezone

from coletor import TIPOS, Bloqueado, Candidato, chave_da_serie, original
from coletor.base import PADRAO_DATA, Coletor
from coletor.http import Http, Resposta
from leitor.pdf import TRAVA_PDFIUM

from . import servicos
from .models import Captura, Coleta, Documento, Evento, Fonte, ItemColetado

log = logging.getLogger(__name__)


def coletar(captura: Captura, coleta: Coleta | None = None, limite: int | None = None, llm: str = "auto",
            ler_em_segundo_plano: bool = True) -> Coleta:
    coleta = coleta or Coleta.objects.create(captura=captura)
    fonte, config = captura.fonte, captura.config
    http = Http(intervalo=float(config.get("intervalo_s", 1.0)))
    estado = dict(captura.estado)
    novos: list[tuple[Documento, Candidato]] = []
    try:
        coletor = TIPOS.get(captura.tipo)
        if coletor is None:
            raise ValueError(f"tipo de captura desconhecido: {captura.tipo}")
        candidatos = coletor.descobrir(config, http, estado)
        if config.get("somente_series_conhecidas"):
            # O histórico interessa para o que já se acompanha; o resto do arquivo fica de fora.
            candidatos = [c for c in candidatos if _serie_conhecida(fonte, _chave(c, config), config)]
        coleta.encontrados = len(candidatos)
        processados = candidatos[:limite]
        for candidato in processados:
            _baixar(captura, coletor, candidato, http, coleta, novos)
        if processados and coleta.bloqueados == len(processados):
            coleta.situacao = Coleta.Situacao.BLOQUEADA
            coleta.mensagem = "o robots.txt da fonte não autoriza robôs nesses endereços: entrada por upload, e-mail ou parceria"
        else:
            coleta.situacao = Coleta.Situacao.OK
            # Coleta parcial (--limite) não avança o marcador: o que ficou de fora volta na próxima.
            if limite is None and estado != captura.estado:
                captura.estado = estado
                captura.save(update_fields=["estado"])
    except Bloqueado as e:
        coleta.situacao, coleta.mensagem = Coleta.Situacao.BLOQUEADA, f"{e}: entrada por upload, e-mail ou parceria"[:300]
    except Exception as e:
        log.exception("coleta de %s falhou", captura)
        coleta.situacao, coleta.mensagem = Coleta.Situacao.ERRO, f"{type(e).__name__}: {e}"[:300]
    coleta.terminada_em = timezone.now()
    coleta.save()
    _avisar(captura, coleta, novos)
    if novos:
        ids = [doc.id for doc, _ in novos]
        if ler_em_segundo_plano:
            threading.Thread(target=_ler_em_fila, args=(ids, llm), daemon=True).start()
        else:
            _ler_em_fila(ids, llm, fechar_conexao=False)
    return coleta


def _ler_em_fila(ids: list[int], llm: str, fechar_conexao: bool = True):
    """Um documento por vez: a leitura por LLM já paraleliza as páginas, e a fonte não precisa de mais pressa.

    Versão mais antiga que outra já recebida da mesma série não muda a cotação: entra direto no histórico,
    com as colunas que passaram nas conferências.
    """
    try:
        for doc_id in ids:
            servicos.processar(doc_id, llm)
            servicos.guardar_se_antiga(doc_id)
    finally:
        if fechar_conexao:
            connection.close()


def _chave(candidato: Candidato, config: dict) -> str:
    return candidato.chave_serie or chave_da_serie(candidato.url_original or candidato.url, config.get("data_no_nome", PADRAO_DATA))


def _baixar(captura: Captura, coletor: Coletor, candidato: Candidato, http: Http, coleta: Coleta, novos: list):
    fonte, chave = captura.fonte, _chave(candidato, captura.config)
    item, _ = ItemColetado.objects.get_or_create(
        captura=captura, url=candidato.url[:1000], defaults={"chave_serie": chave[:500], "titulo": candidato.titulo[:300]})
    item.visto_por_ultimo_em = timezone.now()
    if coletor.imutavel and item.sha256:
        coleta.sem_mudanca += 1
        item.situacao = "sem mudança"
        item.save()
        return
    try:
        if candidato.conteudo is not None:
            resposta = Resposta(200, candidato.conteudo, tipo="application/pdf")
        else:
            # A cópia arquivada não serve para contornar a recusa da fonte: o robots.txt do original também vale.
            if candidato.url_original and not http.permitido(candidato.url_original):
                raise Bloqueado(f"o robots.txt de {urlsplit(candidato.url_original).hostname} não autoriza robôs em {candidato.url_original}")
            resposta = http.get(candidato.url, etag=item.etag, modificado_em=item.modificado_em)
    except Bloqueado:
        coleta.bloqueados += 1
        item.situacao = "bloqueado pelo robots.txt"
        item.save()
        return
    except Exception as e:
        coleta.erros.append({"url": candidato.url, "erro": f"{type(e).__name__}: {e}"[:200]})
        item.save()
        return
    if resposta.status == 304:
        coleta.sem_mudanca += 1
        item.situacao = "sem mudança"
        item.save()
        return
    sha = hashlib.sha256(resposta.conteudo).hexdigest()
    if problema := _defeito(resposta):
        coleta.erros.append({"url": candidato.url, "erro": problema})
        if coletor.imutavel:
            # Cópia arquivada ou anexo não mudam: o defeito é permanente, não adianta pedir de novo.
            item.sha256, item.situacao = sha, "arquivo com defeito"
        item.save()
        return
    item.etag, item.modificado_em = resposta.etag[:200], resposta.modificado_em[:100]
    if sha == item.sha256:
        coleta.sem_mudanca += 1
        item.situacao = "sem mudança"
        item.save()
        return
    nome = candidato.nome_arquivo or _nome_arquivo(candidato.url_original or candidato.url)
    doc, novo = servicos.registrar(resposta.conteudo, nome, fonte, candidato.url[:500], _serie(fonte, chave, captura.config))
    item.sha256, item.documento = sha, doc
    if novo:
        doc.data_versao = candidato.data_versao or _data_do_cabecalho(resposta.modificado_em) or date.today()
        doc.save(update_fields=["data_versao"])
        coleta.novos += 1
        novos.append((doc, candidato))
        item.situacao = "novo"
    else:
        coleta.conhecidos += 1
        item.situacao = "já estava no acervo"
    item.save()


def _defeito(resposta: Resposta) -> str:
    """Por que o arquivo não serve, ou "" se é um PDF que abre.

    O arquivo da web guarda cópias truncadas (na Allcare, todas as de maio/2024 pararam em 1 MiB): o
    arquivo começa como PDF, mas não abre, e registrar só daria erro mais adiante.
    """
    conteudo = resposta.conteudo
    if not conteudo.startswith(b"%PDF"):
        return f"a resposta não é um PDF ({resposta.tipo or 'sem tipo'})"
    try:
        with TRAVA_PDFIUM:
            pdfium.PdfDocument(conteudo).close()
    except pdfium.PdfiumError as e:
        incompleto = "" if b"%%EOF" in conteudo[-2048:] else f"; termina sem %%EOF aos {len(conteudo)} bytes: cópia incompleta"
        return f"PDF que não abre ({e}){incompleto}"
    return ""


def _serie_conhecida(fonte: Fonte, chave: str, config: dict) -> str | None:
    """A série do material anterior com a mesma chave (o endereço sem a data), em qualquer captura da fonte."""
    item = (ItemColetado.objects.filter(captura__fonte=fonte, chave_serie=chave[:500]).exclude(documento=None)
            .select_related("documento").order_by("visto_primeiro_em").first())
    if item and item.documento.serie:
        return item.documento.serie
    padrao = config.get("data_no_nome", PADRAO_DATA)
    for doc in Documento.objects.filter(fonte=fonte).exclude(url_origem="").only("url_origem", "serie"):
        if doc.serie and chave_da_serie(doc.url_origem, padrao) == chave:
            return doc.serie
    return None


def _serie(fonte: Fonte, chave: str, config: dict) -> str:
    return _serie_conhecida(fonte, chave, config) or "_".join(p for p in (_slug(fonte.nome), _slug(PurePosixPath(chave).stem)) if p)[:200]


def _slug(texto: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", texto.lower()).strip("_")


def _nome_arquivo(url: str) -> str:
    nome = unquote(PurePosixPath(urlsplit(original(url)).path).name) or "material.pdf"
    return nome if nome.lower().endswith(".pdf") else f"{nome}.pdf"


def _data_do_cabecalho(texto: str) -> date | None:
    try:
        return parsedate_to_datetime(texto).date() if texto else None
    except (TypeError, ValueError):
        return None


def _avisar(captura: Captura, coleta: Coleta, novos: list[tuple[Documento, Candidato]]):
    fonte = captura.fonte
    if novos:
        itens, versoes, antigas = [], 0, 0
        for doc, candidato in novos:
            mais_nova = servicos.versao_mais_nova(doc)
            anterior = (Documento.objects.filter(serie=doc.serie, fonte=fonte, data_versao__lt=doc.data_versao).exclude(pk=doc.pk)
                        .order_by("-data_versao").first())
            if mais_nova:
                antigas += 1
                mensagem = f"versão de {doc.data_versao:%d/%m/%Y}, anterior à de {mais_nova.data_versao:%d/%m/%Y}: vai para o histórico"
            elif anterior:
                versoes += 1
                mensagem = f"versão nova; a anterior é de {anterior.data_versao:%d/%m/%Y}"
            else:
                mensagem = "tabela que ainda não estava no acervo"
            itens.append({
                "documento": doc.nome_original, "plano": candidato.titulo, "url": candidato.url,
                "mensagem": mensagem + ("; " + "; ".join(candidato.observacoes) if candidato.observacoes else ""),
            })
        titulo = f"{fonte.nome} ({captura.nome or captura.get_tipo_display()}): {len(novos)} tabela(s) coletada(s)"
        if versoes:
            titulo += f", {versoes} delas versão nova de tabela já acompanhada"
        if antigas:
            titulo += f", {antigas} versão(ões) antiga(s) para o histórico"
        Evento.objects.create(tipo=Evento.Tipo.VERSAO_COLETADA, severidade="info", titulo=f"{titulo}; leitura automática em andamento"[:300],
                              detalhe={"itens": itens, "coleta": coleta.id})
    nome = f"{fonte.nome} ({captura.nome or captura.get_tipo_display()})"
    if coleta.situacao == Coleta.Situacao.ERRO:
        Evento.objects.create(tipo=Evento.Tipo.COLETA_FALHOU, severidade="alerta", titulo=f"A coleta de {nome} falhou: {coleta.mensagem}"[:300],
                              detalhe={"coleta": coleta.id})
    elif coleta.situacao == Coleta.Situacao.OK and coleta.encontrados == 0 and getattr(TIPOS.get(captura.tipo), "lista_completa", True):
        # A página que listava tabelas e de repente não lista nenhuma quase sempre mudou de formato.
        anterior = captura.coletas.filter(situacao=Coleta.Situacao.OK, encontrados__gt=0).exclude(pk=coleta.pk).first()
        if anterior:
            Evento.objects.create(
                tipo=Evento.Tipo.COLETA_FALHOU, severidade="alerta",
                titulo=f"A coleta de {nome} não encontrou nenhuma tabela (na anterior: {anterior.encontrados}): a página pode ter mudado de formato"[:300],
                detalhe={"coleta": coleta.id})
