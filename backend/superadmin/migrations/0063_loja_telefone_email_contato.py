from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("superadmin", "0062_configuracaobackup_horario_noturno"),
    ]

    operations = [
        migrations.AddField(
            model_name="loja",
            name="telefone_contato",
            field=models.CharField(
                blank=True,
                default="",
                help_text="Telefone da clínica/salão exibido no recibo de pagamento",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="loja",
            name="email_contato",
            field=models.EmailField(
                blank=True,
                default="",
                help_text="E-mail da clínica/salão exibido no recibo de pagamento",
                max_length=254,
            ),
        ),
    ]
