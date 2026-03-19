"""
Comando para ativar o módulo de contatos em todas as lojas.
"""
from django.core.management.base import BaseCommand
from django.db import connection
from superadmin.models import Loja
from crm_vendas.models_config import CRMConfig


class Command(BaseCommand):
    help = 'Ativa o módulo de contatos em todas as lojas'

    def handle(self, *args, **options):
        lojas = Loja.objects.filter(is_active=True)
        
        self.stdout.write(f'Encontradas {lojas.count()} lojas ativas')
        
        for loja in lojas:
            schema_name = loja.database_name
            self.stdout.write(f'\nProcessando loja {loja.id} - {loja.nome} (schema: {schema_name})')
            
            try:
                with connection.cursor() as cursor:
                    # Setar o search_path para o schema da loja
                    cursor.execute(f"SET search_path TO {schema_name};")
                    
                    # Buscar ou criar config
                    cursor.execute("""
                        SELECT id, modulos_ativos FROM crm_vendas_config WHERE loja_id = %s LIMIT 1;
                    """, [loja.id])
                    
                    result = cursor.fetchone()
                    
                    if result:
                        config_id, modulos_ativos = result
                        
                        # Verificar se contatos já está ativo
                        if modulos_ativos and modulos_ativos.get('contatos'):
                            self.stdout.write(self.style.SUCCESS(f'  ✅ Módulo CONTATOS já está ativo'))
                        else:
                            # Ativar módulo contatos
                            if not modulos_ativos:
                                modulos_ativos = CRMConfig.get_default_modulos()
                            else:
                                modulos_ativos['contatos'] = True
                            
                            cursor.execute("""
                                UPDATE crm_vendas_config 
                                SET modulos_ativos = %s::jsonb, updated_at = NOW()
                                WHERE id = %s;
                            """, [str(modulos_ativos).replace("'", '"'), config_id])
                            
                            self.stdout.write(self.style.SUCCESS(f'  ✅ Módulo CONTATOS ativado com sucesso'))
                    else:
                        # Criar config com módulos padrão
                        modulos_ativos = CRMConfig.get_default_modulos()
                        origens_leads = CRMConfig.get_default_origens()
                        etapas_pipeline = CRMConfig.get_default_etapas()
                        colunas_leads = CRMConfig.get_default_colunas_leads()
                        
                        cursor.execute("""
                            INSERT INTO crm_vendas_config 
                            (loja_id, origens_leads, etapas_pipeline, colunas_leads, modulos_ativos, created_at, updated_at)
                            VALUES (%s, %s::jsonb, %s::jsonb, %s::jsonb, %s::jsonb, NOW(), NOW());
                        """, [
                            loja.id,
                            str(origens_leads).replace("'", '"'),
                            str(etapas_pipeline).replace("'", '"'),
                            str(colunas_leads).replace("'", '"'),
                            str(modulos_ativos).replace("'", '"')
                        ])
                        
                        self.stdout.write(self.style.SUCCESS(f'  ✅ Config criada e módulo CONTATOS ativado'))
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ❌ Erro ao processar schema {schema_name}: {str(e)}'))
        
        self.stdout.write(self.style.SUCCESS('\n✅ Comando concluído!'))
