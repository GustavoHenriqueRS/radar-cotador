from django.contrib import admin
from django.urls import path, re_path
from django.views.generic import TemplateView
from django.conf import settings

from radar import api

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/painel", api.painel),
    path("api/documentos", api.documentos),
    path("api/documentos/<int:pk>", api.documento),
    path("api/documentos/<int:pk>/pagina/<int:numero>.png", api.pagina),
    path("api/documentos/<int:pk>/pdf", api.pdf),
    path("api/documentos/<int:pk>/reprocessar", api.reprocessar),
    path("api/documentos/<int:pk>/publicar", api.publicar),
    path("api/colunas/<int:pk>/aprovar", api.aprovar_coluna),
    path("api/colunas/<int:pk>/ignorar", api.ignorar_coluna),
    path("api/celulas/<int:pk>", api.corrigir_celula),
    path("api/tabelas", api.tabelas),
    path("api/tabelas/historico/<str:registro>", api.historico),
    path("api/tabelas/<int:pk>/rede", api.rede_da_tabela),
    path("api/eventos", api.eventos),
    path("api/operadoras", api.operadoras),
    path("api/fontes", api.fontes),
    path("api/capturas/<int:pk>/coletar", api.coletar_captura),
    path("api/capturas/<int:pk>/coletas", api.coletas_da_captura),
    path("api/cotacao", api.cotacao),
]

# Rotas do React (SPA): qualquer caminho fora de /api e /admin devolve o index.html do build.
if settings.WHITENOISE_ROOT:
    urlpatterns.append(re_path(r"^(?!api/|admin/|static/|assets/).*$", TemplateView.as_view(template_name="index.html")))
