from django.contrib import admin

from .models import Captura, CelulaLida, Coleta, ColunaLida, Documento, Evento, Fonte, ItemColetado, Operadora, TabelaPublicada


@admin.register(Documento)
class DocumentoAdmin(admin.ModelAdmin):
    list_display = ("nome_original", "fonte", "status", "leitura_llm", "ocr", "recebido_em")
    list_filter = ("status", "fonte", "leitura_llm")


@admin.register(TabelaPublicada)
class TabelaPublicadaAdmin(admin.ModelAdmin):
    list_display = ("registro_ans", "nome_plano", "fonte", "ocorrencia", "versao", "ativa", "vigencia_inicio")
    list_filter = ("ativa", "fonte")
    search_fields = ("registro_ans", "nome_plano", "operadora")


@admin.register(Evento)
class EventoAdmin(admin.ModelAdmin):
    list_display = ("tipo", "severidade", "titulo", "criado_em", "resolvido")
    list_filter = ("tipo", "severidade", "resolvido")


@admin.register(Captura)
class CapturaAdmin(admin.ModelAdmin):
    list_display = ("fonte", "nome", "tipo", "ativa")
    list_filter = ("tipo", "ativa")


@admin.register(Coleta)
class ColetaAdmin(admin.ModelAdmin):
    list_display = ("captura", "situacao", "iniciada_em", "encontrados", "novos", "conhecidos", "sem_mudanca", "bloqueados")
    list_filter = ("situacao",)


@admin.register(ItemColetado)
class ItemColetadoAdmin(admin.ModelAdmin):
    list_display = ("url", "captura", "situacao", "visto_por_ultimo_em")
    list_filter = ("situacao",)
    search_fields = ("url", "chave_serie")


admin.site.register([Fonte, Operadora, ColunaLida, CelulaLida])
