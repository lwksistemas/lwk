# Generated manually for performance optimization

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crm_vendas', '0007_backfill_vendedor_lead_conta'),
    ]

    operations = [
        # Vendedor indexes
        migrations.AddIndex(
            model_name='vendedor',
            index=models.Index(fields=['loja_id', 'is_active'], name='crm_vend_loja_active_idx'),
        ),
        migrations.AddIndex(
            model_name='vendedor',
            index=models.Index(fields=['loja_id', 'email'], name='crm_vend_loja_email_idx'),
        ),
        
        # Conta indexes
        migrations.AddIndex(
            model_name='conta',
            index=models.Index(fields=['loja_id', 'nome'], name='crm_conta_loja_nome_idx'),
        ),
        migrations.AddIndex(
            model_name='conta',
            index=models.Index(fields=['loja_id', 'vendedor_id'], name='crm_conta_loja_vend_idx'),
        ),
        migrations.AddIndex(
            model_name='conta',
            index=models.Index(fields=['loja_id', 'created_at'], name='crm_conta_loja_created_idx'),
        ),
        
        # Lead indexes
        migrations.AddIndex(
            model_name='lead',
            index=models.Index(fields=['loja_id', 'status'], name='crm_lead_loja_status_idx'),
        ),
        migrations.AddIndex(
            model_name='lead',
            index=models.Index(fields=['loja_id', 'origem'], name='crm_lead_loja_origem_idx'),
        ),
        migrations.AddIndex(
            model_name='lead',
            index=models.Index(fields=['loja_id', 'vendedor_id'], name='crm_lead_loja_vend_idx'),
        ),
        migrations.AddIndex(
            model_name='lead',
            index=models.Index(fields=['loja_id', 'created_at'], name='crm_lead_loja_created_idx'),
        ),
        migrations.AddIndex(
            model_name='lead',
            index=models.Index(fields=['loja_id', 'conta_id'], name='crm_lead_loja_conta_idx'),
        ),
        
        # Contato indexes
        migrations.AddIndex(
            model_name='contato',
            index=models.Index(fields=['loja_id', 'conta_id'], name='crm_contato_loja_conta_idx'),
        ),
        migrations.AddIndex(
            model_name='contato',
            index=models.Index(fields=['loja_id', 'email'], name='crm_contato_loja_email_idx'),
        ),
        
        # Oportunidade indexes
        migrations.AddIndex(
            model_name='oportunidade',
            index=models.Index(fields=['loja_id', 'etapa'], name='crm_opor_loja_etapa_idx'),
        ),
        migrations.AddIndex(
            model_name='oportunidade',
            index=models.Index(fields=['loja_id', 'vendedor_id'], name='crm_opor_loja_vend_idx'),
        ),
        migrations.AddIndex(
            model_name='oportunidade',
            index=models.Index(fields=['loja_id', 'lead_id'], name='crm_opor_loja_lead_idx'),
        ),
        migrations.AddIndex(
            model_name='oportunidade',
            index=models.Index(fields=['loja_id', 'data_fechamento'], name='crm_opor_loja_dtfech_idx'),
        ),
        migrations.AddIndex(
            model_name='oportunidade',
            index=models.Index(fields=['loja_id', 'etapa', 'vendedor_id'], name='crm_opor_loja_etapa_vend_idx'),
        ),
        migrations.AddIndex(
            model_name='oportunidade',
            index=models.Index(fields=['loja_id', 'created_at'], name='crm_opor_loja_created_idx'),
        ),
        
        # Atividade indexes
        migrations.AddIndex(
            model_name='atividade',
            index=models.Index(fields=['loja_id', 'data'], name='crm_ativ_loja_data_idx'),
        ),
        migrations.AddIndex(
            model_name='atividade',
            index=models.Index(fields=['loja_id', 'concluido'], name='crm_ativ_loja_concl_idx'),
        ),
        migrations.AddIndex(
            model_name='atividade',
            index=models.Index(fields=['loja_id', 'oportunidade_id'], name='crm_ativ_loja_opor_idx'),
        ),
        migrations.AddIndex(
            model_name='atividade',
            index=models.Index(fields=['loja_id', 'lead_id'], name='crm_ativ_loja_lead_idx'),
        ),
        migrations.AddIndex(
            model_name='atividade',
            index=models.Index(fields=['loja_id', 'data', 'concluido'], name='crm_ativ_loja_data_concl_idx'),
        ),
    ]
