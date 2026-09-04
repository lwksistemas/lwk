from datetime import time

from django.db import migrations, models


def _ativar_backup_todas_lojas(apps, schema_editor):
    Loja = apps.get_model("superadmin", "Loja")
    Config = apps.get_model("superadmin", "ConfiguracaoBackup")
    for loja in Loja.objects.all().only("id"):
        slot = int(loja.id or 0) % 20
        total_min = slot * 15
        horario = time(hour=total_min // 60, minute=total_min % 60)
        Config.objects.get_or_create(
            loja_id=loja.id,
            defaults={
                "backup_automatico_ativo": True,
                "frequencia": "diario",
                "horario_envio": horario,
                "manter_ultimos_n_backups": 5,
            },
        )
    Config.objects.filter(backup_automatico_ativo=False).update(backup_automatico_ativo=True)


def _noop(apps, schema_editor):
    return None


class Migration(migrations.Migration):
    dependencies = [
        ("superadmin", "0068_whatsapp_parceiro_documento"),
    ]

    operations = [
        migrations.AlterField(
            model_name="configuracaobackup",
            name="backup_automatico_ativo",
            field=models.BooleanField(
                default=True,
                help_text="Ativa ou desativa o backup automático por e-mail (padrão: ligado)",
            ),
        ),
        migrations.AlterField(
            model_name="configuracaobackup",
            name="incluir_imagens",
            field=models.BooleanField(
                default=False,
                help_text="Legado: o e-mail automático não compacta fotos (o cliente baixa por link).",
            ),
        ),
        migrations.RunPython(_ativar_backup_todas_lojas, _noop),
    ]
