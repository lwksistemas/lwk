from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("salao_cabeleireiro", "0008_nfe_entrada"),
    ]

    operations = [
        migrations.AddField(
            model_name="produto",
            name="fornecedor",
            field=models.CharField(blank=True, default="", max_length=100, verbose_name="Nome do fornecedor"),
        ),
        migrations.AlterField(
            model_name="produto",
            name="nome",
            field=models.CharField(max_length=200, verbose_name="Nome comercial"),
        ),
        migrations.AlterField(
            model_name="vendaitem",
            name="nome",
            field=models.CharField(max_length=200),
        ),
    ]
