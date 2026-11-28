from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("clinica_beleza", "0113_resultado_exame_paciente"),
    ]

    operations = [
        migrations.AddField(
            model_name="appointment",
            name="origem",
            field=models.CharField(
                choices=[("interno", "Interno"), ("online", "Online")],
                db_index=True,
                default="interno",
                help_text="Interno (secretaria) ou Online (página pública).",
                max_length=20,
                verbose_name="Origem",
            ),
        ),
        migrations.CreateModel(
            name="AgendamentoOnlineConfig",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("loja_id", models.IntegerField(db_index=True, help_text="ID da loja proprietária deste registro")),
                ("ativo", models.BooleanField(default=False)),
                ("antecedencia_minima_horas", models.PositiveIntegerField(default=2, help_text="Horas mínimas entre agora e o início do horário.")),
                ("dias_futuros", models.PositiveIntegerField(default=30, help_text="Quantos dias à frente o cliente pode ver no calendário.")),
                ("permitir_mesmo_dia", models.BooleanField(default=True)),
                ("intervalo_slots_minutos", models.PositiveIntegerField(default=30)),
                ("modo_confirmacao", models.CharField(choices=[("automatico", "Confirmação automática"), ("secretaria", "Aprovação pela secretaria")], default="automatico", max_length=20)),
                ("permitir_cancelamento_cliente", models.BooleanField(default=True)),
                ("permitir_reagendamento_cliente", models.BooleanField(default=True)),
                ("prazo_cancelamento_horas", models.PositiveIntegerField(default=24, help_text="Horas mínimas antes do horário para cancelar/reagendar.")),
                ("reserva_pendente_minutos", models.PositiveIntegerField(default=120, help_text="Quanto tempo um pedido aguardando aprovação reserva o horário.")),
                ("enviar_confirmacao", models.BooleanField(default=True)),
                ("enviar_lembrete", models.BooleanField(default=True)),
                ("enviar_cancelamento", models.BooleanField(default=True)),
                ("enviar_reagendamento", models.BooleanField(default=True)),
                ("notificar_secretaria", models.BooleanField(default=True)),
                ("botao_whatsapp_ativo", models.BooleanField(default=True)),
                ("whatsapp_secretaria", models.CharField(blank=True, default="", help_text="Número específico da secretaria (opcional). Vazio = número da clínica.", max_length=20)),
                ("nome_publico", models.CharField(blank=True, default="", max_length=200)),
                ("texto_apresentacao", models.TextField(blank=True, default="")),
                ("logo_url", models.URLField(blank=True, default="", max_length=500)),
                ("banner_url", models.URLField(blank=True, default="", max_length=500)),
                ("cor_primaria", models.CharField(blank=True, default="", max_length=20)),
                ("cor_secundaria", models.CharField(blank=True, default="", max_length=20)),
                ("endereco_publico", models.CharField(blank=True, default="", max_length=300)),
                ("telefone_publico", models.CharField(blank=True, default="", max_length=30)),
                ("politica_privacidade", models.TextField(blank=True, default="")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Configuração do agendamento online",
                "db_table": "clinica_beleza_agendamento_online_config",
                "constraints": [
                    models.UniqueConstraint(fields=("loja_id",), name="uniq_agendamento_online_config_loja"),
                ],
            },
        ),
        migrations.CreateModel(
            name="AgendamentoOnlineProfissional",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("loja_id", models.IntegerField(db_index=True, help_text="ID da loja proprietária deste registro")),
                ("liberado", models.BooleanField(default=False)),
                ("bloqueado_temporariamente", models.BooleanField(default=False)),
                ("usar_horarios_exclusivos", models.BooleanField(default=False, help_text="Se falso, usa o horário de trabalho cadastrado (menos intervalo).")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("professional", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="agendamento_online", to="clinica_beleza.professional")),
            ],
            options={
                "verbose_name": "Profissional no agendamento online",
                "db_table": "clinica_beleza_agendamento_online_profissional",
            },
        ),
        migrations.CreateModel(
            name="AgendamentoOnlineHorario",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("loja_id", models.IntegerField(db_index=True, help_text="ID da loja proprietária deste registro")),
                ("dia_semana", models.PositiveSmallIntegerField(help_text="0=segunda … 6=domingo")),
                ("hora_inicio", models.TimeField()),
                ("hora_fim", models.TimeField()),
                ("ativo", models.BooleanField(default=True)),
                ("vinculo", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="horarios", to="clinica_beleza.agendamentoonlineprofissional")),
            ],
            options={
                "verbose_name": "Horário online do profissional",
                "db_table": "clinica_beleza_agendamento_online_horario",
                "ordering": ["dia_semana", "hora_inicio"],
            },
        ),
        migrations.CreateModel(
            name="AgendamentoOnlineProcedimento",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("loja_id", models.IntegerField(db_index=True, help_text="ID da loja proprietária deste registro")),
                ("liberado", models.BooleanField(default=True)),
                ("exibir_valor", models.BooleanField(default=True)),
                ("ordem", models.PositiveIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("procedure", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="agendamento_online", to="clinica_beleza.procedure")),
                ("profissionais", models.ManyToManyField(blank=True, help_text="Vazio = todos os profissionais liberados online.", related_name="procedimentos_online", to="clinica_beleza.professional")),
            ],
            options={
                "verbose_name": "Procedimento no agendamento online",
                "db_table": "clinica_beleza_agendamento_online_procedimento",
                "ordering": ["ordem", "id"],
            },
        ),
    ]
