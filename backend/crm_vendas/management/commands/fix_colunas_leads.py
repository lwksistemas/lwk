"""
Comando para adicionar 'valor_estimado' nas colunas_leads de todas as lojas.
"""
from django.core.management.base import BaseCommand
from django.db import connection
from crm_vendas.models_config import CRMConfig
from superadmin.models import Loja


class Command(BaseCommand):
    help = 'Adiciona valor_estimado nas colunas_leads de todas as configurações CRM'

    def handle(self, *args, **options):
        self.stdout.write("🔧 Corrigindo colunas_leads em todas as lojas...")
        
        lojas = Loja.objects.filter(is_active=True)
        self.stdout.write(f"📊 Total de lojas ativas: {lojas.count()}")
        
        atualizadas = 0
        
        for loja in lojas:
            try:
                # Construir schema_name a partir do slug
                schema_name = f"loja_{loja.slug}"
                
                # Usar SQL direto para mudar de schema e atualizar
                with connection.cursor() as cursor:
                    # Mudar para o schema do tenant
                    cursor.execute(f"SET search_path TO {schema_name}")
                    
                    # Verificar se a configuração existe
                    cursor.execute("""
                        SELECT id, colunas_leads 
                        FROM crm_vendas_config 
                        WHERE loja_id = %s
                    """, [loja.id])
                    
                    row = cursor.fetchone()
                    
                    if not row:
                        # Criar configuração com valores padrão
                        colunas_default = ['nome', 'empresa', 'telefone', 'email', 'origem', 'status', 'valor_estimado']
                        cursor.execute("""
                            INSERT INTO crm_vendas_config 
                            (loja_id, origens_leads, etapas_pipeline, colunas_leads, modulos_ativos, created_at, updated_at)
                            VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
                        """, [
                            loja.id,
                            '[]',
                            '[]',
                            str(colunas_default).replace("'", '"'),
                            '{}'
                        ])
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"✅ Loja {loja.slug} ({loja.nome}): Configuração criada com colunas padrão"
                            )
                        )
                        atualizadas += 1
                    else:
                        config_id, colunas_leads = row
                        
                        # Verificar se valor_estimado já está nas colunas
                        if 'valor_estimado' not in str(colunas_leads):
                            # Adicionar valor_estimado
                            import json
                            colunas_list = json.loads(colunas_leads) if isinstance(colunas_leads, str) else colunas_leads
                            colunas_list.append('valor_estimado')
                            
                            cursor.execute("""
                                UPDATE crm_vendas_config 
                                SET colunas_leads = %s, updated_at = NOW()
                                WHERE id = %s
                            """, [json.dumps(colunas_list), config_id])
                            
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f"✅ Loja {loja.slug} ({loja.nome}): valor_estimado adicionado"
                                )
                            )
                            atualizadas += 1
                        else:
                            self.stdout.write(
                                f"ℹ️  Loja {loja.slug} ({loja.nome}): já possui valor_estimado"
                            )
                    
                    # Voltar para o schema public
                    cursor.execute("SET search_path TO public")
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"❌ Erro na loja {loja.slug}: {e}")
                )
        
        self.stdout.write(
            self.style.SUCCESS(f"\n✅ Processo concluído! {atualizadas} lojas atualizadas.")
        )
