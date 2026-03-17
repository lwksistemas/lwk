# Generated manually on 2026-03-17 21:30
# Corrige constraint de foreign key em FinanceiroLoja para usar CASCADE

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('superadmin', '0035_googlecalendarconnection_vendedor'),
    ]

    operations = [
        migrations.RunSQL(
            # Remover constraint antiga (NO ACTION)
            sql="""
            ALTER TABLE superadmin_financeiroloja 
            DROP CONSTRAINT IF EXISTS superadmin_financeir_loja_id_5f812886_fk_superadmi;
            """,
            reverse_sql=migrations.RunSQL.noop
        ),
        migrations.RunSQL(
            # Recriar constraint com CASCADE
            sql="""
            ALTER TABLE superadmin_financeiroloja 
            ADD CONSTRAINT superadmin_financeir_loja_id_5f812886_fk_superadmi 
            FOREIGN KEY (loja_id) 
            REFERENCES superadmin_loja(id) 
            ON DELETE CASCADE 
            DEFERRABLE INITIALLY DEFERRED;
            """,
            reverse_sql="""
            ALTER TABLE superadmin_financeiroloja 
            DROP CONSTRAINT IF EXISTS superadmin_financeir_loja_id_5f812886_fk_superadmi;
            
            ALTER TABLE superadmin_financeiroloja 
            ADD CONSTRAINT superadmin_financeir_loja_id_5f812886_fk_superadmi 
            FOREIGN KEY (loja_id) 
            REFERENCES superadmin_loja(id) 
            ON DELETE NO ACTION 
            DEFERRABLE INITIALLY DEFERRED;
            """
        ),
    ]
