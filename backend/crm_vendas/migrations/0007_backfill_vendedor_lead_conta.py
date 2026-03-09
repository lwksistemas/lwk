# Data migration: preenche vendedor_id em leads e contas antigos
# a partir das oportunidades vinculadas (para que apareçam para o vendedor)
from django.db import migrations


def backfill_lead_vendedor(apps, schema_editor):
    Lead = apps.get_model('crm_vendas', 'Lead')
    Oportunidade = apps.get_model('crm_vendas', 'Oportunidade')
    for lead in Lead.objects.filter(vendedor_id__isnull=True).iterator():
        opp = Oportunidade.objects.filter(lead=lead, vendedor_id__isnull=False).order_by('id').first()
        if opp:
            lead.vendedor_id = opp.vendedor_id
            lead.save(update_fields=['vendedor_id'])


def backfill_conta_vendedor(apps, schema_editor):
    Conta = apps.get_model('crm_vendas', 'Conta')
    Lead = apps.get_model('crm_vendas', 'Lead')
    for conta in Conta.objects.filter(vendedor_id__isnull=True).iterator():
        lead = Lead.objects.filter(conta=conta).exclude(vendedor_id__isnull=True).order_by('id').first()
        if lead:
            conta.vendedor_id = lead.vendedor_id
            conta.save(update_fields=['vendedor_id'])


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('crm_vendas', '0006_add_vendedor_to_lead_and_conta'),
    ]

    operations = [
        migrations.RunPython(backfill_lead_vendedor, noop),
        migrations.RunPython(backfill_conta_vendedor, noop),
    ]
