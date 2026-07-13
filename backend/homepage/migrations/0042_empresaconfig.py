from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("homepage", "0041_funcionalidade_imagem_modulosistema_imagem"),
    ]

    operations = [
        migrations.CreateModel(
            name="EmpresaConfig",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nome_empresa", models.CharField(default="LWK Sistemas", max_length=200)),
                ("cnpj", models.CharField(blank=True, default="", help_text="CNPJ formatado (ex: 00.000.000/0001-00)", max_length=20)),
                ("endereco", models.CharField(blank=True, default="", help_text="Endereço completo", max_length=300)),
                ("telefone_whatsapp", models.CharField(blank=True, default="", help_text="Número WhatsApp com DDD (ex: 5511999999999)", max_length=20)),
                ("mensagem_whatsapp", models.CharField(blank=True, default="Olá! Gostaria de saber mais sobre o LWK Sistemas.", help_text="Mensagem padrão ao clicar no WhatsApp", max_length=300)),
                ("email_contato", models.EmailField(blank=True, default="", help_text="Email de contato da empresa", max_length=254)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Configuração da Empresa",
                "verbose_name_plural": "Configurações da Empresa",
                "db_table": "homepage_empresa_config",
            },
        ),
    ]
