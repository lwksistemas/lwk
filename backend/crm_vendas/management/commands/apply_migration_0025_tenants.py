"""
Comando para aplicar migration 0025 (remove GenericForeignKey) nos schemas de tenant.
"""
from django.core.management.base import BaseCommand
from django.db import connection
from superadmin.models import Loja


class Command(BaseCommand):
    help = 'Aplica migration 0025 (AssinaturaDigital) nos schemas de tenant'

    def handle(self, *args, **options):
        self.stdout.write('🔧 Aplicando migration 0025 nos schemas de tenant...\n')
        
        # Buscar lojas CRM ativas
        lojas_crm = Loja.objects.using('default').filter(
            is_active=True,
            tipo_loja__slug='crm-vendas'
        )
        
        self.stdout.write(f'📊 Lojas CRM encontradas: {lojas_crm.count()}\n')
        
        for loja in lojas_crm:
            schema_name = loja.database_name.replace('-', '_')
            self.stdout.write(f'\n🏪 Loja: {loja.nome} (ID: {loja.id})')
            self.stdout.write(f'   Schema: {schema_name}')
            
            try:
                # Verificar se schema existe
                with connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT EXISTS (
                            SELECT 1 
                            FROM information_schema.schemata 
                            WHERE schema_name = %s
                        )
                    """, [schema_name])
                    
                    if not cursor.fetchone()[0]:
                        self.stdout.write(self.style.WARNING(f'   ⚠️  Schema não existe'))
                        continue
                    
                    # Verificar se tabela AssinaturaDigital existe
                    cursor.execute(f"""
                        SELECT EXISTS (
                            SELECT 1 
                            FROM information_schema.tables 
                            WHERE table_schema = %s
                            AND table_name = 'crm_vendas_assinatura_digital'
                        )
                    """, [schema_name])
                    
                    if not cursor.fetchone()[0]:
                        self.stdout.write(self.style.WARNING(f'   ⚠️  Tabela AssinaturaDigital não existe'))
                        continue
                    
                    # Verificar se migration já foi aplicada (campos novos existem)
                    cursor.execute(f"""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_schema = %s
                        AND table_name = 'crm_vendas_assinatura_digital'
                        AND column_name IN ('proposta_id', 'contrato_id')
                    """, [schema_name])
                    
                    colunas_existentes = [row[0] for row in cursor.fetchall()]
                    
                    if len(colunas_existentes) == 2:
                        self.stdout.write(self.style.SUCCESS(f'   ✅ Migration já aplicada'))
                        continue
                    
                    # Aplicar migration
                    self.stdout.write(f'   🔄 Aplicando migration...')
                    
                    # Setar search_path
                    cursor.execute(f'SET search_path TO "{schema_name}", public')
                    
                    # 1. Adicionar novos campos
                    if 'proposta_id' not in colunas_existentes:
                        cursor.execute("""
                            ALTER TABLE crm_vendas_assinatura_digital
                            ADD COLUMN proposta_id INTEGER NULL
                        """)
                        self.stdout.write(f'      ✅ Campo proposta_id adicionado')
                    
                    if 'contrato_id' not in colunas_existentes:
                        cursor.execute("""
                            ALTER TABLE crm_vendas_assinatura_digital
                            ADD COLUMN contrato_id INTEGER NULL
                        """)
                        self.stdout.write(f'      ✅ Campo contrato_id adicionado')
                    
                    # 2. Migrar dados existentes
                    cursor.execute("""
                        UPDATE crm_vendas_assinatura_digital
                        SET proposta_id = object_id
                        WHERE content_type_id = (
                            SELECT id FROM django_content_type 
                            WHERE app_label = 'crm_vendas' AND model = 'proposta'
                        )
                        AND proposta_id IS NULL
                    """)
                    proposta_count = cursor.rowcount
                    
                    cursor.execute("""
                        UPDATE crm_vendas_assinatura_digital
                        SET contrato_id = object_id
                        WHERE content_type_id = (
                            SELECT id FROM django_content_type 
                            WHERE app_label = 'crm_vendas' AND model = 'contrato'
                        )
                        AND contrato_id IS NULL
                    """)
                    contrato_count = cursor.rowcount
                    
                    self.stdout.write(f'      ✅ Dados migrados: {proposta_count} propostas, {contrato_count} contratos')
                    
                    # 3. Adicionar ForeignKeys
                    cursor.execute("""
                        ALTER TABLE crm_vendas_assinatura_digital
                        ADD CONSTRAINT crm_assin_proposta_fk
                        FOREIGN KEY (proposta_id)
                        REFERENCES crm_vendas_proposta(id)
                        ON DELETE CASCADE
                        DEFERRABLE INITIALLY DEFERRED
                    """)
                    self.stdout.write(f'      ✅ ForeignKey proposta_id criada')
                    
                    cursor.execute("""
                        ALTER TABLE crm_vendas_assinatura_digital
                        ADD CONSTRAINT crm_assin_contrato_fk
                        FOREIGN KEY (contrato_id)
                        REFERENCES crm_vendas_contrato(id)
                        ON DELETE CASCADE
                        DEFERRABLE INITIALLY DEFERRED
                    """)
                    self.stdout.write(f'      ✅ ForeignKey contrato_id criada')
                    
                    # 4. Remover campos antigos
                    cursor.execute("""
                        ALTER TABLE crm_vendas_assinatura_digital
                        DROP COLUMN IF EXISTS content_type_id CASCADE
                    """)
                    self.stdout.write(f'      ✅ Campo content_type_id removido')
                    
                    cursor.execute("""
                        ALTER TABLE crm_vendas_assinatura_digital
                        DROP COLUMN IF EXISTS object_id CASCADE
                    """)
                    self.stdout.write(f'      ✅ Campo object_id removido')
                    
                    # 5. Remover índice antigo e adicionar novos
                    cursor.execute("""
                        DROP INDEX IF EXISTS crm_assin_content_idx
                    """)
                    
                    cursor.execute("""
                        CREATE INDEX IF NOT EXISTS crm_assin_proposta_idx
                        ON crm_vendas_assinatura_digital(proposta_id)
                    """)
                    self.stdout.write(f'      ✅ Índice proposta_id criado')
                    
                    cursor.execute("""
                        CREATE INDEX IF NOT EXISTS crm_assin_contrato_idx
                        ON crm_vendas_assinatura_digital(contrato_id)
                    """)
                    self.stdout.write(f'      ✅ Índice contrato_id criado')
                    
                    # 6. Adicionar constraint
                    cursor.execute("""
                        ALTER TABLE crm_vendas_assinatura_digital
                        ADD CONSTRAINT crm_assin_proposta_ou_contrato
                        CHECK (
                            (proposta_id IS NOT NULL AND contrato_id IS NULL) OR
                            (proposta_id IS NULL AND contrato_id IS NOT NULL)
                        )
                    """)
                    self.stdout.write(f'      ✅ Constraint adicionada')
                    
                    # 7. Registrar migration como aplicada
                    cursor.execute("""
                        INSERT INTO django_migrations (app, name, applied)
                        VALUES ('crm_vendas', '0025_remove_genericforeignkey_assinatura', NOW())
                        ON CONFLICT DO NOTHING
                    """)
                    
                    self.stdout.write(self.style.SUCCESS(f'   ✅ Migration aplicada com sucesso!'))
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'   ❌ Erro: {e}'))
                import traceback
                self.stdout.write(traceback.format_exc())
        
        self.stdout.write(self.style.SUCCESS('\n✅ Processo concluído!'))
