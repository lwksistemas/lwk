from django.db import migrations, models


def copiar_logo_atual_do_recibo(apps, schema_editor):
    """O recibo deixa de acompanhar a tela de login, mas não fica sem imagem."""
    Loja = apps.get_model("superadmin", "Loja")
    for loja in Loja.objects.all().only("id", "logo", "login_logo", "recibo_logo"):
        if (loja.recibo_logo or "").strip():
            continue
        origem = (loja.logo or "").strip() or (loja.login_logo or "").strip()
        if not origem:
            continue
        loja.recibo_logo = origem
        loja.save(update_fields=["recibo_logo"])


class Migration(migrations.Migration):

    dependencies = [
        ("superadmin", "0076_loja_agenda_visual"),
    ]

    operations = [
        migrations.AddField(
            model_name="loja",
            name="recibo_logo",
            field=models.URLField(
                blank=True,
                default="",
                help_text="Logomarca usada só no recibo de pagamento. Não altera a tela de login.",
            ),
        ),
        migrations.AddField(
            model_name="loja",
            name="recibo_cor",
            field=models.CharField(
                blank=True,
                default="",
                help_text="Cor da faixa do recibo (#RRGGBB). Vazio usa a cor principal da clínica.",
                max_length=7,
            ),
        ),
        migrations.RunPython(copiar_logo_atual_do_recibo, migrations.RunPython.noop),
    ]
