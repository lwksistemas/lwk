"""
Script para aplicar migration 0052 (tipo na Conta + empresa_prestadora na Oportunidade)
diretamente via SQL em todos os schemas de lojas.
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection
from superadmin.models import Loja


def apply():
    lojas = Loja.objects.filter(is_active=True, database_created=True)
    print(f"Encontradas {lojas.count()} lojas ativas\n")

    for loja in lojas:
        schema = loja.schema_name if hasattr(loja, 'schema_name') else f"loja_{loja.cnpj.replace('.','').replace('/','').replace('-','')}"
        print(f"🔄 Schema: {schema} ({loja.nome})")
        try:
            with connection.cursor() as cursor:
                cursor.execute(f"SET search_path TO {schema}")

                # 1. Adicionar campo tipo na crm_vendas_conta
                cursor.execute(f"""
                    DO $$
                    BEGIN
                        IF NOT EXISTS (
                            SELECT 1 FROM information_schema.columns
                            WHERE table_schema = '{schema}'
                            AND table_name = 'crm_vendas_conta'
                            AND column_name = 'tipo'
                        ) THEN
                            ALTER TABLE crm_vendas_conta ADD COLUMN tipo varchar(20) NOT NULL DEFAULT 'cliente';
                        END IF;
                    END $$;
                """)

                # 2. Adicionar campo empresa_prestadora_id na crm_vendas_oportunidade
                cursor.execute(f"""
                    DO $$
                    BEGIN
                        IF NOT EXISTS (
                            SELECT 1 FROM information_schema.columns
                            WHERE table_schema = '{schema}'
                            AND table_name = 'crm_vendas_oportunidade'
                            AND column_name = 'empresa_prestadora_id'
                        ) THEN
                            ALTER TABLE crm_vendas_oportunidade
                                ADD COLUMN empresa_prestadora_id integer NULL
                                REFERENCES crm_vendas_conta(id) ON DELETE SET NULL;
                        END IF;
                    END $$;
                """)

                # 3. Index por tipo
                cursor.execute(f"""
                    CREATE INDEX IF NOT EXISTS crm_conta_loja_tipo_idx
                    ON crm_vendas_conta(loja_id, tipo);
                """)

                connection.commit()
                print(f"  ✅ OK")
        except Exception as e:
            print(f"  ❌ Erro: {e}")

    # Reset search_path
    with connection.cursor() as cursor:
        cursor.execute("SET search_path TO public")

    print("\n✅ Concluído!")


if __name__ == '__main__':
    apply()
