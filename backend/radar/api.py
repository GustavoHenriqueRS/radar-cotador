import threading
from decimal import Decimal, InvalidOperation

import pypdfium2 as pdfium
from django.conf import settings
from django.db import connection
from django.db.models import Count, Q
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response

from leitor.faixas import formatar_registro
from leitor.pdf import TRAVA_PDFIUM

from . import servicos
from .coleta import coletar
from .models import Captura, CelulaLida, Coleta, ColunaLida, Documento, Evento, Fonte, Operadora, TabelaPublicada


def _doc_resumo(d: Documento) -> dict:
    return {
        "id": d.id, "nome": d.nome_original, "serie": d.serie, "fonte": d.fonte.nome if d.fonte else None,
        "status": d.status, "recebido_em": d.recebido_em, "paginas": d.paginas, "ocr": d.ocr,
        "leitura_llm": d.leitura_llm, "custo_llm_usd": d.custo_llm_usd, "operadora": d.operadora,
        "administradora": d.administradora, "tipo_contratacao": d.tipo_contratacao,
        "vigencia_inicio": d.vigencia_inicio, "vigencia_fim": d.vigencia_fim, "resumo": d.resumo, "erro": d.erro,
    }


def _evento(e: Evento) -> dict:
    return {
        "id": e.id, "tipo": e.tipo, "tipo_nome": e.get_tipo_display(), "severidade": e.severidade, "titulo": e.titulo,
        "registro_ans": formatar_registro(e.registro_ans) if e.registro_ans else "", "operadora": e.operadora,
        "documento_id": e.documento_id, "documento": e.documento.nome_original if e.documento else None,
        "criado_em": e.criado_em, "data_efeito": e.data_efeito, "detalhe": e.detalhe,
    }


@api_view(["GET"])
def painel(request):
    docs = Documento.objects.all()
    celulas = CelulaLida.objects.all()
    total_celulas = celulas.count()
    confirmadas = celulas.filter(status_leitura="confirmado").count()
    automaticas = celulas.filter(revisar=False, corrigida=False).count()
    tabelas = TabelaPublicada.objects.filter(ativa=True)
    hoje = timezone.localdate()
    return Response({
        "documentos": docs.count(),
        "documentos_por_status": dict(docs.values_list("status").annotate(n=Count("id"))),
        "precos_lidos": total_celulas,
        "precos_confirmados_dupla_leitura": confirmadas,
        "precos_sem_revisao": automaticas,
        "precos_revisar": celulas.filter(revisar=True).exclude(coluna__registro_ans="").count(),
        # Colunas sem nº de registro ANS impresso: o problema é identificar o produto, não o preço.
        "precos_sem_produto": celulas.filter(coluna__registro_ans="").count(),
        # Taxa de automação medida na leitura (o resumo é gravado antes de qualquer aprovação humana).
        "precos_com_produto": sum(d.resumo.get("celulas_com_produto", 0) for d in docs),
        "precos_com_produto_sem_revisao": sum(d.resumo.get("celulas_com_produto", 0) - d.resumo.get("revisar_com_produto", 0) for d in docs),
        "tabelas_ativas": tabelas.count(),
        "operadoras_com_tabela": tabelas.values("operadora").distinct().count(),
        "tabelas_vencidas": tabelas.filter(vigencia_fim__lt=hoje).count(),
        "custo_llm_usd": sum((d.custo_llm_usd or 0) for d in docs),
        "eventos_abertos": Evento.objects.filter(resolvido=False).exclude(severidade="info").count(),
        "eventos": [_evento(e) for e in Evento.objects.select_related("documento")[:12]],
    })


@api_view(["GET", "POST"])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def documentos(request):
    if request.method == "POST":
        arquivo = request.FILES.get("arquivo")
        if not arquivo or not arquivo.name.lower().endswith(".pdf"):
            return Response({"erro": "envie um PDF no campo 'arquivo'"}, status=400)
        fonte = Fonte.objects.filter(pk=request.data.get("fonte")).first() if request.data.get("fonte") else None
        doc, novo = servicos.registrar(arquivo.read(), arquivo.name, fonte, request.data.get("url_origem", ""))
        if novo:
            servicos.processar_em_segundo_plano(doc.id)
        return Response({"id": doc.id, "novo": novo, "status": doc.status}, status=201 if novo else 200)
    qs = Documento.objects.select_related("fonte")
    if status := request.query_params.get("status"):
        qs = qs.filter(status=status)
    return Response([_doc_resumo(d) for d in qs])


