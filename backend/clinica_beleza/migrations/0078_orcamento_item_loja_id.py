from django.db import migrations, models


def copiar_loja_id_dos_itens(apps, schema_editor):
    """Copia loja_id do orçamento pai. Não apaga nem recria item."""
    OrcamentoItem = apps.get_model("clinica_beleza", "OrcamentoItem")
    OrcamentoConsulta = apps.get_model("clinica_beleza", "OrcamentoConsulta")
    item_table = OrcamentoItem._meta.db_table
    orc_table = OrcamentoConsulta._meta.db_table
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            f"""
            UPDATE {item_table} AS i
            SET loja_id = o.loja_id
            FROM {orc_table} AS o
            WHERE i.orcamento_id = o.id
              AND i.loja_id IS NULL
            """,
        )


class Migration(migrations.Migration):

    dependencies = [
        ("clinica_beleza", "0077_orcamento_consulta"),
    ]

    operations = [
        migrations.AddField(
            model_name="orcamentoitem",
            name="loja_id",
            field=models.IntegerField(
                db_index=True,
                help_text="ID da loja proprietária deste registro",
                null=True,
            ),
        ),
        migrations.RunPython(copiar_loja_id_dos_itens, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="orcamentoitem",
            name="loja_id",
            field=models.IntegerField(
                db_index=True,
                help_text="ID da loja proprietária deste registro",
            ),
        ),
    ]
