"""Pipeline: receber → ler duas vezes → conferir → revisar o apontado → publicar versão → gerar eventos."""
import functools
import hashlib
import logging
import re
import threading
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
from statistics import median

from django.conf import settings
from django.core.files.base import ContentFile
from django.db import connection, transaction
from django.utils import timezone

from leitor.ans import ARQUIVOS, IndiceANS, construir_indice
from leitor.condicoes import parear
from leitor import regras
from leitor.conferencia import SO_LLM, conferir
from leitor.faixas import FAIXAS, formatar_registro
from leitor.llm import ler_com_llm, tem_credencial, tem_gravacao
from leitor.pdf import TRAVA_PDFIUM
from leitor.rede import IndiceRede

from .models import CelulaLida, ColunaLida, Documento, Evento, Fonte, TabelaPublicada

log = logging.getLogger(__name__)
_indice: IndiceANS | None = None
_trava_indice = threading.Lock()


def indice() -> IndiceANS:
    global _indice
    with _trava_indice:
        if _indice is None:
            caminho = settings.DADOS_ANS / "indice.sqlite"
            if not caminho.exists():
                baixar_dados_ans()
                construir_indice(settings.DADOS_ANS, caminho)
            _indice = IndiceANS(caminho)
        return _indice


_rede: IndiceRede | None = None


def rede() -> IndiceRede | None:
    """Rede hospitalar e alterações de rede (comando baixar_rede_ans); a demonstração traz um recorte pronto."""
    global _rede
    if _rede is None:
        for caminho in (settings.DADOS_ANS / "rede.sqlite", settings.RAIZ / "amostras" / "ans" / "rede.sqlite"):
            if caminho.exists():
                _rede = IndiceRede(caminho)
                break
    return _rede


def atributos_ans(registro: str) -> dict | None:
    """O que o registro do produto na ANS diz sobre reembolso, coparticipação, acomodação e abrangência."""
    planos = indice().planos(registro) if registro else []
    if not planos:
        return None
    p = planos[0]
    return {"reembolso": p.livre_escolha, "coparticipacao": p.fator_moderador, "acomodacao": p.acomodacao,
            "abrangencia": p.abrangencia, "segmentacao": p.segmentacao, "situacao": p.situacao}


def baixar_dados_ans():
    import urllib.request

    settings.DADOS_ANS.mkdir(parents=True, exist_ok=True)
    for nome, url in ARQUIVOS.items():
        destino = settings.DADOS_ANS / nome
        if destino.exists():
            continue
        log.info("baixando %s", url)
        pedido = urllib.request.Request(url, headers={"User-Agent": "desafio-cotador/0.1"})
        with urllib.request.urlopen(pedido, timeout=600) as r, open(destino, "wb") as f:
            while bloco := r.read(1 << 20):
                f.write(bloco)


def serie_do_nome(nome: str) -> str:
    """'allcare_unimed_bh_adesao_mg_2026-09-08.pdf' → 'allcare_unimed_bh_adesao_mg' (tira data e prefixo wayback)."""
    base = re.sub(r"\.pdf$", "", nome, flags=re.I)
    base = re.sub(r"^wayback_", "", base)
    return re.sub(r"_\d{4}-\d{2}(-\d{2})?$", "", base)


def registrar(conteudo: bytes, nome: str, fonte: Fonte | None = None, url_origem: str = "", serie: str = "") -> tuple[Documento, bool]:
    sha = hashlib.sha256(conteudo).hexdigest()
    existente = Documento.objects.filter(sha256=sha).first()
    if existente:
        return existente, False
    doc = Documento(nome_original=nome, sha256=sha, fonte=fonte, url_origem=url_origem, serie=serie or serie_do_nome(nome))
    doc.arquivo.save(nome, ContentFile(conteudo), save=False)
    doc.save()
    return doc, True


def processar_em_segundo_plano(doc_id: int, llm: str = "auto"):
    def rodar():
        try:
            processar(doc_id, llm)
        finally:
            connection.close()

    threading.Thread(target=rodar, daemon=True).start()


def processar(doc_id: int, llm: str = "auto") -> Documento:
    """llm: 'auto' (ao vivo se houver chave, senão gravação, senão só geométrica), 'gravada', 'nao'.

    A leitura por LLM é a segunda opinião: se ela falhar (cota, rede, recusa), o documento segue
    com a leitura geométrica e a falha fica registrada nele.
    """
    doc = Documento.objects.get(pk=doc_id)
    doc.status, doc.erro = Documento.Status.PROCESSANDO, ""
    doc.save(update_fields=["status", "erro"])
    caminho = Path(doc.arquivo.path)
    try:
        leitura, custo, modo, falha = None, None, "nenhuma", ""
        if llm == "auto" and tem_credencial():
            try:
                r = ler_com_llm(caminho)
                leitura, custo, modo = r.leitura, r.custo, "ao_vivo"
            except Exception as e:
                log.warning("segunda leitura falhou em %s: %s", doc, e)
                falha = f"{type(e).__name__}: {e}"[:400]
        if leitura is None and llm in ("auto", "gravada") and tem_gravacao(caminho):
            r = ler_com_llm(caminho, replay=True)
            leitura, custo, modo = r.leitura, r.custo, "gravada"
        elif leitura is None and falha:
            modo = "falhou"
        conf = conferir(caminho, indice(), leitura, data_material=doc.data_versao)
        _salvar_conferencia(doc, conf, modo, custo, falha)
    except Exception as e:  # o documento fica marcado com o erro para alguém olhar
        log.exception("falha ao processar %s", doc)
        doc.status, doc.erro = Documento.Status.ERRO, f"{type(e).__name__}: {e}"
        doc.save(update_fields=["status", "erro"])
    return doc


