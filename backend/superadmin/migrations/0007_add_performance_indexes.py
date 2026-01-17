# Generated migration for performance indexes

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('superadmin', '0006_add_senha_provisoria_usuario_sistema'),
    ]

    operations = [
        # TipoLoja indexes
        migrations.AddIndex(
            model_name='tipoloja',
            index=models.Index(fields=['slug'], name='tipo_loja_slug_idx'),
        ),
        migrations.AddIndex(
            model_name='tipoloja',
            index=models.Index(fields=['dashboard_template'], name='tipo_loja_template_idx'),
        ),
        
        # PlanoAssinatura indexes
        migrations.AddIndex(
            model_name='planoassinatura',
            index=models.Index(fields=['is_active', 'ordem'], name='plano_active_ordem_idx'),
        ),
        migrations.AddIndex(
            model_name='planoassinatura',
            index=models.Index(fields=['slug'], name='plano_slug_idx'),
        ),
        
        # Loja indexes
        migrations.AddIndex(
            model_name='loja',
            index=models.Index(fields=['is_active', '-created_at'], name='loja_active_created_idx'),
        ),
        migrations.AddIndex(
            model_name='loja',
            index=models.Index(fields=['tipo_loja', 'is_active'], name='loja_tipo_active_idx'),
        ),
        migrations.AddIndex(
            model_name='loja',
            index=models.Index(fields=['plano', 'is_active'], name='loja_plano_active_idx'),
        ),
        migrations.AddIndex(
            model_name='loja',
            index=models.Index(fields=['owner', 'is_active'], name='loja_owner_active_idx'),
        ),
        migrations.AddIndex(
            model_name='loja',
            index=models.Index(fields=['database_name'], name='loja_db_name_idx'),
        ),
        migrations.AddIndex(
            model_name='loja',
            index=models.Index(fields=['is_trial', 'trial_ends_at'], name='loja_trial_idx'),
        ),
        
        # FinanceiroLoja indexes
        migrations.AddIndex(
            model_name='financeiroloja',
            index=models.Index(fields=['status_pagamento', 'data_proxima_cobranca'], name='fin_status_data_idx'),
        ),
        migrations.AddIndex(
            model_name='financeiroloja',
            index=models.Index(fields=['loja', 'status_pagamento'], name='fin_loja_status_idx'),
        ),
        
        # PagamentoLoja indexes
        migrations.AddIndex(
            model_name='pagamentoloja',
            index=models.Index(fields=['loja', 'status', '-data_vencimento'], name='pag_loja_status_idx'),
        ),
        migrations.AddIndex(
            model_name='pagamentoloja',
            index=models.Index(fields=['status', 'data_vencimento'], name='pag_status_venc_idx'),
        ),
        migrations.AddIndex(
            model_name='pagamentoloja',
            index=models.Index(fields=['financeiro', '-data_vencimento'], name='pag_fin_venc_idx'),
        ),
        
        # UsuarioSistema indexes
        migrations.AddIndex(
            model_name='usuariosistema',
            index=models.Index(fields=['tipo', 'is_active'], name='usuario_tipo_active_idx'),
        ),
        migrations.AddIndex(
            model_name='usuariosistema',
            index=models.Index(fields=['user', 'tipo'], name='usuario_user_tipo_idx'),
        ),
    ]
