"""
Comando para criar tabela AssinaturaDigital em todos os schemas de tenant.
Aplica migrations 0024 e 0025 completas.
"""
from django.core.management.base import BaseCommand
from django.db import connection
from superadmin.models import Loja


class Command(BaseCommand):
    help = 'Cria tabela AssinaturaDigital em todos os schemas de tenant'

    def handle(self, *args, **options):
        self.stdout.write('🔄 Iniciando setup de AssinaturaDigital nos tenants...\n')
        
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
                    # Definir search_path
                    cursor.execute(f'SET search_path TO {schema_name};')
                    
                    # Verificar se a tabela já existe
                    cursor.execute(f"""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_schema = '{schema_name}'
                            AND table_name = 'crm_vendas_assinatura_digital'
                        );
                    """)
                    tabela_existe = cursor.fetchone()[0]
                    
                    if tabela_existe:
                        # Verificar se já tem os novos campos
                        cursor.execute(f"""
                            SELECT EXISTS (
                                SELECT FROM information_schema.columns 
                                WHERE table_schema = '{schema_name}'
                                AND table_name = 'crm_vendas_assinatura_digital'
                                AND column_name = 'proposta_id'
                            );
                        """)
                        tem_novos_campos = cursor.fetchone()[0]
                        
                        if tem_novos_campos:
                            self.stdout.write(self.style.SUCCESS(f'  ✅ Já configurado'))
                            sucesso += 1
                            continue
                        else:
                            self.stdout.write(f'  🔄 Atualizando estrutura...')
                    else:
                        self.stdout.write(f'  🔄 Criando tabela...')
                    
                    # Criar ou recriar tabela com estrutura correta
                    if tabela_existe:
                        # Fazer backup dos dados
                        cursor.execute(f"""
                            CREATE TEMP TABLE assinatura_backup AS
                            SELECT * FROM {schema_name}.crm_vendas_assinatura_digital;
                        """)
                        
                        # Dropar tabela antiga
                        cursor.execute(f'DROP TABLE IF EXISTS {schema_name}.crm_vendas_assinatura_digital CASCADE;')
                    
                    # Criar tabela nova com estrutura correta
                    cursor.execute(f"""
                        CREATE TABLE {schema_name}.crm_vendas_assinatura_digital (
                            id SERIAL PRIMARY KEY,
                            loja_id INTEGER NOT NULL,
                            proposta_id INTEGER NULL,
                            contrato_id INTEGER NULL,
                            tipo VARCHAR(10) NOT NULL,
                            nome_assinante VARCHAR(200) NOT NULL,
                            email_assinante VARCHAR(254) NOT NULL,
                            ip_address INET NOT NULL,
                            timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                            user_agent TEXT NOT NULL DEFAULT '',
                            token VARCHAR(255) NOT NULL UNIQUE,
                            token_expira_em TIMESTAMP WITH TIME ZONE NOT NULL,
                            assinado BOOLEAN NOT NULL DEFAULT FALSE,
                            assinado_em TIMESTAMP WITH TIME ZONE NULL,
                            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                            CONSTRAINT crm_assin_proposta_ou_contrato CHECK (
                                (proposta_id IS NOT NULL AND contrato_id IS NULL) OR
                                (proposta_id IS NULL AND contrato_id IS NOT NULL)
                            )
                        );
                    """)
                    
                    # Adicionar foreign keys
                    cursor.execute(f"""
                        ALTER TABLE {schema_name}.crm_vendas_assinatura_digital
                        ADD CONSTRAINT crm_vendas_assinatura_digital_proposta_id_fkey
                        FOREIGN KEY (proposta_id) REFERENCES {schema_name}.crm_vendas_proposta(id)
                        ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED;
                    """)
                    
                    cursor.execute(f"""
                        ALTER TABLE {schema_name}.crm_vendas_assinatura_digital
                        ADD CONSTRAINT crm_vendas_assinatura_digital_contrato_id_fkey
                        FOREIGN KEY (contrato_id) REFERENCES {schema_name}.crm_vendas_contrato(id)
                        ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED;
                    """)
                    
                    # Criar índices
                    cursor.execute(f"""
                        CREATE INDEX crm_assin_loja_token_idx
                        ON {schema_name}.crm_vendas_assinatura_digital (loja_id, token);
                    """)
                    
                    cursor.execute(f"""
                        CREATE INDEX crm_assin_loja_tipo_idx
                        ON {schema_name}.crm_vendas_assinatura_digital (loja_id, tipo, assinado);
                    """)
                    
                    cursor.execute(f"""
                        CREATE INDEX crm_assin_proposta_idx
                        ON {schema_name}.crm_vendas_assinatura_digital (proposta_id);
                    """)
                    
                    cursor.execute(f"""
                        CREATE INDEX crm_assin_contrato_idx
                        ON {schema_name}.crm_vendas_assinatura_digital (contrato_id);
                    """)
                    
                    # Restaurar dados se havia backup
                    if tabela_existe:
                        cursor.execute(f"""
                            INSERT INTO {schema_name}.crm_vendas_assinatura_digital (
                                id, loja_id, tipo, nome_assinante, email_assinante,
                                ip_address, timestamp, user_agent, token, token_expira_em,
                                assinado, assinado_em, created_at, updated_at,
                                proposta_id, contrato_id
                            )
                            SELECT 
                                id, loja_id, tipo, nome_assinante, email_assinante,
                                ip_address, timestamp, user_agent, token, token_expira_em,
                                assinado, assinado_em, created_at, updated_at,
                                CASE 
                                    WHEN content_type_id = (
                                        SELECT id FROM public.django_content_type 
                                        WHERE app_label = 'crm_vendas' AND model = 'proposta'
                                    ) THEN object_id
                                    ELSE NULL
                                END as proposta_id,
                                CASE 
                                    WHEN content_type_id = (
                                        SELECT id FROM public.django_content_type 
                                        WHERE app_label = 'crm_vendas' AND model = 'contrato'
                                    ) THEN object_id
                                    ELSE NULL
                                END as contrato_id
                            FROM assinatura_backup;
                        """)
                        
                        # Atualizar sequence
                        cursor.execute(f"""
                            SELECT setval('{schema_name}.crm_vendas_assinatura_digital_id_seq', 
                                (SELECT MAX(id) FROM crm_vendas_assinatura_digital));
                        """)
                    
                    self.stdout.write(self.style.SUCCESS(f'  ✅ Configurado com sucesso'))
                    sucesso += 1
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ❌ Erro: {str(e)}'))
                erros += 1
                import traceback
                traceback.print_exc()
        
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS(f'✅ Sucesso: {sucesso}'))
        if erros > 0:
            self.stdout.write(self.style.ERROR(f'❌ Erros: {erros}'))
        self.stdout.write('='*60 + '\n')
        
        if erros == 0:
            self.stdout.write(self.style.SUCCESS('🎉 Setup concluído com sucesso em todos os tenants!'))
        else:
            self.stdout.write(self.style.WARNING(f'⚠️  Setup concluído com {erros} erro(s)'))