def _posicao(col) -> tuple:
    caixa = next((c.caixa for c in col.celulas if c.caixa), None)
    return (col.pagina, 0, caixa[1], caixa[0]) if caixa else (col.pagina, 1, 0, 0)


@transaction.atomic
def _salvar_conferencia(doc: Documento, conf, modo: str, custo, falha_llm: str = ""):
    import pypdfium2 as pdfium

    doc.colunas.all().delete()
    doc.eventos.filter(resolvido=False).delete()
    colunas = sorted(conf.colunas, key=_posicao)
    # A ocorrência é a chave de comparação entre versões. Coluna lida só pelo LLM numera depois das
    # geométricas: se ela aparece numa versão e não na outra, não desloca a chave das colunas estáveis.
    ocorrencia_de, ocorrencias = {}, {}
    for col in sorted(colunas, key=lambda c: (all(x.geometrico is None for x in c.celulas), _posicao(c))):
        ocorrencia_de[id(col)] = ocorrencias.get(col.registro or "", 0)
        ocorrencias[col.registro or ""] = ocorrencia_de[id(col)] + 1
    pendentes: dict[tuple, list[dict]] = {}
    for ordem, col in enumerate(colunas):
        ocorrencia = ocorrencia_de[id(col)]
        coluna = ColunaLida.objects.create(
            documento=doc, ordem=ordem, pagina=col.pagina, tabela=col.tabela[:300], coluna=col.coluna[:200],
            ocorrencia=ocorrencia, marcas_condicao=col.condicao, registro_ans=col.registro or "",
            plano_ans=col.como_dict()["plano_ans"], achados=[a.como_dict() for a in col.achados],
        )
        CelulaLida.objects.bulk_create([
            CelulaLida(
                coluna=coluna, faixa=c.faixa,
                valor_geometrico=_dec(c.geometrico), valor_llm=_dec(c.llm), valor_final=_dec(c.valor), valor_calculado=_dec(c.calculado),
                status_leitura=c.status, caixa=c.caixa, revisar=c.revisar,
            )
            for c in col.celulas
        ])
        for tipo, severidade, mensagem in _achados_para_eventos(col):
            pendentes.setdefault((tipo, severidade), []).append({"registro": col.registro or "", "mensagem": mensagem, "pagina": col.pagina})
    for (tipo, severidade), itens in pendentes.items():
        _evento_agrupado(doc, tipo, severidade, itens)

    with TRAVA_PDFIUM:
        documento_pdf = pdfium.PdfDocument(doc.arquivo.path)
        doc.paginas = len(documento_pdf)
        documento_pdf.close()
    doc.ocr = conf.ocr
    doc.leitura_llm = modo
    doc.custo_llm_usd = Decimal(str(custo.usd)) if custo else None
    doc.resumo = conf.resumo()
    doc.achados_documento = [a.como_dict() for a in conf.achados_documento]
    if conf.leitura_llm:
        lt = conf.leitura_llm
        doc.operadora = lt.operadora or doc.operadora
        doc.administradora = lt.administradora or doc.administradora
        doc.tipo_contratacao = CONTRATACAO.get(lt.tipo_contratacao, lt.tipo_contratacao or doc.tipo_contratacao)
        doc.vigencia_inicio = _data(lt.vigencia_inicio) or doc.vigencia_inicio
        doc.vigencia_fim = _data(lt.vigencia_fim) or doc.vigencia_fim
        doc.extra_llm = {
            "produtos": [p.model_dump() for p in lt.produtos],
            "coparticipacao": [c.model_dump() for c in lt.coparticipacao],
            "carencias": [c.model_dump() for c in lt.carencias],
            "elegibilidade": lt.elegibilidade,
            "avisos": lt.avisos,
        }
    else:
        doc.extra_llm = {"falha": falha_llm} if falha_llm else {}
        doc.vigencia_inicio = doc.vigencia_inicio or conf.vigencia_impressa[0]
        doc.vigencia_fim = doc.vigencia_fim or conf.vigencia_impressa[1]
        if not doc.operadora:
            doc.operadora = _operadora_dominante(doc)
    doc.status = Documento.Status.EM_REVISAO
    doc.save()


CONTRATACAO = {"individual_familiar": "Individual ou familiar", "coletivo_empresarial": "Coletivo empresarial",
               "coletivo_adesao": "Coletivo por adesão", "nao_informado": ""}


def _operadora_dominante(doc: Documento) -> str:
    nomes = [c.plano_ans["operadora"] for c in doc.colunas.all() if c.plano_ans]
    return max(set(nomes), key=nomes.count) if nomes else ""


TITULOS_AGRUPADOS = {
    Evento.Tipo.REGISTRO_INVALIDO: "{n} registros ANS citados na tabela não existem no catálogo da ANS",
    Evento.Tipo.OPERADORA_CANCELADA: "{n} planos são de operadora cancelada na ANS",
    Evento.Tipo.PLANO_SUSPENSO: "{n} planos da tabela estão suspensos ou cancelados na ANS",
    Evento.Tipo.PRECO_FORA_DA_BANDA: "{n} planos com preço fora da referência da nota técnica da ANS",
}


