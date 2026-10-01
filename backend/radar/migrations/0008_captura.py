import django.db.models.deletion
from django.db import migrations, models

ROTULOS = {"pagina_publica": "Página pública com links", "url_direta": "Endereço fixo do material"}


def para_capturas(apps, schema_editor):
    """O tipo e a configuração de coleta saem da fonte e viram a primeira captura dela."""
    Fonte, Captura = apps.get_model("radar", "Fonte"), apps.get_model("radar", "Captura")
    Coleta, ItemColetado = apps.get_model("radar", "Coleta"), apps.get_model("radar", "ItemColetado")
    for fonte in Fonte.objects.exclude(coleta="manual"):
        captura = Captura.objects.create(fonte=fonte, tipo=fonte.coleta, nome=ROTULOS.get(fonte.coleta, ""),
                                         config=fonte.config_coleta, ativa=fonte.coleta_ativa)
        Coleta.objects.filter(fonte=fonte).update(captura=captura)
        ItemColetado.objects.filter(fonte=fonte).update(captura=captura)
    Coleta.objects.filter(captura=None).delete()
    ItemColetado.objects.filter(captura=None).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('radar', '0007_coleta'),
    ]

    operations = [
        migrations.CreateModel(
            name='Captura',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipo', models.CharField(choices=[('pagina_publica', 'Página pública com links'), ('url_direta', 'Endereço fixo do material'), ('wayback', 'Histórico no arquivo da web'), ('caixa_email', 'Caixa de e-mail')], help_text='Cada tipo é uma classe do pacote coletor', max_length=30)),
                ('nome', models.CharField(blank=True, max_length=120)),
                ('config', models.JSONField(blank=True, default=dict, help_text='Endereço, filtros, onde está a data da versão... (ver o tipo de captura)')),
                ('estado', models.JSONField(blank=True, default=dict, help_text='O que passa de uma coleta para a outra (ex.: o último e-mail lido)')),
                ('ativa', models.BooleanField(default=False, help_text='Entra na coleta agendada')),
                ('fonte', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='capturas', to='radar.fonte')),
            ],
            options={
                'ordering': ['fonte', 'id'],
            },
        ),
        migrations.AddField(
            model_name='coleta',
            name='captura',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='coletas', to='radar.captura'),
        ),
        migrations.AddField(
            model_name='itemcoletado',
            name='captura',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='itens', to='radar.captura'),
        ),
        migrations.RunPython(para_capturas, migrations.RunPython.noop),
    ]
