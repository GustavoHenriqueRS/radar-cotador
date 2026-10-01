"""Modelo de dados do radar.

Fluxo: Documento (material recebido) → ColunaLida/CelulaLida (dupla leitura + regras) → revisão
humana só do que foi apontado → TabelaPublicada (versão com vigência e origem) → Evento (o que mudou).
Nada é sobrescrito: cada publicação é uma versão nova ligada ao documento de onde saiu.
Antes de tudo, a captura: cada fonte tem um ou mais fluxos de entrada (Captura: página pública, endereço
fixo, histórico no arquivo da web, caixa de e-mail); cada passagem por um deles é uma Coleta, que traz só
o material novo (ItemColetado).
"""
from django.db import models

from coletor import TIPOS

FAIXAS = ["00-18", "19-23", "24-28", "29-33", "34-38", "39-43", "44-48", "49-53", "54-58", "59+"]


class Operadora(models.Model):
    registro_ans = models.CharField(max_length=6, unique=True)
    nome = models.CharField(max_length=200)
    ativa = models.BooleanField(default=True)
    cancelada_em = models.DateField(null=True, blank=True)
    motivo_cancelamento = models.CharField(max_length=200, blank=True)
    no_cotador = models.BooleanField(default=False, help_text="Aparece na lista de operadoras do Cotador")
    canal = models.CharField(max_length=200, blank=True, help_text="Por onde o preço chega, segundo o mapeamento (fontes/operadoras)")
    relatorio = models.CharField(max_length=200, blank=True, help_text="Relatório do mapeamento no repositório")

    def __str__(self):
        return f"{self.nome} ({self.registro_ans})"


class Fonte(models.Model):
    class Tipo(models.TextChoices):
        DADOS_ANS = "dados_ans", "Dados abertos da ANS"
        SITE_OPERADORA = "site_operadora", "Site público da operadora"
        PDF_OPERADORA = "pdf_operadora", "Material da operadora"
        PDF_ADMINISTRADORA = "pdf_administradora", "Material de administradora"
        ENVIO_CORRETOR = "envio_corretor", "Enviado por corretor"
        PARCERIA = "parceria", "Integração com parceiro"

    nome = models.CharField(max_length=120, unique=True)
    tipo = models.CharField(max_length=30, choices=Tipo.choices)
    url = models.URLField(blank=True)
    confiabilidade = models.PositiveSmallIntegerField(default=3, help_text="1 (baixa) a 5 (fonte oficial)")
    observacoes = models.TextField(blank=True, help_text="robots.txt, termos de uso, contato")

    def __str__(self):
        return self.nome


class Captura(models.Model):
    """Um fluxo de entrada de material de uma fonte. A fonte é quem publica; a captura é por onde chega."""

    fonte = models.ForeignKey(Fonte, related_name="capturas", on_delete=models.CASCADE)
    tipo = models.CharField(max_length=30, choices=[(t, c.rotulo) for t, c in TIPOS.items()],
                            help_text="Cada tipo é uma classe do pacote coletor")
    nome = models.CharField(max_length=120, blank=True)
    config = models.JSONField(default=dict, blank=True, help_text="Endereço, filtros, onde está a data da versão... (ver o tipo de captura)")
    estado = models.JSONField(default=dict, blank=True, help_text="O que passa de uma coleta para a outra (ex.: o último e-mail lido)")
    ativa = models.BooleanField(default=False, help_text="Entra na coleta agendada")

    class Meta:
        ordering = ["fonte", "id"]

    def __str__(self):
        return f"{self.fonte} · {self.nome or self.get_tipo_display()}"


