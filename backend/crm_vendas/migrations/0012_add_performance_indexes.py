# Generated manually for performance optimization
# Compatible with django-tenants (tenant schemas)

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crm_vendas', '0007_backfill_vendedor_lead_conta'),
    ]

    operations = [
        # Vendedor indexes
        migrations.RunSQL(
            sql="""
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'crm_vend_loja_active_idx') THEN
                    CREATE INDEX CONCURRENTLY crm_vend_loja_active_idx ON crm_vendas_vendedor (loja_id, is_active);
                END IF;
                IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'crm_vend_loja_email_idx') THEN
                    CREATE INDEX CONCURRENTLY crm_vend_loja_email_idx ON crm_vendas_vendedor (loja_id, email);
                END IF;
            END $$;
            """,
            reverse_sql="""
            DROP INDEX IF EXISTS crm_vend_loja_active_idx;
            DROP INDEX IF EXISTS crm_vend_loja_email_idx;
            """,
        ),
        
        # Conta indexes
        migrations.RunSQL(
            sql="""
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'crm_conta_loja_nome_idx') THEN
                    CREATE INDEX CONCURRENTLY crm_conta_loja_nome_idx ON crm_vendas_conta (loja_id, nome);
                END IF;
                IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'crm_conta_loja_vend_idx') THEN
                    CREATE INDEX CONCURRENTLY crm_conta_loja_vend_idx ON crm_vendas_conta (loja_id, vendedor_id);
                END IF;
                IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'crm_conta_loja_created_idx') THEN
                    CREATE INDEX CONCURRENTLY crm_conta_loja_created_idx ON crm_vendas_conta (loja_id, created_at);
                END IF;
            END $$;
            """,
            reverse_sql="""
            DROP INDEX IF EXISTS crm_conta_loja_nome_idx;
            DROP INDEX IF EXISTS crm_conta_loja_vend_idx;
            DROP INDEX IF EXISTS crm_conta_loja_created_idx;
            """,
        ),
        
        # Lead indexes
        migrations.RunSQL(
            sql="""
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'crm_lead_loja_status_idx') THEN
                    CREATE INDEX CONCURRENTLY crm_lead_loja_status_idx ON crm_vendas_lead (loja_id, status);
                END IF;
                IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'crm_lead_loja_origem_idx') THEN
                    CREATE INDEX CONCURRENTLY crm_lead_loja_origem_idx ON crm_vendas_lead (loja_id, origem);
                END IF;
                IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'crm_lead_loja_vend_idx') THEN
                    CREATE INDEX CONCURRENTLY crm_lead_loja_vend_idx ON crm_vendas_lead (loja_id, vendedor_id);
                END IF;
                IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'crm_lead_loja_created_idx') THEN
                    CREATE INDEX CONCURRENTLY crm_lead_loja_created_idx ON crm_vendas_lead (loja_id, created_at);
                END IF;
                IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'crm_lead_loja_conta_idx') THEN
                    CREATE INDEX CONCURRENTLY crm_lead_loja_conta_idx ON crm_vendas_lead (loja_id, conta_id);
                END IF;
            END $$;
            """,
            reverse_sql="""
            DROP INDEX IF EXISTS crm_lead_loja_status_idx;
            DROP INDEX IF EXISTS crm_lead_loja_origem_idx;
            DROP INDEX IF EXISTS crm_lead_loja_vend_idx;
            DROP INDEX IF EXISTS crm_lead_loja_created_idx;
            DROP INDEX IF EXISTS crm_lead_loja_conta_idx;
            """,
        ),
        
        # Contato indexes
        migrations.RunSQL(
            sql="""
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'crm_contato_loja_conta_idx') THEN
                    CREATE INDEX CONCURRENTLY crm_contato_loja_conta_idx ON crm_vendas_contato (loja_id, conta_id);
                END IF;
                IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'crm_contato_loja_email_idx') THEN
                    CREATE INDEX CONCURRENTLY crm_contato_loja_email_idx ON crm_vendas_contato (loja_id, email);
                END IF;
            END $$;
            """,
            reverse_sql="""
            DROP INDEX IF EXISTS crm_contato_loja_conta_idx;
            DROP INDEX IF EXISTS crm_contato_loja_email_idx;
            """,
        ),
        
        # Oportunidade indexes
        migrations.RunSQL(
            sql="""
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'crm_opor_loja_etapa_idx') THEN
                    CREATE INDEX CONCURRENTLY crm_opor_loja_etapa_idx ON crm_vendas_oportunidade (loja_id, etapa);
                END IF;
                IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'crm_opor_loja_vend_idx') THEN
                    CREATE INDEX CONCURRENTLY crm_opor_loja_vend_idx ON crm_vendas_oportunidade (loja_id, vendedor_id);
                END IF;
                IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'crm_opor_loja_lead_idx') THEN
                    CREATE INDEX CONCURRENTLY crm_opor_loja_lead_idx ON crm_vendas_oportunidade (loja_id, lead_id);
                END IF;
                IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'crm_opor_loja_dtfech_idx') THEN
                    CREATE INDEX CONCURRENTLY crm_opor_loja_dtfech_idx ON crm_vendas_oportunidade (loja_id, data_fechamento);
                END IF;
                IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'crm_opor_loja_etapa_vend_idx') THEN
                    CREATE INDEX CONCURRENTLY crm_opor_loja_etapa_vend_idx ON crm_vendas_oportunidade (loja_id, etapa, vendedor_id);
                END IF;
                IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'crm_opor_loja_created_idx') THEN
                    CREATE INDEX CONCURRENTLY crm_opor_loja_created_idx ON crm_vendas_oportunidade (loja_id, created_at);
                END IF;
            END $$;
            """,
            reverse_sql="""
            DROP INDEX IF EXISTS crm_opor_loja_etapa_idx;
            DROP INDEX IF EXISTS crm_opor_loja_vend_idx;
            DROP INDEX IF EXISTS crm_opor_loja_lead_idx;
            DROP INDEX IF EXISTS crm_opor_loja_dtfech_idx;
            DROP INDEX IF EXISTS crm_opor_loja_etapa_vend_idx;
            DROP INDEX IF EXISTS crm_opor_loja_created_idx;
            """,
        ),
        
        # Atividade indexes
        migrations.RunSQL(
            sql="""
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'crm_ativ_loja_data_idx') THEN
                    CREATE INDEX CONCURRENTLY crm_ativ_loja_data_idx ON crm_vendas_atividade (loja_id, data);
                END IF;
                IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'crm_ativ_loja_concl_idx') THEN
                    CREATE INDEX CONCURRENTLY crm_ativ_loja_concl_idx ON crm_vendas_atividade (loja_id, concluido);
                END IF;
                IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'crm_ativ_loja_opor_idx') THEN
                    CREATE INDEX CONCURRENTLY crm_ativ_loja_opor_idx ON crm_vendas_atividade (loja_id, oportunidade_id);
                END IF;
                IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'crm_ativ_loja_lead_idx') THEN
                    CREATE INDEX CONCURRENTLY crm_ativ_loja_lead_idx ON crm_vendas_atividade (loja_id, lead_id);
                END IF;
                IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'crm_ativ_loja_data_concl_idx') THEN
                    CREATE INDEX CONCURRENTLY crm_ativ_loja_data_concl_idx ON crm_vendas_atividade (loja_id, data, concluido);
                END IF;
            END $$;
            """,
            reverse_sql="""
            DROP INDEX IF EXISTS crm_ativ_loja_data_idx;
            DROP INDEX IF EXISTS crm_ativ_loja_concl_idx;
            DROP INDEX IF EXISTS crm_ativ_loja_opor_idx;
            DROP INDEX IF EXISTS crm_ativ_loja_lead_idx;
            DROP INDEX IF EXISTS crm_ativ_loja_data_concl_idx;
            """,
        ),
    ]
