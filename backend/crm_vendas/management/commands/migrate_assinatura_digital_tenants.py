"""
Comando para aplicar migration de AssinaturaDigital em todos os schemas de tenant.
A migration 0025 precisa ser aplicada em cada schema de loja.
"""
from django.core.management.base import BaseCommand
from django.db import connection
from superadmin.models import Loja


class Command(BaseCommand):
    help = 'Aplica migration 0025 de AssinaturaDigital em todos os schemas de tenant'

    def handle(self, *args, **options):
        self.stdout.write('🔄 Iniciando migração de AssinaturaDigital nos tenants...\n')
        
        # Obter todas as lojas ativas
        lojas = Loja.objects.using('default').filter(is_active=True)
        total = lojas.count()
        
        self.stdout.write(f'📊 Total de lojas ativas: {total}\n')
        
        sucesso = 0
        erros = 0
        
        for i, loja in enumerate(lojas, 1):
            schema_name = f'loja_{loja.id}'
            self.stdout.write(f'[{i}/{total}] Processando {loja.nome} (schema: {schema_name})...')
            
            try:
                with connection.cursor() as cursor:
                    # Verificar se a tabela existe no schema
                    cursor.execute(f"""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_schema = '{schema_name}'
                            AND table_name = 'crm_vendas_assinatura_digital'
                        );
                    """)
                    tabela_existe = cursor.fetchone()[0]
                    
                    if not tabela_existe:
                        self.stdout.write(self.style.WARNING(f'  ⚠️  Tabela não existe no schema {schema_name}'))
                        continue
                    
                    # Verificar se a coluna proposta_id já existe
                    cursor.execute(f"""
                        SELECT EXISTS (
                            SELECT FROM information_schema.columns 
                            WHERE table_schema = '{schema_name}'
                            AND table_name = 'crm_vendas_assinatura_digital'
                            AND column_name = 'proposta_id'
                        );
                    """)
                    coluna_existe = cursor.fetchone()[0]
                    
                    if coluna_existe:
                        self.stdout.write(self.style.SUCCESS(f'  ✅ Já migrado'))
                        sucesso += 1
                        continue
                    
                    # Aplicar migration
                    cursor.execute(f'SET search_path TO {schema_name};')
                    
                    # Adicionar coluna proposta_id
                    cursor.execute("""
                        ALTER TABLE crm_vendas_assinatura_digital
                        ADD COLUMN proposta_id INTEGER NULL;
                    """)
                    
                    # Adicionar coluna contrato_id
                    cursor.execute("""
                        ALTER TABLE crm_vendas_assinatura_digital
                        ADD COLUMN contrato_id INTEGER NULL;
                    """)
                    
                    # Migrar dados existentes
                    cursor.execute("""
                        UPDATE crm_vendas_assinatura_digital
                        SET proposta_id = object_id
                        WHERE content_type_id = (
                            SELECT id FROM public.django_content_type 
                            WHERE app_label = 'crm_vendas' AND model = 'proposta'
                        );
                    """)
                    
                    cursor.execute("""
                        UPDATE crm_vendas_assinatura_digital
                        SET contrato_id = object_id
                        WHERE content_type_id = (
                            SELECT id FROM public.django_content_type 
                            WHERE app_label = 'crm_vendas' AND model = 'contrato'
                        );
                    """)
                    
                    # Adicionar foreign keys
                    cursor.execute("""
                        ALTER TABLE crm_vendas_assinatura_digital
                        ADD CONSTRAINT crm_vendas_assinatura_digital_proposta_id_fkey
                        FOREIGN KEY (proposta_id) REFERENCES crm_vendas_proposta(id)
                        ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED;
                    """)
                    
                    cursor.execute("""
                        ALTER TABLE crm_vendas_assinatura_digital
                        ADD CONSTRAINT crm_vendas_assinatura_digital_contrato_id_fkey
                        FOREIGN KEY (contrato_id) REFERENCES crm_vendas_contrato(id)
                        ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED;
                    """)
                    
                    # Remover colunas antigas
                    cursor.execute("""
                        ALTER TABLE crm_vendas_assinatura_digital
                        DROP COLUMN IF EXISTS content_type_id;
                    """)
                    
                    cursor.execute("""
                        ALTER TABLE crm_vendas_assinatura_digital
                        DROP COLUMN IF EXISTS object_id;
                    """)
                    
                    # Remover índice antigo se existir
                    cursor.execute("""
                        DROP INDEX IF EXISTS crm_assin_content_idx;
                    """)
                    
                    # Adicionar novos índices
                    cursor.execute("""
                        CREATE INDEX IF NOT EXISTS crm_assin_proposta_idx
                        ON crm_vendas_assinatura_digital (proposta_id);
                    """)
                    
                    cursor.execute("""
                        CREATE INDEX IF NOT EXISTS crm_assin_contrato_idx
                        ON crm_vendas_assinatura_digital (contrato_id);
                    """)
                    
                    # Adicionar constraint
                    cursor.execute("""
                        ALTER TABLE crm_vendas_assinatura_digital
                        ADD CONSTRAINT crm_assin_proposta_ou_contrato
                        CHECK (
                            (proposta_id IS NOT NULL AND contrato_id IS NULL) OR
                            (proposta_id IS NULL AND contrato_id IS NOT NULL)
                        );
                    """)
                    
                    self.stdout.write(self.style.SUCCESS(f'  ✅ Migrado com sucesso'))
                    sucesso += 1
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ❌ Erro: {str(e)}'))
                erros += 1
        
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS(f'✅ Sucesso: {sucesso}'))
        if erros > 0:
            self.stdout.write(self.style.ERROR(f'❌ Erros: {erros}'))
        self.stdout.write('='*60 + '\n')
        
        if erros == 0:
            self.stdout.write(self.style.SUCCESS('🎉 Migração concluída com sucesso em todos os tenants!'))
        else:
            self.stdout.write(self.style.WARNING(f'⚠️  Migração concluída com {erros} erro(s)'))