def _achados_para_eventos(col) -> list[tuple[str, str, str]]:
    reg = formatar_registro(col.registro) if col.registro else ""
    eventos = []
    for a in col.achados:
        if a.regra == "Catálogo ANS" and "não existe" in a.mensagem:
            eventos.append((Evento.Tipo.REGISTRO_INVALIDO, "erro", f"Registro {reg} não existe no catálogo da ANS"))
        elif a.regra == "Cadastro de operadoras":
            eventos.append((Evento.Tipo.OPERADORA_CANCELADA, "erro", f"Plano {reg}: {a.mensagem}"))
        elif a.regra.startswith("RN 543") or (a.regra == "Catálogo ANS" and "desde" in a.mensagem):
            eventos.append((Evento.Tipo.PLANO_SUSPENSO, "alerta", f"Plano {reg}: {a.mensagem}"))
    fora = [a for a in col.achados if (a.regra.startswith("RN 564") or a.regra.startswith("Nota técnica")) and a.severidade != "info"]
    if fora:
        eventos.append((Evento.Tipo.PRECO_FORA_DA_BANDA, "alerta",
                        f"Plano {reg}: {fora[0].mensagem}" if len(fora) == 1 else f"Plano {reg}: {len(fora)} preços fora da referência da nota técnica"))
    return eventos


def _evento_agrupado(doc, tipo, severidade, itens: list[dict]):
    unicos = {i["mensagem"]: i for i in itens}
    itens = list(unicos.values())
    if len(itens) == 1:
        _evento(doc, tipo, severidade, itens[0]["mensagem"], itens[0]["registro"], {"pagina": itens[0]["pagina"]})
    else:
        _evento(doc, tipo, severidade, TITULOS_AGRUPADOS[tipo].format(n=len(itens)), "", {"itens": itens})


def _evento(doc, tipo, severidade, titulo, registro="", detalhe=None, data_efeito=None):
    return Evento.objects.create(
        tipo=tipo, severidade=severidade, titulo=titulo[:300], registro_ans=registro or "",
        operadora=doc.operadora if doc else "", documento=doc, detalhe=detalhe or {}, data_efeito=data_efeito,
    )


def _pct(x: float) -> str:
    return f"{x:+.1%}".replace(".", ",")


def _dec(v):
    return None if v is None else Decimal(str(round(v, 2)))


def _data(texto):
    try:
        return date.fromisoformat(texto) if texto else None
    except ValueError:
        return None


# ---------------------------------------------------------------- revisão

def corrigir_celula(celula: CelulaLida, valor: Decimal):
    celula.valor_final, celula.corrigida, celula.revisar = valor, True, False
    celula.save(update_fields=["valor_final", "corrigida", "revisar"])
    atualizar_resumo(celula.coluna.documento)


def aprovar_coluna(coluna: ColunaLida):
    coluna.celulas.filter(revisar=True).update(revisar=False)
    coluna.status = ColunaLida.Status.APROVADA
    coluna.save(update_fields=["status"])
    atualizar_resumo(coluna.documento)


def atualizar_resumo(doc: Documento):
    """O resumo gravado no processamento fica velho depois da revisão; recalcula o que muda."""
    celulas = CelulaLida.objects.filter(coluna__documento=doc)
    doc.resumo = {**doc.resumo, "revisar": celulas.filter(revisar=True).count(),
                  "corrigidas": celulas.filter(corrigida=True).count()}
    doc.save(update_fields=["resumo"])


def pode_publicar(coluna: ColunaLida) -> bool:
    return (bool(coluna.registro_ans) and coluna.status != ColunaLida.Status.IGNORADA
            and not coluna.celulas.filter(revisar=True).exists() and _faixas_completas(coluna))


def _faixas_completas(coluna: ColunaLida) -> bool:
    """Da primeira faixa vendida até 59+, sem buraco: preço avulso ('a partir de', adicional de odonto) não é tabela."""
    lidas = {c.faixa for c in coluna.celulas.all() if c.valor_final is not None}
    if not lidas:
        return False
    primeira = min(FAIXAS.index(f) for f in lidas)
    return all(f in lidas for f in FAIXAS[primeira:])


# ---------------------------------------------------------------- publicação

def versao_mais_nova(doc: Documento) -> Documento | None:
    """Material mais novo da mesma série já recebido. Se existe, este é uma versão antiga."""
    if not doc.data_versao:
        return None
    return (Documento.objects.filter(serie=doc.serie, fonte=doc.fonte, data_versao__gt=doc.data_versao).exclude(pk=doc.pk)
            .exclude(status__in=[Documento.Status.DESCARTADO, Documento.Status.ERRO]).order_by("-data_versao").first())


def guardar_se_antiga(doc_id: int) -> dict | None:
    """Versão antiga não muda o que o corretor vê; por isso entra no histórico sem esperar a revisão."""
    doc = Documento.objects.get(pk=doc_id)
    if doc.status == Documento.Status.EM_REVISAO and versao_mais_nova(doc):
        return publicar(doc)
    return None


def _precos(coluna: ColunaLida) -> dict:
    return {c.faixa: float(c.valor_final) for c in coluna.celulas.all() if c.valor_final is not None}


def _dados_da_tabela(doc: Documento, coluna: ColunaLida) -> dict:
    return dict(
        registro_ans=coluna.registro_ans, ocorrencia=coluna.ocorrencia, marcas_condicao=coluna.marcas_condicao, fonte=doc.fonte,
        condicao=coluna.tabela, nome_plano=(coluna.plano_ans or {}).get("nome", coluna.coluna),
        operadora=(coluna.plano_ans or {}).get("operadora", doc.operadora), administradora=doc.administradora,
        tipo_contratacao=(coluna.plano_ans or {}).get("contratacao", doc.tipo_contratacao), documento=doc, coluna=coluna,
        precos=_precos(coluna), vigencia_inicio=doc.vigencia_inicio, vigencia_fim=doc.vigencia_fim,
    )


