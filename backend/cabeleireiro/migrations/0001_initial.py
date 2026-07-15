import django.core.validators
import django.db.models.deletion
from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Cliente",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("loja_id", models.IntegerField(db_index=True, help_text="ID da loja proprietária deste registro")),
                ("nome", models.CharField(max_length=200, verbose_name="Nome")),
                ("email", models.EmailField(blank=True, max_length=254, null=True, verbose_name="E-mail")),
                ("telefone", models.CharField(max_length=20, verbose_name="Telefone")),
                ("cpf", models.CharField(blank=True, max_length=14, null=True, verbose_name="CPF")),
                ("data_nascimento", models.DateField(blank=True, null=True, verbose_name="Data de Nascimento")),
                ("endereco", models.TextField(blank=True, null=True, verbose_name="Endereço")),
                ("cidade", models.CharField(blank=True, max_length=100, null=True, verbose_name="Cidade")),
                ("estado", models.CharField(blank=True, max_length=2, null=True, verbose_name="Estado")),
                ("observacoes", models.TextField(blank=True, null=True, verbose_name="Observações")),
                ("is_active", models.BooleanField(default=True, verbose_name="Ativo")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Criado em")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Atualizado em")),
                ("allow_whatsapp", models.BooleanField(default=True, verbose_name="Permitir WhatsApp")),
                ("foto_url", models.URLField(blank=True, default="", max_length=500, verbose_name="Foto")),
                ("cep", models.CharField(blank=True, default="", max_length=10, verbose_name="CEP")),
                ("logradouro", models.CharField(blank=True, default="", max_length=200)),
                ("numero", models.CharField(blank=True, default="", max_length=20)),
                ("complemento", models.CharField(blank=True, default="", max_length=100)),
                ("bairro", models.CharField(blank=True, default="", max_length=100)),
            ],
            options={
                "verbose_name": "Cliente",
                "verbose_name_plural": "Clientes",
                "db_table": "cabeleireiro_cliente",
                "ordering": ["nome"],
            },
        ),
        migrations.CreateModel(
            name="Profissional",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("loja_id", models.IntegerField(db_index=True, help_text="ID da loja proprietária deste registro")),
                ("nome", models.CharField(max_length=200, verbose_name="Nome")),
                ("email", models.EmailField(blank=True, max_length=254, null=True, verbose_name="E-mail")),
                ("telefone", models.CharField(max_length=20, verbose_name="Telefone")),
                ("especialidade", models.CharField(blank=True, default="Cabeleireiro(a)", max_length=100, verbose_name="Especialidade")),
                ("registro_profissional", models.CharField(blank=True, help_text="CRM, COREN, etc", max_length=50, null=True, verbose_name="Registro Profissional")),
                ("comissao_percentual", models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=5, validators=[django.core.validators.MinValueValidator(Decimal("0.00"))], verbose_name="Comissão %")),
                ("is_active", models.BooleanField(default=True, verbose_name="Ativo")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Criado em")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Atualizado em")),
                ("cor_agenda", models.CharField(blank=True, default="#4A3042", max_length=7)),
            ],
            options={
                "verbose_name": "Profissional",
                "verbose_name_plural": "Profissionais",
                "db_table": "cabeleireiro_profissional",
                "ordering": ["nome"],
            },
        ),
        migrations.CreateModel(
            name="Servico",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("loja_id", models.IntegerField(db_index=True, help_text="ID da loja proprietária deste registro")),
                ("nome", models.CharField(max_length=200, verbose_name="Nome")),
                ("descricao", models.TextField(blank=True, null=True, verbose_name="Descrição")),
                ("duracao_minutos", models.IntegerField(verbose_name="Duração (minutos)")),
                ("preco", models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal("0.00"))], verbose_name="Preço")),
                ("categoria", models.CharField(blank=True, default="Geral", max_length=100, verbose_name="Categoria")),
                ("is_active", models.BooleanField(default=True, verbose_name="Ativo")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Criado em")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Atualizado em")),
            ],
            options={
                "verbose_name": "Serviço",
                "verbose_name_plural": "Serviços",
                "db_table": "cabeleireiro_servico",
                "ordering": ["categoria", "nome"],
            },
        ),
        migrations.CreateModel(
            name="Agendamento",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("loja_id", models.IntegerField(db_index=True, help_text="ID da loja proprietária deste registro")),
                ("data", models.DateField(verbose_name="Data")),
                ("hora_inicio", models.TimeField(verbose_name="Início")),
                ("hora_fim", models.TimeField(blank=True, null=True, verbose_name="Fim")),
                ("status", models.CharField(choices=[("SCHEDULED", "Agendado"), ("ARRIVED", "Chegou"), ("IN_PROGRESS", "Em atendimento"), ("DONE", "Concluído"), ("NO_SHOW", "Não compareceu"), ("CANCELLED", "Cancelado")], default="SCHEDULED", max_length=20)),
                ("valor", models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal("0.00"))])),
                ("observacoes", models.TextField(blank=True, default="")),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("cliente", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="agendamentos", to="cabeleireiro.cliente")),
                ("profissional", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="agendamentos", to="cabeleireiro.profissional")),
                ("servico", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="agendamentos", to="cabeleireiro.servico")),
            ],
            options={
                "db_table": "cabeleireiro_agendamento",
                "ordering": ["data", "hora_inicio"],
            },
        ),
        migrations.AddIndex(
            model_name="agendamento",
            index=models.Index(fields=["loja_id", "data", "status"], name="cabeleireir_loja_id_a8f1d0_idx"),
        ),
        migrations.AddIndex(
            model_name="agendamento",
            index=models.Index(fields=["loja_id", "profissional", "data"], name="cabeleireir_loja_id_b2e4c1_idx"),
        ),
    ]
