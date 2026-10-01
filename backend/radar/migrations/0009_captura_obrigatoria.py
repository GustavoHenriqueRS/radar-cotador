import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    """Separada da 0008: no PostgreSQL, alterar a tabela na mesma transação que atualizou as chaves falha."""

    dependencies = [
        ('radar', '0008_captura'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='itemcoletado',
            unique_together=set(),
        ),
        migrations.RemoveField(
            model_name='itemcoletado',
            name='fonte',
        ),
        migrations.RemoveField(
            model_name='coleta',
            name='fonte',
        ),
        migrations.AlterField(
            model_name='coleta',
            name='captura',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='coletas', to='radar.captura'),
        ),
        migrations.AlterField(
            model_name='itemcoletado',
            name='captura',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='itens', to='radar.captura'),
        ),
        migrations.AlterField(
            model_name='itemcoletado',
            name='url',
            field=models.CharField(help_text='Endereço do material; no e-mail, o endereço IMAP do anexo', max_length=1000),
        ),
        migrations.AlterUniqueTogether(
            name='itemcoletado',
            unique_together={('captura', 'url')},
        ),
        migrations.RemoveField(
            model_name='fonte',
            name='coleta',
        ),
        migrations.RemoveField(
            model_name='fonte',
            name='config_coleta',
        ),
        migrations.RemoveField(
            model_name='fonte',
            name='coleta_ativa',
        ),
        migrations.AlterField(
            model_name='documento',
            name='status',
            field=models.CharField(choices=[('processando', 'Processando'), ('em_revisao', 'Em revisão'), ('publicado', 'Publicado'), ('historico', 'No histórico'), ('descartado', 'Descartado'), ('erro', 'Erro')], default='processando', max_length=20),
        ),
        migrations.AlterField(
            model_name='evento',
            name='tipo',
            field=models.CharField(choices=[('tabela_nova', 'Tabela nova'), ('reajuste', 'Preço alterado'), ('produto_novo', 'Produto novo'), ('produto_removido', 'Produto saiu da tabela'), ('versao_coletada', 'Tabela coletada'), ('versao_historica', 'Versão antiga no histórico'), ('coleta_falhou', 'Coleta com problema'), ('condicao_alterada', 'Condição de venda mudou'), ('fonte_divergente', 'Fontes divergentes'), ('registro_invalido', 'Registro ANS inválido'), ('plano_suspenso', 'Plano suspenso ou cancelado na ANS'), ('operadora_cancelada', 'Operadora cancelada na ANS'), ('preco_fora_da_banda', 'Preço fora da banda da nota técnica'), ('vigencia_vencida', 'Vigência vencida')], max_length=30),
        ),
    ]
