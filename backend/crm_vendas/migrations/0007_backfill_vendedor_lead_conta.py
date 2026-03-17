# Data migration: preenche vendedor_id em leads e contas antigos
# Só executa em schemas onde as tabelas existem (tenants); no public faz no-op.
from django.db import migrations


def backfill_vendedor(apps, schema_editor):
    conn = schema_editor.connection
    if conn.vendor != 'postgresql':
        return
    db_alias = schema_editor.connection.alias
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = current_schema()
            AND table_name = 'crm_vendas_lead'
        """)
        if not cursor.fetchone():
            return  # Tabelas não existem neste schema (ex: public)
    Lead = apps.get_model('crm_vendas', 'Lead')
    Oportunidade = apps.get_model('crm_vendas', 'Oportunidade')
    Conta = apps.get_model('crm_vendas', 'Conta')
    # Usar .using(db_alias) para tenant schemas
    for lead in Lead.objects.using(db_alias).filter(vendedor_id__isnull=True).iterator():
        opp = Oportunidade.objects.using(db_alias).filter(lead=lead, vendedor_id__isnull=False).order_by('id').first()
        if opp:
            lead.vendedor_id = opp.vendedor_id
            lead.save(update_fields=['vendedor_id'], using=db_alias)
    for conta in Conta.objects.using(db_alias).filter(vendedor_id__isnull=True).iterator():
        lead = Lead.objects.using(db_alias).filter(conta=conta).exclude(vendedor_id__isnull=True).order_by('id').first()
        if lead:
            conta.vendedor_id = lead.vendedor_id
            conta.save(update_fields=['vendedor_id'], using=db_alias)


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('crm_vendas', '0006_add_vendedor_to_lead_and_conta'),
    ]

    operations = [
        migrations.RunPython(backfill_vendedor, noop),
    ]