@transaction.atomic
def publicar(doc: Documento) -> dict:
    if mais_nova := versao_mais_nova(doc):
        return _publicar_no_historico(doc, mais_nova)
    agora = timezone.now()
    publicadas, iguais, bloqueadas = 0, 0, 0
    mudancas, divergencias = [], []
    colunas = list(doc.colunas.prefetch_related("celulas"))
    # Cada coluna casa com a versão vigente do mesmo registro na mesma condição de venda, não pela posição,
    # que muda quando a operadora reorganiza o material. Coluna presente mas bloqueada também casa: o produto
    # não "saiu da tabela", e a versão anterior vale até a nova ser aprovada.
    da_serie = TabelaPublicada.objects.filter(documento__serie=doc.serie, fonte=doc.fonte).order_by("ocorrencia", "id")
    vigentes = list(da_serie.filter(ativa=True))
    # Sem versão vigente, o produto pode ter histórico (versões antigas coletadas, produto que saiu e voltou):
    # a versão nova continua essa história em vez de começar outra.
    encerradas = list(da_serie.filter(ativa=False, substituida_por=None).exclude(documento=doc))
    presentes = [c for c in colunas if c.registro_ans and c.status != ColunaLida.Status.IGNORADA]
    anterior_de, vistas = {}, set()
    for registro in {c.registro_ans for c in presentes}:
        antigas = [t for t in vigentes if t.registro_ans == registro]
        novas = sorted((c for c in presentes if c.registro_ans == registro), key=lambda c: c.ocorrencia)
        sem_vigente = []
        for antiga, nova_coluna in parear(antigas, novas, lambda x: x.marcas_condicao):
            if antiga and nova_coluna:
                anterior_de[nova_coluna.id] = antiga
                vistas.add(antiga.id)
            elif nova_coluna:
                sem_vigente.append(nova_coluna)
        for antiga, nova_coluna in parear([t for t in encerradas if t.registro_ans == registro], sem_vigente, lambda x: x.marcas_condicao):
            if antiga and nova_coluna:
                anterior_de[nova_coluna.id] = antiga
    for coluna in colunas:
        if not pode_publicar(coluna):
            bloqueadas += 1
            continue
        dados = _dados_da_tabela(doc, coluna)
        atual = anterior_de.get(coluna.id)
        if atual and atual.ativa and atual.precos == dados["precos"]:
            atual.confirmada_em = agora
            atual.save(update_fields=["confirmada_em"])
            iguais += 1
            continue
        nova = TabelaPublicada.objects.create(**dados, versao=(atual.versao + 1) if atual else 1, confirmada_em=agora)
        publicadas += 1
        if atual:
            atual.ativa, atual.substituida_por = False, nova
            atual.save(update_fields=["ativa", "substituida_por"])
            if _variacoes(atual.precos, nova.precos):
                mudancas.append(_mudanca(atual, nova))
        divergencias += _conferir_outras_fontes(nova)

    _eventos_de_publicacao(doc, mudancas, divergencias)
    removidas = _retirar_ausentes(doc, vistas, {c.registro_ans for c in presentes})
    if publicadas and not removidas and not TabelaPublicada.objects.filter(documento__serie=doc.serie).exclude(documento=doc).exists():
        _evento(doc, Evento.Tipo.TABELA_NOVA, "info", f"Tabela nova: {doc.nome_original} ({publicadas} preços por produto publicados)")
    doc.status = Documento.Status.PUBLICADO
    doc.save(update_fields=["status"])
    return {"publicadas": publicadas, "sem_mudanca": iguais, "bloqueadas": bloqueadas, "retiradas": removidas}


def _variacoes(antes: dict, depois: dict) -> dict:
    return {f: (antes[f], depois[f]) for f in FAIXAS if f in antes and f in depois and abs(antes[f] - depois[f]) >= 0.005}


def _mudanca(atual: TabelaPublicada, nova: TabelaPublicada) -> dict:
    variacoes = _variacoes(atual.precos, nova.precos)
    pct = median(d / a - 1 for a, d in variacoes.values() if a) if variacoes else 0
    return {"registro": nova.registro_ans, "plano": nova.nome_plano, "variacao_mediana": pct,
            "versoes": [atual.versao, nova.versao], "faixas": variacoes}


def _conferir_outras_fontes(nova: TabelaPublicada) -> list[dict]:
    """Mesmo produto publicado por outra fonte com preço diferente: um dos dois está desatualizado."""
    achados = []
    candidatas = TabelaPublicada.objects.filter(registro_ans=nova.registro_ans, ativa=True).exclude(fonte=nova.fonte).select_related("fonte", "documento")
    for outra in _mesma_condicao(nova, candidatas):
        variacoes = _variacoes(outra.precos, nova.precos)
        if variacoes:
            achados.append({"registro": nova.registro_ans, "plano": nova.nome_plano, "outra_fonte": str(outra.fonte),
                            "outro_documento": outra.documento.nome_original,
                            "variacao_mediana": median(d / a - 1 for a, d in variacoes.values() if a)})
    return achados


def _mesma_condicao(t: TabelaPublicada, candidatas) -> list[TabelaPublicada]:
    """Em cada outro material, a tabela do mesmo registro na condição de venda equivalente, se houver."""
    grupos: dict[tuple, list[TabelaPublicada]] = {}
    for c in candidatas:
        if c.id != t.id and (c.fonte_id, c.documento.serie) != (t.fonte_id, t.documento.serie):
            grupos.setdefault((c.fonte_id, c.documento.serie), []).append(c)
    escolhidas = []
    for grupo in grupos.values():
        grupo.sort(key=lambda c: abs(c.ocorrencia - t.ocorrencia))
        escolhidas += [b for a, b in parear([t], grupo, lambda x: x.marcas_condicao) if a is t and b is not None]
    return escolhidas


