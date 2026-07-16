import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("cabeleireiro", "0006_payment"),
    ]

    operations = [
        migrations.AddField(
            model_name="profissionalcomissao",
            name="servico",
            field=models.ForeignKey(
                blank=True,
                help_text="Serviço específico da categoria. Vazio = regra legada só por categoria.",
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="comissoes",
                to="cabeleireiro.servico",
                verbose_name="Serviço",
            ),
        ),
        migrations.AlterModelOptions(
            name="profissionalcomissao",
            options={
                "ordering": ["profissional", "categoria", "servico"],
                "verbose_name": "Comissão do profissional",
                "verbose_name_plural": "Comissões dos profissionais",
            },
        ),
        migrations.AddIndex(
            model_name="profissionalcomissao",
            index=models.Index(fields=["profissional", "servico"], name="cab_com_prof_svc_idx"),
        ),
    ]
