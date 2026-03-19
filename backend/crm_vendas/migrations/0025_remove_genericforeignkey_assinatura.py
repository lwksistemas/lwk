# Generated manually - Remove GenericForeignKey e adiciona ForeignKeys diretos

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('crm_vendas', '0024_add_assinatura_digital'),
    ]

    operations = [
        # Adicionar novos campos
        migrations.AddField(
            model_name='assinaturadigital',
            name='proposta',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='assinaturas',
                to='crm_vendas.proposta',
                help_text='Proposta sendo assinada'
            ),
        ),
        migrations.AddField(
            model_name='assinaturadigital',
            name='contrato',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='assinaturas',
                to='crm_vendas.contrato',
                help_text='Contrato sendo assinado'
            ),
        ),
        
        # Migrar dados existentes de content_type/object_id para proposta/contrato
        migrations.RunSQL(
            sql="""
                UPDATE crm_vendas_assinatura_digital
                SET proposta_id = object_id
                WHERE content_type_id = (
                    SELECT id FROM django_content_type 
                    WHERE app_label = 'crm_vendas' AND model = 'proposta'
                );
                
                UPDATE crm_vendas_assinatura_digital
                SET contrato_id = object_id
                WHERE content_type_id = (
                    SELECT id FROM django_content_type 
                    WHERE app_label = 'crm_vendas' AND model = 'contrato'
                );
            """,
            reverse_sql="""
                UPDATE crm_vendas_assinatura_digital
                SET object_id = proposta_id,
                    content_type_id = (
                        SELECT id FROM django_content_type 
                        WHERE app_label = 'crm_vendas' AND model = 'proposta'
                    )
                WHERE proposta_id IS NOT NULL;
                
                UPDATE crm_vendas_assinatura_digital
                SET object_id = contrato_id,
                    content_type_id = (
                        SELECT id FROM django_content_type 
                        WHERE app_label = 'crm_vendas' AND model = 'contrato'
                    )
                WHERE contrato_id IS NOT NULL;
            """
        ),
        
        # Remover campos antigos
        migrations.RemoveField(
            model_name='assinaturadigital',
            name='content_type',
        ),
        migrations.RemoveField(
            model_name='assinaturadigital',
            name='object_id',
        ),
        
        # Remover índice antigo e adicionar novos
        migrations.RemoveIndex(
            model_name='assinaturadigital',
            name='crm_assin_content_idx',
        ),
        migrations.AddIndex(
            model_name='assinaturadigital',
            index=models.Index(fields=['proposta'], name='crm_assin_proposta_idx'),
        ),
        migrations.AddIndex(
            model_name='assinaturadigital',
            index=models.Index(fields=['contrato'], name='crm_assin_contrato_idx'),
        ),
        
        # Adicionar constraint para garantir que apenas um dos campos está preenchido
        migrations.AddConstraint(
            model_name='assinaturadigital',
            constraint=models.CheckConstraint(
                check=(
                    models.Q(proposta__isnull=False, contrato__isnull=True) |
                    models.Q(proposta__isnull=True, contrato__isnull=False)
                ),
                name='crm_assin_proposta_ou_contrato'
            ),
        ),
    ]