class Documento(models.Model):
    class Status(models.TextChoices):
        PROCESSANDO = "processando", "Processando"
        EM_REVISAO = "em_revisao", "Em revisão"
        PUBLICADO = "publicado", "Publicado"
        HISTORICO = "historico", "No histórico"
        DESCARTADO = "descartado", "Descartado"
        ERRO = "erro", "Erro"

    arquivo = models.FileField(upload_to="documentos/")
    nome_original = models.CharField(max_length=255)
    serie = models.CharField(max_length=200, blank=True, help_text="Mesmo material em versões diferentes (ex.: allcare_unimed_bh_adesao_mg)")
    sha256 = models.CharField(max_length=64, unique=True)
    fonte = models.ForeignKey(Fonte, null=True, blank=True, on_delete=models.SET_NULL)
    url_origem = models.URLField(blank=True, max_length=500)
    recebido_em = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PROCESSANDO)
    paginas = models.PositiveIntegerField(default=0)
    ocr = models.BooleanField(default=False)
    leitura_llm = models.CharField(max_length=20, default="nenhuma", help_text="nenhuma | ao_vivo | gravada | falhou")
    custo_llm_usd = models.DecimalField(max_digits=8, decimal_places=4, null=True, blank=True)
    operadora = models.CharField(max_length=200, blank=True)
    administradora = models.CharField(max_length=200, blank=True)
    tipo_contratacao = models.CharField(max_length=40, blank=True)
    data_versao = models.DateField(null=True, blank=True, help_text="Data desta versão do material (nome do arquivo, capa)")
    vigencia_inicio = models.DateField(null=True, blank=True)
    vigencia_fim = models.DateField(null=True, blank=True)
    resumo = models.JSONField(default=dict, blank=True)
    achados_documento = models.JSONField(default=list, blank=True)
    extra_llm = models.JSONField(default=dict, blank=True, help_text="coparticipação, carências, elegibilidade, avisos")
    erro = models.TextField(blank=True)

    class Meta:
        ordering = ["-recebido_em"]

    def __str__(self):
        return self.nome_original


class ColunaLida(models.Model):
    """Uma coluna de preços de uma tabela do documento: um produto numa condição (vidas, coparticipação...)."""

    class Status(models.TextChoices):
        PENDENTE = "pendente", "Pendente"
        APROVADA = "aprovada", "Aprovada"
        IGNORADA = "ignorada", "Ignorada"

    documento = models.ForeignKey(Documento, related_name="colunas", on_delete=models.CASCADE)
    ordem = models.PositiveIntegerField()
    pagina = models.PositiveIntegerField()
    tabela = models.CharField(max_length=300, blank=True)
    coluna = models.CharField(max_length=200, blank=True)
    ocorrencia = models.PositiveIntegerField(default=0, help_text="Ordem de aparição do registro no documento; desempata quando a condição não distingue")
    marcas_condicao = models.JSONField(default=list, blank=True, help_text="Condição de venda lida no título e no rótulo: vidas, coparticipação, composição...")
    registro_ans = models.CharField(max_length=9, blank=True)
    plano_ans = models.JSONField(null=True, blank=True)
    achados = models.JSONField(default=list, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDENTE)

    class Meta:
        ordering = ["documento", "ordem"]


class CelulaLida(models.Model):
    coluna = models.ForeignKey(ColunaLida, related_name="celulas", on_delete=models.CASCADE)
    faixa = models.CharField(max_length=5)
    valor_geometrico = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    valor_llm = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    valor_final = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    valor_calculado = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True,
                                          help_text="Recalculado pelo percentual de faixa das colunas com o mesmo padrão")
    status_leitura = models.CharField(max_length=20)
    caixa = models.JSONField(null=True, blank=True, help_text="[x0, topo, x1, base] em pontos do PDF")
    revisar = models.BooleanField(default=False)
    corrigida = models.BooleanField(default=False)

    class Meta:
        ordering = ["coluna", "faixa"]


class TabelaPublicada(models.Model):
    """Versão publicada do preço de um produto numa condição. Versões antigas ficam como histórico."""

    registro_ans = models.CharField(max_length=9, db_index=True)
    ocorrencia = models.PositiveIntegerField(default=0)
    condicao = models.CharField(max_length=300, blank=True)
    marcas_condicao = models.JSONField(default=list, blank=True)
    nome_plano = models.CharField(max_length=300, blank=True)
    operadora = models.CharField(max_length=200, blank=True)
    administradora = models.CharField(max_length=200, blank=True)
    tipo_contratacao = models.CharField(max_length=40, blank=True)
    fonte = models.ForeignKey(Fonte, null=True, blank=True, on_delete=models.SET_NULL)
    documento = models.ForeignKey(Documento, related_name="publicacoes", on_delete=models.PROTECT)
    coluna = models.OneToOneField(ColunaLida, null=True, on_delete=models.SET_NULL)
    precos = models.JSONField(help_text="faixa -> valor")
    vigencia_inicio = models.DateField(null=True, blank=True)
    vigencia_fim = models.DateField(null=True, blank=True)
    versao = models.PositiveIntegerField(default=1)
    publicada_em = models.DateTimeField(auto_now_add=True)
    confirmada_em = models.DateTimeField(null=True, blank=True, help_text="Última vez que um documento novo trouxe os mesmos preços")
    ativa = models.BooleanField(default=True)
    substituida_por = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL, related_name="+")

    class Meta:
        ordering = ["registro_ans", "ocorrencia", "-versao"]
        indexes = [models.Index(fields=["registro_ans", "ativa"])]


