"""
Adiciona campo 'tipo' à Conta (cliente, prestadora, ambos)
e campo 'empresa_prestadora' à Oportunidade.
"""
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('crm_vendas', '0051_alter_proposta_status'),
    ]

    operations = [
        # 1. Adicionar campo tipo à Conta (default='cliente' para registros existentes)
        migrations.AddField(
            model_name='conta',
            name='tipo',
            field=models.CharField(
                choices=[
                    ('cliente', 'Cliente'),
                    ('prestadora', 'Prestadora de Serviço'),
                    ('ambos', 'Cliente e Prestadora'),
                ],
                default='cliente',
                help_text='Tipo da empresa: cliente, prestadora de serviço ou ambos',
                max_length=20,
            ),
        ),
        # 2. Adicionar campo empresa_prestadora à Oportunidade
        migrations.AddField(
            model_name='oportunidade',
            name='empresa_prestadora',
            field=models.ForeignKey(
                blank=True,
                help_text='Empresa para a qual o serviço é prestado nesta oportunidade',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='oportunidades_prestadas',
                to='crm_vendas.conta',
            ),
        ),
        # 3. Index por tipo na Conta
        migrations.AddIndex(
            model_name='conta',
            index=models.Index(fields=['loja_id', 'tipo'], name='crm_conta_loja_tipo_idx'),
        ),
    ]
