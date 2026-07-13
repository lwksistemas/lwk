"""Migration para criar tabelas de Estoque (ProdutoEstoque + MovimentacaoEstoque).
"""
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("clinica_beleza", "0016_alter_patient_options_alter_procedure_options_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="ProdutoEstoque",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("loja_id", models.IntegerField(db_index=True, default=0, verbose_name="ID da Loja")),
                ("nome", models.CharField(max_length=200, verbose_name="Nome do produto")),
                ("categoria", models.CharField(choices=[("injetavel", "Injetável"), ("soroterapia", "Soroterapia"), ("cosmético", "Cosmético"), ("descartavel", "Descartável"), ("equipamento", "Equipamento"), ("outro", "Outro")], default="outro", max_length=30, verbose_name="Categoria")),
                ("marca", models.CharField(blank=True, default="", max_length=100, verbose_name="Marca/Fabricante")),
                ("unidade_medida", models.CharField(default="unidade", help_text="Ex: unidade, ml, mg, ampola, frasco", max_length=30, verbose_name="Unidade de medida")),
                ("quantidade_atual", models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name="Quantidade atual")),
                ("quantidade_minima", models.DecimalField(decimal_places=2, default=0, help_text="Alerta quando atingir este valor", max_digits=10, verbose_name="Estoque mínimo")),
                ("preco_custo", models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name="Preço de custo (R$)")),
                ("preco_venda", models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name="Preço de venda (R$)")),
                ("validade", models.DateField(blank=True, null=True, verbose_name="Data de validade")),
                ("lote", models.CharField(blank=True, default="", max_length=50, verbose_name="Lote")),
                ("observacoes", models.TextField(blank=True, default="", verbose_name="Observações")),
                ("is_active", models.BooleanField(default=True, verbose_name="Ativo")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Criado em")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Atualizado em")),
            ],
            options={
                "verbose_name": "Produto do estoque",
                "verbose_name_plural": "Produtos do estoque",
                "ordering": ["nome"],
                "app_label": "clinica_beleza",
            },
        ),
        migrations.CreateModel(
            name="MovimentacaoEstoque",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("loja_id", models.IntegerField(db_index=True, default=0, verbose_name="ID da Loja")),
                ("tipo", models.CharField(choices=[("entrada", "Entrada"), ("saida", "Saída"), ("ajuste", "Ajuste de inventário")], max_length=10)),
                ("quantidade", models.DecimalField(decimal_places=2, max_digits=10, verbose_name="Quantidade")),
                ("motivo", models.CharField(blank=True, default="", max_length=200, verbose_name="Motivo/Observação")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Data da movimentação")),
                ("produto", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="movimentacoes", to="clinica_beleza.produtoestoque")),
                ("profissional", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="clinica_beleza.professional", verbose_name="Profissional responsável")),
                ("appointment", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="clinica_beleza.appointment", verbose_name="Agendamento vinculado")),
            ],
            options={
                "verbose_name": "Movimentação de estoque",
                "verbose_name_plural": "Movimentações de estoque",
                "ordering": ["-created_at"],
                "app_label": "clinica_beleza",
            },
        ),
    ]
