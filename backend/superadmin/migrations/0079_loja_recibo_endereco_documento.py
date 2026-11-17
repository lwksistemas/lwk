from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("superadmin", "0078_plano_tem_simulacao_estetica"),
    ]

    operations = [
        migrations.AddField(
            model_name="loja",
            name="recibo_endereco",
            field=models.CharField(
                blank=True,
                default="",
                help_text="Endereço impresso no recibo. Vazio usa o endereço do cadastro da loja.",
                max_length=300,
            ),
        ),
        migrations.AddField(
            model_name="loja",
            name="recibo_documento",
            field=models.CharField(
                blank=True,
                default="",
                help_text="CPF ou CNPJ impresso no recibo, só dígitos. Vazio usa o documento do cadastro.",
                max_length=18,
            ),
        ),
    ]