def _eventos_de_publicacao(doc, mudancas: list[dict], divergencias: list[dict]):
    if mudancas:
        pct = median(m["variacao_mediana"] for m in mudancas)
        titulo = (f"{mudancas[0]['plano'] or formatar_registro(mudancas[0]['registro'])}: preço {_pct(pct)} em relação à versão anterior"
                  if len(mudancas) == 1 else f"{len(mudancas)} produtos com preço alterado nesta versão de {_tabela_de(doc)} (mediana {_pct(pct)})")
        _evento(doc, Evento.Tipo.REAJUSTE, "info", titulo, mudancas[0]["registro"] if len(mudancas) == 1 else "",
                {"variacao_mediana": pct, "itens": mudancas}, data_efeito=doc.vigencia_inicio)
    por_fonte: dict[str, list[dict]] = {}
    for d in divergencias:
        por_fonte.setdefault(d["outra_fonte"], []).append(d)
    for outra_fonte, itens in por_fonte.items():
        pct = median(i["variacao_mediana"] for i in itens)
        mais_antiga = "a outra fonte parece estar com tabela antiga" if pct > 0 else "esta tabela parece mais antiga"
        _evento(doc, Evento.Tipo.FONTE_DIVERGENTE, "alerta",
                f"{len(itens)} produto(s) com preço diferente entre {doc.fonte} e {outra_fonte} ({_pct(pct)}): {mais_antiga}",
                itens[0]["registro"] if len(itens) == 1 else "",
                {"variacao_mediana": pct, "fonte_a": outra_fonte, "fonte_b": str(doc.fonte), "doc_a": itens[0]["outro_documento"],
                 "doc_b": doc.nome_original, "itens": itens})


def _tabela_de(doc: Documento) -> str:
    """Nome legível do material para os avisos: operadora, contratação e fonte, em vez do código da série."""
    partes = [doc.operadora or doc.serie, doc.tipo_contratacao.lower()]
    return ", ".join(p for p in partes if p) + (f" ({doc.fonte})" if doc.fonte else "")


def _retirar_ausentes(doc, vistas: set, presentes: set[str]) -> int:
    """Tabela vigente do mesmo material que não casou com nenhuma coluna desta versão.

    Se o registro sumiu do material, o produto saiu da tabela. Se o registro continua e só aquela condição
    sumiu (ex.: "titular" e "titular + 1" viraram uma tabela só), o que mudou foi a condição de venda.
    """
    retiradas, condicoes = [], []
    anteriores = TabelaPublicada.objects.filter(ativa=True, documento__serie=doc.serie, fonte=doc.fonte).exclude(documento=doc)
    for t in anteriores:
        if t.id in vistas:
            continue
        t.ativa = False
        t.save(update_fields=["ativa"])
        item = {"registro": t.registro_ans, "plano": t.nome_plano, "ultimo_documento": t.documento.nome_original}
        if t.registro_ans in presentes:
            condicoes.append({**item, "mensagem": f"condição encerrada: {' · '.join(t.marcas_condicao) or t.condicao}"})
        else:
            retiradas.append(item)
    if condicoes:
        _evento(doc, Evento.Tipo.CONDICAO_ALTERADA, "info",
                f"Condições de venda mudaram em {_tabela_de(doc)}: {len(condicoes)} tabelas encerradas, os produtos continuam", "",
                {"itens": condicoes})
    if retiradas:
        planos = {r["registro"] for r in retiradas}
        titulo = (f"{retiradas[0]['plano'] or formatar_registro(retiradas[0]['registro'])} saiu da tabela de {_tabela_de(doc)}"
                  if len(planos) == 1 else f"{len(planos)} produtos saíram da tabela de {_tabela_de(doc)}")
        _evento(doc, Evento.Tipo.PRODUTO_REMOVIDO, "alerta", titulo, retiradas[0]["registro"] if len(planos) == 1 else "", {"itens": retiradas})
    return len(retiradas) + len(condicoes)


@dataclass
class _Lugar:
    """Onde uma versão de certa data entra na história de um produto: entre `antes` e `depois`."""
    cadeia: list
    antes: TabelaPublicada | None
    depois: TabelaPublicada | None
    ja_tem: bool

    @property
    def marcas_condicao(self) -> list:
        return (self.depois or self.antes).marcas_condicao

    @property
    def ocorrencia(self) -> int:
        return (self.depois or self.antes).ocorrencia


def _data_da(t: TabelaPublicada) -> date:
    return t.documento.data_versao or timezone.localtime(t.publicada_em).date()


def _cadeias(tabelas: list[TabelaPublicada]) -> list[list[TabelaPublicada]]:
    """As versões de cada produto, da mais antiga à mais recente, seguindo substituida_por."""
    por_id = {t.id: t for t in tabelas}
    substituidas = {t.substituida_por_id for t in tabelas if t.substituida_por_id}
    cadeias = []
    for t in tabelas:
        if t.id in substituidas:
            continue
        cadeia = [t]
        while cadeia[-1].substituida_por_id in por_id and len(cadeia) <= len(tabelas):
            cadeia.append(por_id[cadeia[-1].substituida_por_id])
        cadeias.append(cadeia)
    return cadeias


def _lugar(cadeia: list[TabelaPublicada], doc: Documento) -> _Lugar:
    antes = None
    for t in cadeia:
        if _data_da(t) > doc.data_versao:
            break
        antes = t
    i = cadeia.index(antes) + 1 if antes else 0
    return _Lugar(cadeia, antes, cadeia[i] if i < len(cadeia) else None, any(t.documento_id == doc.id for t in cadeia))


