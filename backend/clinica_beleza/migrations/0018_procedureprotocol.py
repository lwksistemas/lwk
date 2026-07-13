import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("clinica_beleza", "0017_produtoestoque_movimentacaoestoque"),
    ]

    operations = [
        migrations.CreateModel(
            name="ProcedureProtocol",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("loja_id", models.IntegerField(db_index=True, default=0, verbose_name="ID da Loja")),
                ("nome", models.CharField(max_length=200, verbose_name="Nome do protocolo")),
                ("descricao", models.TextField(blank=True, default="", verbose_name="Descrição")),
                ("preparacao", models.TextField(blank=True, default="", verbose_name="Preparação")),
                ("execucao", models.TextField(blank=True, default="", verbose_name="Execução")),
                ("pos_procedimento", models.TextField(blank=True, default="", verbose_name="Pós-procedimento")),
                ("tempo_estimado", models.PositiveIntegerField(default=30, verbose_name="Tempo estimado (min)")),
                ("materiais_necessarios", models.TextField(blank=True, default="", verbose_name="Materiais necessários")),
                ("contraindicacoes", models.TextField(blank=True, default="", verbose_name="Contraindicações")),
                ("cuidados_especiais", models.TextField(blank=True, default="", verbose_name="Cuidados especiais")),
                ("is_active", models.BooleanField(default=True, verbose_name="Ativo")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("procedure", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="protocolos", to="clinica_beleza.procedure", verbose_name="Procedimento")),
            ],
            options={
                "verbose_name": "Protocolo de procedimento",
                "verbose_name_plural": "Protocolos de procedimentos",
                "db_table": "clinica_beleza_protocolos",
                "ordering": ["procedure__nome", "nome"],
            },
        ),
    ]
