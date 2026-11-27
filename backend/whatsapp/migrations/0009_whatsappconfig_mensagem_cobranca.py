# Mensagem padrão de cobrança por loja (inadimplência).
# IF NOT EXISTS: ensure_whatsapp_evolution_fields pode ter criado a coluna antes.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("whatsapp", "0008_confirmacao_antecedencias"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddField(
                    model_name="whatsappconfig",
                    name="mensagem_cobranca",
                    field=models.TextField(
                        blank=True,
                        default="",
                        help_text=(
                            "Placeholders: {nome}, {valor}, {vencimento}, {dias_atraso}, {clinica}. "
                            "Deixe em branco para usar a mensagem padrão."
                        ),
                        verbose_name="Mensagem personalizada de cobrança",
                    ),
                ),
            ],
            database_operations=[
                migrations.RunSQL(
                    sql=(
                        "ALTER TABLE whatsapp_whatsappconfig "
                        "ADD COLUMN IF NOT EXISTS mensagem_cobranca "
                        "TEXT NOT NULL DEFAULT '';"
                    ),
                    reverse_sql=(
                        "ALTER TABLE whatsapp_whatsappconfig "
                        "DROP COLUMN IF EXISTS mensagem_cobranca;"
                    ),
                ),
            ],
        ),
    ]