@transaction.atomic
def _publicar_no_historico(doc: Documento, mais_nova: Documento) -> dict:
    """Versão mais antiga que outra já recebida da mesma série (cópia no arquivo da web, PDF antigo enviado).

    Cada tabela entra na história do produto, na posição da sua data, e nada do que está vigente muda: o
    material antigo nunca volta a ser o preço da cotação, em qualquer ordem que os documentos cheguem.
    """
    colunas = list(doc.colunas.prefetch_related("celulas"))
    ja_publicadas = set(TabelaPublicada.objects.filter(documento=doc).values_list("coluna_id", flat=True))
    pendentes = [c for c in colunas if c.registro_ans and c.status != ColunaLida.Status.IGNORADA and c.id not in ja_publicadas]
    publicaveis = [c for c in pendentes if pode_publicar(c)]
    cadeias = _cadeias(list(TabelaPublicada.objects.filter(documento__serie=doc.serie, fonte=doc.fonte).select_related("documento").order_by("id")))
    inseridas, iguais, adiadas, mudancas = 0, 0, 0, []
    for registro in sorted({c.registro_ans for c in publicaveis}):
        lugares = sorted((_lugar(c, doc) for c in cadeias if c[0].registro_ans == registro), key=lambda lugar: lugar.ocorrencia)
        novas = sorted((c for c in publicaveis if c.registro_ans == registro), key=lambda c: c.ocorrencia)
        for lugar, coluna in parear(lugares, novas, lambda x: x.marcas_condicao):
            if coluna is None:
                continue
            dados = _dados_da_tabela(doc, coluna)
            if lugar and lugar.ja_tem:
                iguais += 1
                continue
            if lugar and lugar.depois is None and lugar.antes.ativa:
                # A vigente é mais antiga que esta versão e há outra ainda mais nova a caminho: quem
                # substitui a vigente é a publicação da mais nova, com revisão.
                adiadas += 1
                continue
            if lugar and any(t is not None and t.precos == dados["precos"] for t in (lugar.antes, lugar.depois)):
                iguais += 1
                continue
            nova = TabelaPublicada.objects.create(**dados, ativa=False, substituida_por=lugar.depois if lugar else None, versao=1)
            inseridas += 1
            if lugar is None:
                continue
            if lugar.antes:
                lugar.antes.substituida_por = nova
                lugar.antes.save(update_fields=["substituida_por"])
            lugar.cadeia.insert(lugar.cadeia.index(lugar.depois) if lugar.depois else len(lugar.cadeia), nova)
            for versao, t in enumerate(lugar.cadeia, start=1):
                if t.versao != versao:
                    t.versao = versao
                    t.save(update_fields=["versao"])
            if lugar.depois and _variacoes(nova.precos, lugar.depois.precos):
                mudancas.append(_mudanca(nova, lugar.depois))
    if inseridas:
        titulo = f"{_tabela_de(doc)}: versão de {doc.data_versao:%d/%m/%Y} entrou no histórico ({inseridas} tabela(s))"
        if mudancas:
            pct = median(m["variacao_mediana"] for m in mudancas)
            titulo += f"; até a versão seguinte, preço {_pct(pct)} (mediana)"
        _evento(doc, Evento.Tipo.VERSAO_HISTORICA, "info", titulo, mudancas[0]["registro"] if len(mudancas) == 1 else "",
                {"itens": mudancas, "versao_mais_nova": mais_nova.nome_original}, data_efeito=doc.data_versao)
    # Os avisos da conferência (plano suspenso hoje, nota técnica de hoje) falam da cotação; versão antiga não vai para ela.
    doc.eventos.filter(tipo__in=list(TITULOS_AGRUPADOS), resolvido=False).delete()
    doc.status = Documento.Status.HISTORICO
    doc.save(update_fields=["status"])
    return {"publicadas": inseridas, "sem_mudanca": iguais, "bloqueadas": len(pendentes) - len(publicaveis), "retiradas": 0,
            "historico": True, "adiadas": adiadas, "versao_mais_nova": mais_nova.data_versao}


# ---------------------------------------------------------------- radar ANS

def sincronizar_com_ans() -> int:
    """Confere o que está publicado contra o cadastro atual da ANS e as vigências. Roda diariamente."""
    from .models import Operadora

    ix = indice()
    novos = 0
    for o in Operadora.objects.filter(no_cotador=True):
        dados = ix.operadora(o.registro_ans)
        if not dados:
            continue
        o.ativa = bool(dados["ativa"])
        o.cancelada_em = _data(dados["data_cancelamento"]) if dados["data_cancelamento"] else None
        o.motivo_cancelamento = dados["motivo_cancelamento"] or ""
        o.save()
        if not o.ativa and not Evento.objects.filter(tipo=Evento.Tipo.OPERADORA_CANCELADA, detalhe__registro_operadora=o.registro_ans).exists():
            Evento.objects.create(
                tipo=Evento.Tipo.OPERADORA_CANCELADA, severidade="erro",
                titulo=f"{o.nome} está na lista do Cotador, mas o registro na ANS foi cancelado em {o.cancelada_em:%d/%m/%Y} ({o.motivo_cancelamento})",
                operadora=o.nome, detalhe={"registro_operadora": o.registro_ans}, data_efeito=o.cancelada_em,
            )
            novos += 1
    for t in TabelaPublicada.objects.filter(ativa=True):
        planos = ix.planos(t.registro_ans)
        situacao = planos[0].situacao if planos else "inexistente"
        if situacao != "Ativo" and not Evento.objects.filter(tipo=Evento.Tipo.PLANO_SUSPENSO, registro_ans=t.registro_ans, resolvido=False).exists():
            Evento.objects.create(tipo=Evento.Tipo.PLANO_SUSPENSO, severidade="alerta", registro_ans=t.registro_ans,
                                  titulo=f"{t.nome_plano}: situação na ANS agora é '{situacao}'", operadora=t.operadora)
            novos += 1
    novos += sincronizar_rede()
    novos += sincronizar_notas_novas()
    hoje = timezone.localdate()
    for d in Documento.objects.filter(vigencia_fim__isnull=False, vigencia_fim__lte=hoje, status=Documento.Status.PUBLICADO):
        if not Evento.objects.filter(tipo=Evento.Tipo.VIGENCIA_VENCIDA, documento=d).exists():
            quando = "vence hoje" if d.vigencia_fim == hoje else f"venceu em {d.vigencia_fim:%d/%m/%Y}"
            _evento(d, Evento.Tipo.VIGENCIA_VENCIDA, "alerta", f"Tabela {d.nome_original} {quando}: pedir versão nova", data_efeito=d.vigencia_fim)
            novos += 1
    return novos