@api_view(["GET"])
def documento(request, pk):
    d = get_object_or_404(Documento.objects.select_related("fonte"), pk=pk)
    tamanhos = []
    if d.arquivo and d.status != Documento.Status.PROCESSANDO:
        with TRAVA_PDFIUM:
            pdf = pdfium.PdfDocument(d.arquivo.path)
            tamanhos = [list(pdf[i].get_size()) for i in range(len(pdf))]
            pdf.close()
    colunas = []
    for c in d.colunas.prefetch_related("celulas"):
        colunas.append({
            "id": c.id, "ordem": c.ordem, "pagina": c.pagina, "tabela": c.tabela, "coluna": c.coluna,
            "ocorrencia": c.ocorrencia, "registro_ans": formatar_registro(c.registro_ans) if c.registro_ans else "",
            "plano_ans": c.plano_ans, "achados": c.achados, "status": c.status,
            "publicavel": servicos.pode_publicar(c),
            "celulas": [
                {"id": x.id, "faixa": x.faixa, "geometrico": x.valor_geometrico, "llm": x.valor_llm, "calculado": x.valor_calculado,
                 "valor": x.valor_final, "status": x.status_leitura, "caixa": x.caixa, "revisar": x.revisar,
                 "corrigida": x.corrigida}
                for x in sorted(c.celulas.all(), key=lambda x: x.faixa)
            ],
        })
    return Response({
        **_doc_resumo(d), "tamanhos_paginas": tamanhos, "colunas": colunas, "url_origem": d.url_origem,
        "achados_documento": d.achados_documento, "extra_llm": d.extra_llm,
        "eventos": [_evento(e) for e in d.eventos.all()],
    })


@api_view(["GET"])
def pagina(request, pk, numero):
    d = get_object_or_404(Documento, pk=pk)
    destino = settings.MEDIA_ROOT / "paginas" / f"{d.sha256[:16]}_{numero}.png"
    if not destino.exists():
        with TRAVA_PDFIUM:
            pdf = pdfium.PdfDocument(d.arquivo.path)
            try:
                if not 1 <= numero <= len(pdf):
                    raise Http404
                destino.parent.mkdir(parents=True, exist_ok=True)
                pdf[numero - 1].render(scale=2).to_pil().save(destino, optimize=True)
            finally:
                pdf.close()
    return FileResponse(open(destino, "rb"), content_type="image/png")


@api_view(["GET"])
def pdf(request, pk):
    d = get_object_or_404(Documento, pk=pk)
    return FileResponse(open(d.arquivo.path, "rb"), content_type="application/pdf",
                        as_attachment=request.GET.get("baixar") == "1", filename=d.nome_original)


@api_view(["POST"])
def reprocessar(request, pk):
    d = get_object_or_404(Documento, pk=pk)
    servicos.processar_em_segundo_plano(d.id, request.data.get("llm", "auto"))
    return Response({"ok": True})


@api_view(["POST"])
def publicar(request, pk):
    d = get_object_or_404(Documento, pk=pk)
    return Response(servicos.publicar(d))


@api_view(["POST"])
def aprovar_coluna(request, pk):
    servicos.aprovar_coluna(get_object_or_404(ColunaLida, pk=pk))
    return Response({"ok": True})


@api_view(["POST"])
def ignorar_coluna(request, pk):
    coluna = get_object_or_404(ColunaLida, pk=pk)
    coluna.status = ColunaLida.Status.IGNORADA
    coluna.save(update_fields=["status"])
    return Response({"ok": True})


@api_view(["POST"])
def corrigir_celula(request, pk):
    try:
        valor = Decimal(str(request.data.get("valor")).replace(".", "").replace(",", ".")) if "," in str(request.data.get("valor")) else Decimal(str(request.data.get("valor")))
    except (InvalidOperation, TypeError):
        return Response({"erro": "valor inválido"}, status=400)
    servicos.corrigir_celula(get_object_or_404(CelulaLida, pk=pk), valor)
    return Response({"ok": True})


