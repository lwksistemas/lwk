from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("superadmin", "0069_backup_automatico_padrao"),
    ]

    operations = [
        migrations.AddField(
            model_name="loja",
            name="colunas_pacientes",
            field=models.JSONField(
                blank=True,
                default=list,
                help_text="Colunas visíveis na listagem de Clientes (clínica). Vazio = padrão sem Ações.",
            ),
        ),
    ]