def sincronizar_notas_novas() -> int:
    """Tabela publicada cujo plano ganhou nota técnica nova na ANS depois do material: pedir a versão atual.

    É o sinal de que existe tabela nova mesmo sem acesso a ela; um aviso por documento e data de nota.
    """
    ix = indice()
    avisados = set(Evento.objects.filter(tipo=Evento.Tipo.NOTA_TECNICA_NOVA).values_list("detalhe__chave", flat=True))
    por_documento: dict[int, list[dict]] = {}
    for t in TabelaPublicada.objects.filter(ativa=True).select_related("documento"):
        data_material = t.documento.data_versao or t.documento.vigencia_inicio
        planos = ix.planos(t.registro_ans)
        if not data_material or not planos:
            continue
        ultima = ix.ultima_nota(planos[0].id_plano)
        if regras.nota_mais_nova(ultima, data_material):
            por_documento.setdefault(t.documento_id, []).append({"registro": t.registro_ans, "plano": t.nome_plano, "nota": ultima})
    novos = 0
    for doc_id, itens in por_documento.items():
        doc = Documento.objects.get(pk=doc_id)
        mais_recente = max(i["nota"] for i in itens)
        chave = f"{doc_id}:{mais_recente}"
        if chave in avisados:
            continue
        unicos = {i["registro"]: i for i in itens}
        quem = next(iter(unicos.values()))["plano"] if len(unicos) == 1 else f"{len(unicos)} planos"
        _evento(doc, Evento.Tipo.NOTA_TECNICA_NOVA, "alerta",
                f"{_tabela_de(doc)}: {quem} com nota técnica nova na ANS (até {date.fromisoformat(mais_recente):%d/%m/%Y}), "
                f"depois do material de {(doc.data_versao or doc.vigencia_inicio):%d/%m/%Y}: pedir a tabela atual à fonte",
                next(iter(unicos)) if len(unicos) == 1 else "", {"chave": chave, "itens": list(unicos.values())},
                data_efeito=date.fromisoformat(mais_recente))
        novos += 1
    return novos


JANELA_REDE = timedelta(days=90)
_MINUSCULAS = {"de", "da", "do", "das", "dos", "e", "em"}
_SIGLAS = {"SA", "S.A.", "S/A", "LTDA", "ME", "EIRELI", "UTI", "SUS"}


def _nome_proprio(texto: str) -> str:
    """'MATERNIDADE DE CAMPINAS' → 'Maternidade de Campinas'; siglas societárias continuam em maiúsculas."""
    palavras = texto.split()
    return " ".join(p if p in _SIGLAS else p.lower() if i and p.lower() in _MINUSCULAS else p.capitalize() for i, p in enumerate(palavras))


def mudancas_de_rede(registro: str, hoje: date | None = None, uf: str | None = None, so_futuras: bool = False) -> list[dict]:
    """Pedidos de mudança de rede do plano deferidos pela ANS, a valer em breve ou valendo há pouco, um por protocolo.

    Na cotação: com a UF do cliente, só as mudanças naquele estado; sem ela, só as que ainda vão valer. Plano
    nacional tem mudança de rede toda semana em algum lugar do país, e isso não interessa a quem cota em outro estado.
    """
    ix = rede()
    if ix is None:
        return []
    hoje = hoje or timezone.localdate()
    grupos: dict[str, dict] = {}
    for a in ix.alteracoes(registro):
        efeito = _data(a["alterada_em"])
        if not a["resultado"].lower().startswith("deferid") or not efeito or efeito < hoje - JANELA_REDE:
            continue
        if (uf and uf not in (a["excluido_uf"], a["incluido_uf"])) or (so_futuras and efeito < hoje):
            continue
        g = grupos.setdefault(a["protocolo"], {
            "protocolo": a["protocolo"], "tipo": a["tipo"], "motivo": a["motivo"], "plano": a["plano"], "solicitada_em": a["solicitada_em"],
            "vale_em": efeito, "excluidos": [], "incluidos": []})
        if a["excluido"]:
            item = f"{_nome_proprio(a['excluido'])} ({a['excluido_municipio']}/{a['excluido_uf']})"
            if item not in g["excluidos"]:
                g["excluidos"].append(item)
        if a["incluido"]:
            item = f"{_nome_proprio(a['incluido'])} ({a['incluido_municipio']}/{a['incluido_uf']})"
            if item not in g["incluidos"]:
                g["incluidos"].append(item)
    return sorted(grupos.values(), key=lambda g: g["vale_em"])