@api_view(["GET"])
def tabelas(request):
    qs = TabelaPublicada.objects.filter(ativa=True).select_related("fonte", "documento")
    if q := request.query_params.get("q"):
        digitos = "".join(ch for ch in q if ch.isdigit())
        qs = qs.filter(Q(nome_plano__icontains=q) | Q(operadora__icontains=q) | (Q(registro_ans__contains=digitos) if digitos else Q(pk__in=[])))
    return Response([_tabela(t) for t in qs[:500]])


def _tabela(t: TabelaPublicada) -> dict:
    referencia = t.confirmada_em or t.publicada_em
    return {
        "id": t.id, "registro_ans": formatar_registro(t.registro_ans), "ocorrencia": t.ocorrencia, "condicao": t.condicao,
        "marcas_condicao": t.marcas_condicao,
        "plano": t.nome_plano, "operadora": t.operadora, "administradora": t.administradora,
        "tipo_contratacao": t.tipo_contratacao, "fonte": t.fonte.nome if t.fonte else None,
        "documento_id": t.documento_id, "documento": t.documento.nome_original, "precos": t.precos,
        "vigencia_inicio": t.vigencia_inicio, "vigencia_fim": t.vigencia_fim, "versao": t.versao,
        "publicada_em": t.publicada_em, "confirmada_em": t.confirmada_em, "ativa": t.ativa,
        "data_material": t.documento.data_versao,
        "dias_desde_confirmacao": (timezone.now() - referencia).days,
        "ans": servicos.atributos_ans(t.registro_ans),
        "rede": servicos.rede().resumo(t.registro_ans) if servicos.rede() else None,
    }


@api_view(["GET"])
def rede_da_tabela(request, pk):
    """Rede hospitalar do produto e os pedidos de mudança de rede, do registro oficial na ANS."""
    t = get_object_or_404(TabelaPublicada, pk=pk)
    ix = servicos.rede()
    if ix is None:
        return Response({"erro": "a rede hospitalar ainda não foi baixada da ANS (comando baixar_rede_ans)"}, status=404)
    uf = (request.query_params.get("uf") or "").upper() or None
    return Response({
        "registro_ans": formatar_registro(t.registro_ans), "plano": t.nome_plano, "atualizado_em": ix.atualizado_em(),
        "resumo": ix.resumo(t.registro_ans), "hospitais": ix.hospitais(t.registro_ans, uf)[:500],
        "mudancas": servicos.mudancas_de_rede(t.registro_ans), "historico_de_mudancas": ix.alteracoes(t.registro_ans)[:200],
        "fonte": "ANS, dados abertos: produtos e prestadores hospitalares; solicitações de alteração de rede hospitalar",
    })


@api_view(["GET"])
def historico(request, registro):
    digitos = "".join(ch for ch in registro if ch.isdigit())
    tabelas = list(TabelaPublicada.objects.filter(registro_ans=digitos).select_related("fonte", "documento"))
    anterior = {t.substituida_por_id: t.id for t in tabelas if t.substituida_por_id}

    def cadeia(t_id: int) -> int:
        while t_id in anterior:
            t_id = anterior[t_id]
        return t_id

    tabelas.sort(key=lambda t: (t.fonte.nome if t.fonte else "", cadeia(t.id), t.versao))
    return Response([{**_tabela(t), "cadeia": cadeia(t.id)} for t in tabelas])


@api_view(["GET"])
def eventos(request):
    qs = Evento.objects.select_related("documento")
    if tipo := request.query_params.get("tipo"):
        qs = qs.filter(tipo=tipo)
    return Response([_evento(e) for e in qs[: int(request.query_params.get("limite", 200))]])


