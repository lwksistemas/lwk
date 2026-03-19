"""
Comando para criar/corrigir tabela AssinaturaDigital no schema public.
Sistema usa tabelas compartilhadas com filtro por loja_id, não schemas isolados.
"""
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Cria/corrige tabela AssinaturaDigital no schema public'

    def handle(self, *args, **options):
        self.stdout.write('🔄 Corrigindo tabela AssinaturaDigital...\n')
        
        try:
            with connection.cursor() as cursor:
                # Verificar se a tabela existe
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public'
                        AND table_name = 'crm_vendas_assinatura_digital'
                    );
                """)
                tabela_existe = cursor.fetchone()[0]
                
                if tabela_existe:
                    # Verificar se já tem os novos campos
                    cursor.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.columns 
                            WHERE table_schema = 'public'
                            AND table_name = 'crm_vendas_assinatura_digital'
                            AND column_name = 'proposta_id'
                        );
                    """)
                    tem_novos_campos = cursor.fetchone()[0]
                    
                    if tem_novos_campos:
                        self.stdout.write(self.style.SUCCESS('✅ Tabela já está correta'))
                        return
                    
                    self.stdout.write('🔄 Atualizando estrutura da tabela...')
                    
                    # Fazer backup dos dados
                    cursor.execute("""
                        CREATE TEMP TABLE assinatura_backup AS
                        SELECT * FROM crm_vendas_assinatura_digital;
                    """)
                    
                    # Dropar tabela antiga
                    cursor.execute('DROP TABLE IF EXISTS crm_vendas_assinatura_digital CASCADE;')
                else:
                    self.stdout.write('🔄 Criando tabela...')
                
                # Criar tabela com estrutura correta
                cursor.execute("""
                    CREATE TABLE crm_vendas_assinatura_digital (
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
                
                # Criar índices
                cursor.execute("""
                    CREATE INDEX crm_assin_loja_token_idx
                    ON crm_vendas_assinatura_digital (loja_id, token);
                """)
                
                cursor.execute("""
                    CREATE INDEX crm_assin_loja_tipo_idx
                    ON crm_vendas_assinatura_digital (loja_id, tipo, assinado);
                """)
                
                cursor.execute("""
                    CREATE INDEX crm_assin_proposta_idx
                    ON crm_vendas_assinatura_digital (proposta_id);
                """)
                
                cursor.execute("""
                    CREATE INDEX crm_assin_contrato_idx
                    ON crm_vendas_assinatura_digital (contrato_id);
                """)
                
                # Restaurar dados se havia backup
                if tabela_existe:
                    cursor.execute("""
                        INSERT INTO crm_vendas_assinatura_digital (
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
                                    SELECT id FROM django_content_type 
                                    WHERE app_label = 'crm_vendas' AND model = 'proposta'
                                ) THEN object_id
                                ELSE NULL
                            END as proposta_id,
                            CASE 
                                WHEN content_type_id = (
                                    SELECT id FROM django_content_type 
                                    WHERE app_label = 'crm_vendas' AND model = 'contrato'
                                ) THEN object_id
                                ELSE NULL
                            END as contrato_id
                        FROM assinatura_backup;
                    """)
                    
                    # Atualizar sequence
                    cursor.execute("""
                        SELECT setval('crm_vendas_assinatura_digital_id_seq', 
                            (SELECT MAX(id) FROM crm_vendas_assinatura_digital));
                    """)
                
                self.stdout.write(self.style.SUCCESS('\n✅ Tabela corrigida com sucesso!'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ Erro: {str(e)}'))
            import traceback
            traceback.print_exc()
            raise
