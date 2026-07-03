"""Campos de snapshot do emitente (Dados da Loja) em proposta e contrato."""
from django.db import migrations, models

_EMITENTE_FIELDS = [
    ('emitente_nome', models.CharField(blank=True, default='', help_text='Snapshot: nome do emitente (vazio = dados da loja)', max_length=255)),
    ('emitente_endereco', models.CharField(blank=True, default='', max_length=500)),
    ('emitente_cpf_cnpj', models.CharField(blank=True, default='', max_length=18)),
    ('emitente_responsavel', models.CharField(blank=True, default='', max_length=255)),
    ('emitente_email', models.EmailField(blank=True, default='')),
]


class Migration(migrations.Migration):

    dependencies = [
        ('crm_vendas', '0067_lead_cpfcnpj_index_opor_prob_constraint'),
    ]

    operations = [
        *[
            migrations.AddField(
                model_name='proposta',
                name=name,
                field=field,
            )
            for name, field in _EMITENTE_FIELDS
        ],
        *[
            migrations.AddField(
                model_name='contrato',
                name=name,
                field=field,
            )
            for name, field in _EMITENTE_FIELDS
        ],
    ]