@api_view(["GET"])
def operadoras(request):
    """Saúde da base: as operadoras que o Cotador oferece, conferidas no cadastro da ANS."""
    dados = []
    for o in Operadora.objects.filter(no_cotador=True).order_by("-ativa", "nome"):
        ativas = TabelaPublicada.objects.filter(ativa=True, operadora__icontains=o.nome.split()[0])
        dados.append({
            "registro_ans": o.registro_ans, "nome": o.nome, "ativa": o.ativa, "cancelada_em": o.cancelada_em,
            "motivo_cancelamento": o.motivo_cancelamento, "tabelas_ativas": ativas.count(), "canal": o.canal,
        })
    return Response(dados)


@api_view(["GET"])
def fontes(request):
    return Response([
        {"id": f.id, "nome": f.nome, "tipo": f.tipo, "tipo_nome": f.get_tipo_display(), "url": f.url,
         "confiabilidade": f.confiabilidade, "observacoes": f.observacoes,
         "documentos": f.documento_set.count(), "capturas": [_captura(c) for c in f.capturas.all()]}
        for f in Fonte.objects.order_by("-confiabilidade", "nome").prefetch_related("capturas")
    ])


# O que da configuração aparece na tela: onde a captura olha. Credenciais nunca ficam na configuração
# (a caixa de e-mail guarda só o nome da variável de ambiente com a senha).
def _onde(c: Captura) -> str:
    cfg = c.config
    if c.tipo == "pagina_publica":
        return cfg.get("url", "")
    if c.tipo == "url_direta":
        urls = [u if isinstance(u, str) else u.get("url", "") for u in cfg.get("urls", [])]
        return urls[0] + (f" e mais {len(urls) - 1}" if len(urls) > 1 else "") if urls else ""
    if c.tipo == "wayback":
        return ", ".join(cfg.get("enderecos", []))
    if c.tipo == "caixa_email":
        return f"{cfg.get('usuario', '')} · {cfg.get('pasta', 'INBOX')} · remetentes {', '.join(cfg.get('remetentes', []))}"
    return ""


def _captura(c: Captura) -> dict:
    return {"id": c.id, "tipo": c.tipo, "tipo_nome": c.get_tipo_display(), "nome": c.nome or c.get_tipo_display(),
            "onde": _onde(c), "ativa": c.ativa, "ultima_coleta": _coleta(c.coletas.first())}


def _coleta(c: Coleta | None) -> dict | None:
    if c is None:
        return None
    return {"id": c.id, "situacao": c.situacao, "situacao_nome": c.get_situacao_display(), "iniciada_em": c.iniciada_em,
            "terminada_em": c.terminada_em, "encontrados": c.encontrados, "novos": c.novos, "conhecidos": c.conhecidos,
            "sem_mudanca": c.sem_mudanca, "bloqueados": c.bloqueados, "erros": len(c.erros), "mensagem": c.mensagem}


@api_view(["POST"])
def coletar_captura(request, pk):
    captura = get_object_or_404(Captura.objects.select_related("fonte"), pk=pk)
    if captura.coletas.filter(situacao=Coleta.Situacao.RODANDO).exists():
        return Response({"erro": "já há uma coleta em andamento nesta captura"}, status=409)
    coleta = Coleta.objects.create(captura=captura)

    def rodar():
        try:
            coletar(captura, coleta=coleta, llm=request.data.get("llm", "auto"))
        finally:
            connection.close()

    threading.Thread(target=rodar, daemon=True).start()
    return Response(_coleta(coleta), status=202)


@api_view(["GET"])
def coletas_da_captura(request, pk):
    captura = get_object_or_404(Captura, pk=pk)
    return Response([{**_coleta(c), "erros_detalhe": c.erros[:20]} for c in captura.coletas.all()[:20]])


@api_view(["POST"])
def cotacao(request):
    try:
        idades = [int(i) for i in request.data.get("idades", []) if str(i).strip() != ""]
    except ValueError:
        return Response({"erro": "idades inválidas"}, status=400)
    if not idades or any(i < 0 or i > 120 for i in idades):
        return Response({"erro": "informe as idades dos beneficiários"}, status=400)
    uf = str(request.data.get("uf") or "").upper()
    if uf and (len(uf) != 2 or not uf.isalpha()):
        return Response({"erro": "UF inválida"}, status=400)
    return Response(servicos.cotar(idades, request.data.get("tipo", ""), uf))
