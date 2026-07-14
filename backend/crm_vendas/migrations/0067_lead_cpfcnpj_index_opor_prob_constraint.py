"""Índice em Lead.cpf_cnpj + CheckConstraint em Oportunidade.probabilidade.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("crm_vendas", "0066_vendedor_config_acesso"),
    ]

    operations = [
        # Índice composto (loja_id, cpf_cnpj) para acelerar filtros de documento
        migrations.AddIndex(
            model_name="lead",
            index=models.Index(
                fields=["loja_id", "cpf_cnpj"],
                name="crm_lead_loja_cpfcnpj_idx",
            ),
        ),
        # Constraint de range em probabilidade (0-100)
        migrations.AddConstraint(
            model_name="oportunidade",
            constraint=models.CheckConstraint(
                condition=models.Q(probabilidade__gte=0) & models.Q(probabilidade__lte=100),
                name="crm_opor_prob_range",
            ),
        ),
    ]
