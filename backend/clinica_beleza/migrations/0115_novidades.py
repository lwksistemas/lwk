from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("clinica_beleza", "0114_agendamento_online"),
    ]

    operations = [
        migrations.CreateModel(
            name="NovidadeConfig",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("loja_id", models.IntegerField(db_index=True)),
                (
                    "ativo",
                    models.BooleanField(
                        default=True,
                        help_text="Exibir o carrossel de novidades na página pública.",
                    ),
                ),
                (
                    "intervalo_carrossel",
                    models.PositiveSmallIntegerField(
                        default=5,
                        help_text="Segundos entre os slides do carrossel (3 a 30).",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Configuração de novidades",
                "db_table": "clinica_beleza_novidade_config",
            },
        ),
        migrations.CreateModel(
            name="Novidade",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("loja_id", models.IntegerField(db_index=True)),
                ("titulo", models.CharField(max_length=200)),
                ("descricao", models.TextField(blank=True, default="")),
                ("imagem_url", models.URLField(blank=True, default="", max_length=500)),
                (
                    "selo",
                    models.CharField(
                        blank=True,
                        default="Novidades",
                        help_text="Etiqueta no canto do card, ex.: Novidades, Promoção.",
                        max_length=40,
                    ),
                ),
                (
                    "condicao_especial",
                    models.CharField(
                        blank=True,
                        default="",
                        help_text="Texto do destaque de preço/oferta.",
                        max_length=200,
                    ),
                ),
                ("preco_de", models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ("preco_por", models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ("botao_texto", models.CharField(blank=True, default="Agende agora", max_length=80)),
                (
                    "botao_url",
                    models.CharField(
                        blank=True,
                        default="",
                        help_text="Link do botão. Vazio = inicia o agendamento na mesma página.",
                        max_length=500,
                    ),
                ),
                (
                    "beneficios",
                    models.JSONField(
                        blank=True,
                        default=list,
                        help_text="Lista de textos curtos exibidos no slide.",
                    ),
                ),
                ("ordem", models.PositiveIntegerField(default=0)),
                ("ativo", models.BooleanField(default=True)),
                ("data_inicio", models.DateField(blank=True, null=True)),
                ("data_fim", models.DateField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Novidade",
                "verbose_name_plural": "Novidades",
                "db_table": "clinica_beleza_novidade",
                "ordering": ["ordem", "id"],
            },
        ),
        migrations.AddConstraint(
            model_name="novidadeconfig",
            constraint=models.UniqueConstraint(fields=("loja_id",), name="uniq_novidade_config_loja"),
        ),
    ]