def sincronizar_rede() -> int:
    """Mudança de rede deferida pela ANS num plano publicado vira aviso no radar, um por protocolo.

    O material de venda não traz isso: é o registro oficial que diz que um hospital sai da rede, e quando.
    """
    if rede() is None:
        return 0
    hoje = timezone.localdate()
    planos: dict[str, list[TabelaPublicada]] = {}
    for t in TabelaPublicada.objects.filter(ativa=True):
        planos.setdefault(t.registro_ans, []).append(t)
    avisados = set(Evento.objects.filter(tipo=Evento.Tipo.REDE_ALTERADA).values_list("detalhe__protocolo", flat=True))
    por_protocolo: dict[str, dict] = {}
    for registro, tabelas in planos.items():
        for m in mudancas_de_rede(registro, hoje):
            if m["protocolo"] in avisados:
                continue
            g = por_protocolo.setdefault(m["protocolo"], {**m, "planos": []})
            g["planos"].append({"registro": registro, "nome": tabelas[0].nome_plano, "operadora": tabelas[0].operadora})
    for m in por_protocolo.values():
        quando = f"em {m['vale_em']:%d/%m/%Y}" if m["vale_em"] >= hoje else f"desde {m['vale_em']:%d/%m/%Y}"
        quem = m["planos"][0]["nome"] if len(m["planos"]) == 1 else f"{len(m['planos'])} planos publicados"
        sai = ", ".join(m["excluidos"][:2]) + (f" e mais {len(m['excluidos']) - 2}" if len(m["excluidos"]) > 2 else "")
        if m["incluidos"]:
            entra = ", ".join(m["incluidos"][:2]) + (f" e mais {len(m['incluidos']) - 2}" if len(m["incluidos"]) > 2 else "")
            titulo, severidade = f"{quem}: {sai} sai da rede {quando}, substituído por {entra} (deferido pela ANS)", "info"
        else:
            titulo, severidade = f"{quem}: {sai} sai da rede {quando}, sem substituto (redução deferida pela ANS)", "alerta"
        Evento.objects.create(
            tipo=Evento.Tipo.REDE_ALTERADA, severidade=severidade, titulo=titulo[:300],
            registro_ans=m["planos"][0]["registro"] if len(m["planos"]) == 1 else "", operadora=m["planos"][0]["operadora"],
            data_efeito=m["vale_em"], detalhe={**{k: v for k, v in m.items() if k != "vale_em"}, "vale_em": m["vale_em"].isoformat(),
                                                "fonte": "ANS: solicitações de alteração de rede hospitalar (dados abertos)"})
    return len(por_protocolo)


# ---------------------------------------------------------------- cotação

def idade_para_faixa(idade: int) -> str:
    limites = [18, 23, 28, 33, 38, 43, 48, 53, 58]
    for faixa, limite in zip(FAIXAS, limites):
        if idade <= limite:
            return faixa
    return "59+"


def cotar(idades: list[int], tipo: str = "", uf: str = "") -> list[dict]:
    faixas = [idade_para_faixa(i) for i in idades]
    resultado = []
    ix = rede()

    @functools.cache
    def do_registro(registro: str) -> dict:
        resumo = ix.resumo(registro) if ix else None
        return {"ans": atributos_ans(registro), "rede": resumo, "rede_na_uf": resumo["por_uf"].get(uf) if resumo and uf else None,
                "mudancas_de_rede": mudancas_de_rede(registro, uf=uf or None, so_futuras=not uf)}

    ativas = list(TabelaPublicada.objects.filter(ativa=True).select_related("documento", "fonte"))
    por_registro: dict[str, list[TabelaPublicada]] = {}
    for t in ativas:
        por_registro.setdefault(t.registro_ans, []).append(t)
    for t in ativas:
        if tipo and tipo.lower() not in (t.tipo_contratacao or "").lower():
            continue
        if any(f not in t.precos for f in faixas):
            continue
        total = sum(t.precos[f] for f in faixas)
        referencia = t.confirmada_em or t.publicada_em
        resultado.append({
            "tabela_id": t.id, "registro_ans": formatar_registro(t.registro_ans), "plano": t.nome_plano,
            "operadora": t.operadora, "fonte": str(t.fonte) if t.fonte else "", "condicao": t.condicao,
            "tipo_contratacao": t.tipo_contratacao, "total": round(total, 2),
            "por_pessoa": [{"idade": i, "faixa": f, "valor": t.precos[f]} for i, f in zip(idades, faixas)],
            "vigencia_inicio": t.vigencia_inicio, "vigencia_fim": t.vigencia_fim, "versao": t.versao,
            "documento": t.documento.nome_original, "documento_id": t.documento_id,
            "dias_desde_confirmacao": (timezone.now() - referencia).days,
            "dupla_leitura": t.documento.leitura_llm in ("ao_vivo", "gravada"),
            "data_material": t.documento.data_versao,
            "divergencias": _divergencias_na_cotacao(t, _mesma_condicao(t, por_registro[t.registro_ans]), faixas),
            **do_registro(t.registro_ans),
        })
    return sorted(resultado, key=lambda r: r["total"])


def _divergencias_na_cotacao(t: TabelaPublicada, mesmas: list[TabelaPublicada], faixas: list[str]) -> list[dict]:
    """O mesmo produto em outra fonte com preço diferente: avisa o corretor qual material é mais novo."""
    saida = []
    for outra in mesmas:
        if outra.id == t.id or any(f not in outra.precos for f in faixas):
            continue
        total_outra = sum(outra.precos[f] for f in faixas)
        total = sum(t.precos[f] for f in faixas)
        if abs(total_outra - total) < 0.01:
            continue
        mais_nova = (outra.documento.data_versao or date.min) > (t.documento.data_versao or date.min)
        saida.append({"fonte": str(outra.fonte), "total": round(total_outra, 2), "diferenca": total_outra / total - 1,
                      "data_material": outra.documento.data_versao, "outra_mais_recente": mais_nova})
    return saida
