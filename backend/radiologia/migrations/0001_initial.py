# Generated manually for radiologia MVP

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="PacienteRadiologia",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("loja_id", models.IntegerField(db_index=True, help_text="ID da loja (tenant)")),
                ("nome", models.CharField(max_length=200)),
                ("cpf", models.CharField(blank=True, default="", max_length=14)),
                ("data_nascimento", models.DateField(blank=True, null=True)),
                ("sexo", models.CharField(blank=True, choices=[("M", "Masculino"), ("F", "Feminino"), ("O", "Outro")], default="", max_length=1)),
                ("telefone", models.CharField(blank=True, default="", max_length=20)),
                ("email", models.EmailField(blank=True, default="", max_length=254)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "radiologia_paciente",
                "ordering": ["nome"],
            },
        ),
        migrations.CreateModel(
            name="Equipamento",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("loja_id", models.IntegerField(db_index=True, help_text="ID da loja (tenant)")),
                ("nome", models.CharField(max_length=120)),
                ("ae_title", models.CharField(help_text="Calling AE Title do aparelho (ex: LWK_US_0001)", max_length=16)),
                ("modality", models.CharField(default="US", help_text="Código DICOM: US, CR, DX, MG, CT, MR…", max_length=8)),
                ("fabricante", models.CharField(blank=True, default="", max_length=80)),
                ("modelo", models.CharField(blank=True, default="", max_length=80)),
                ("station_name", models.CharField(blank=True, default="", max_length=64)),
                ("suporte_dicom_storage", models.BooleanField(default=True)),
                ("suporte_mwl", models.BooleanField(default=True)),
                ("suporte_sr", models.BooleanField(default=False)),
                ("cobranca_mensal", models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "radiologia_equipamento",
                "ordering": ["nome"],
            },
        ),
        migrations.CreateModel(
            name="Procedimento",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("loja_id", models.IntegerField(db_index=True, help_text="ID da loja (tenant)")),
                ("codigo", models.CharField(blank=True, default="", max_length=32)),
                ("nome", models.CharField(max_length=200)),
                ("modality", models.CharField(default="US", max_length=8)),
                ("descricao", models.TextField(blank=True, default="")),
                ("template_laudo", models.TextField(blank=True, default="", help_text="Texto-base do laudo (placeholders opcionais)")),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "radiologia_procedimento",
                "ordering": ["nome"],
            },
        ),
        migrations.CreateModel(
            name="PedidoExame",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("loja_id", models.IntegerField(db_index=True, help_text="ID da loja (tenant)")),
                ("medico_solicitante", models.CharField(blank=True, default="", max_length=200)),
                ("crm_solicitante", models.CharField(blank=True, default="", max_length=32)),
                ("indicacao_clinica", models.TextField(blank=True, default="")),
                ("agendado_para", models.DateTimeField()),
                ("status", models.CharField(choices=[("agendado", "Agendado"), ("na_worklist", "Na worklist"), ("em_aquisicao", "Em aquisição"), ("imagens_recebidas", "Imagens recebidas"), ("em_laudo", "Em laudo"), ("laudado", "Laudado"), ("entregue", "Entregue"), ("cancelado", "Cancelado"), ("orfao", "Estudo órfão")], db_index=True, default="agendado", max_length=32)),
                ("accession_number", models.CharField(blank=True, db_index=True, default="", max_length=64)),
                ("study_instance_uid", models.CharField(blank=True, db_index=True, default="", max_length=128)),
                ("orthanc_study_id", models.CharField(blank=True, default="", max_length=64)),
                ("mwl_synced_at", models.DateTimeField(blank=True, null=True)),
                ("observacoes", models.TextField(blank=True, default="")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("equipamento", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="pedidos", to="radiologia.equipamento")),
                ("paciente", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="pedidos", to="radiologia.pacienteradiologia")),
                ("procedimento", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="pedidos", to="radiologia.procedimento")),
            ],
            options={
                "db_table": "radiologia_pedido_exame",
                "ordering": ["-agendado_para", "-id"],
            },
        ),
        migrations.CreateModel(
            name="Laudo",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("loja_id", models.IntegerField(db_index=True, help_text="ID da loja (tenant)")),
                ("medico_laudador", models.CharField(blank=True, default="", max_length=200)),
                ("crm_laudador", models.CharField(blank=True, default="", max_length=32)),
                ("texto", models.TextField(blank=True, default="")),
                ("conclusao", models.TextField(blank=True, default="")),
                ("bi_rads", models.CharField(blank=True, default="", help_text="Categoria BI-RADS (mamografia)", max_length=8)),
                ("status", models.CharField(choices=[("rascunho", "Rascunho"), ("finalizado", "Finalizado"), ("assinado", "Assinado"), ("entregue", "Entregue")], default="rascunho", max_length=20)),
                ("pdf_url", models.TextField(blank=True, default="")),
                ("assinado_em", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("pedido", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="laudo", to="radiologia.pedidoexame")),
            ],
            options={
                "db_table": "radiologia_laudo",
                "ordering": ["-updated_at"],
            },
        ),
        migrations.CreateModel(
            name="AuditoriaAcessoEstudo",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("loja_id", models.IntegerField(db_index=True, help_text="ID da loja (tenant)")),
                ("study_instance_uid", models.CharField(blank=True, default="", max_length=128)),
                ("usuario_id", models.IntegerField(blank=True, null=True)),
                ("usuario_nome", models.CharField(blank=True, default="", max_length=200)),
                ("acao", models.CharField(default="visualizar", max_length=64)),
                ("ip", models.GenericIPAddressField(blank=True, null=True)),
                ("detalhe", models.TextField(blank=True, default="")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("pedido", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="acessos", to="radiologia.pedidoexame")),
            ],
            options={
                "db_table": "radiologia_auditoria_acesso",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="pacienteradiologia",
            index=models.Index(fields=["loja_id", "cpf"], name="rad_pac_loja_cpf_idx"),
        ),
        migrations.AddIndex(
            model_name="pacienteradiologia",
            index=models.Index(fields=["loja_id", "is_active"], name="rad_pac_loja_ativo_idx"),
        ),
        migrations.AddConstraint(
            model_name="equipamento",
            constraint=models.UniqueConstraint(fields=("loja_id", "ae_title"), name="rad_equip_loja_aet_uniq"),
        ),
        migrations.AddIndex(
            model_name="pedidoexame",
            index=models.Index(fields=["loja_id", "status"], name="rad_ped_loja_status_idx"),
        ),
        migrations.AddIndex(
            model_name="pedidoexame",
            index=models.Index(fields=["loja_id", "accession_number"], name="rad_ped_loja_acc_idx"),
        ),
        migrations.AddIndex(
            model_name="auditoriaacessoestudo",
            index=models.Index(fields=["loja_id", "created_at"], name="rad_aud_loja_dt_idx"),
        ),
    ]