class Evento(models.Model):
    class Tipo(models.TextChoices):
        TABELA_NOVA = "tabela_nova", "Tabela nova"
        REAJUSTE = "reajuste", "Preço alterado"
        PRODUTO_NOVO = "produto_novo", "Produto novo"
        PRODUTO_REMOVIDO = "produto_removido", "Produto saiu da tabela"
        VERSAO_COLETADA = "versao_coletada", "Tabela coletada"
        VERSAO_HISTORICA = "versao_historica", "Versão antiga no histórico"
        COLETA_FALHOU = "coleta_falhou", "Coleta com problema"
        CONDICAO_ALTERADA = "condicao_alterada", "Condição de venda mudou"
        FONTE_DIVERGENTE = "fonte_divergente", "Fontes divergentes"
        REGISTRO_INVALIDO = "registro_invalido", "Registro ANS inválido"
        PLANO_SUSPENSO = "plano_suspenso", "Plano suspenso ou cancelado na ANS"
        OPERADORA_CANCELADA = "operadora_cancelada", "Operadora cancelada na ANS"
        REDE_ALTERADA = "rede_alterada", "Rede hospitalar alterada"
        PRECO_FORA_DA_BANDA = "preco_fora_da_banda", "Preço fora da banda da nota técnica"
        VIGENCIA_VENCIDA = "vigencia_vencida", "Vigência vencida"
        NOTA_TECNICA_NOVA = "nota_tecnica_nova", "Nota técnica nova na ANS"

    tipo = models.CharField(max_length=30, choices=Tipo.choices)
    severidade = models.CharField(max_length=10, default="info")
    titulo = models.CharField(max_length=300)
    detalhe = models.JSONField(default=dict, blank=True)
    registro_ans = models.CharField(max_length=9, blank=True)
    operadora = models.CharField(max_length=200, blank=True)
    documento = models.ForeignKey(Documento, null=True, blank=True, on_delete=models.SET_NULL, related_name="eventos")
    criado_em = models.DateTimeField(auto_now_add=True)
    data_efeito = models.DateField(null=True, blank=True)
    resolvido = models.BooleanField(default=False)

    class Meta:
        ordering = ["-criado_em"]


class Coleta(models.Model):
    """Uma passagem do coletor por uma captura: o que achou, o que era novo, o que foi bloqueado."""

    class Situacao(models.TextChoices):
        RODANDO = "rodando", "Rodando"
        OK = "ok", "Concluída"
        BLOQUEADA = "bloqueada", "Bloqueada pelo robots.txt"
        ERRO = "erro", "Com erro"

    captura = models.ForeignKey(Captura, related_name="coletas", on_delete=models.CASCADE)
    iniciada_em = models.DateTimeField(auto_now_add=True)
    terminada_em = models.DateTimeField(null=True, blank=True)
    situacao = models.CharField(max_length=20, choices=Situacao.choices, default=Situacao.RODANDO)
    encontrados = models.PositiveIntegerField(default=0)
    novos = models.PositiveIntegerField(default=0)
    conhecidos = models.PositiveIntegerField(default=0, help_text="Baixados, mas já estavam no acervo (mesmo hash)")
    sem_mudanca = models.PositiveIntegerField(default=0)
    bloqueados = models.PositiveIntegerField(default=0)
    erros = models.JSONField(default=list, blank=True)
    mensagem = models.CharField(max_length=300, blank=True)

    class Meta:
        ordering = ["-iniciada_em"]


class ItemColetado(models.Model):
    """Cada material que a captura encontrou, com o necessário para baixar de novo só quando mudar."""

    captura = models.ForeignKey(Captura, related_name="itens", on_delete=models.CASCADE)
    url = models.CharField(max_length=1000, help_text="Endereço do material; no e-mail, o endereço IMAP do anexo")
    chave_serie = models.CharField(max_length=500, blank=True)
    titulo = models.CharField(max_length=300, blank=True)
    etag = models.CharField(max_length=200, blank=True)
    modificado_em = models.CharField(max_length=100, blank=True)
    sha256 = models.CharField(max_length=64, blank=True)
    documento = models.ForeignKey(Documento, null=True, blank=True, on_delete=models.SET_NULL)
    situacao = models.CharField(max_length=60, blank=True)
    visto_primeiro_em = models.DateTimeField(auto_now_add=True)
    visto_por_ultimo_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = [("captura", "url")]
