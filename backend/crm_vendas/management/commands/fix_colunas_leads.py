"""
Comando para adicionar 'valor_estimado' nas colunas_leads de todas as lojas.
"""
from django.core.management.base import BaseCommand
from django_tenants.utils import schema_context
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
                # Usar schema_context para mudar para o schema do tenant
                with schema_context(loja.schema_name):
                    # Buscar ou criar configuração
                    config, created = CRMConfig.objects.get_or_create(
                        loja_id=loja.id,
                        defaults={
                            'origens_leads': CRMConfig.get_default_origens(),
                            'etapas_pipeline': CRMConfig.get_default_etapas(),
                            'colunas_leads': CRMConfig.get_default_colunas_leads(),
                            'modulos_ativos': CRMConfig.get_default_modulos(),
                        }
                    )
                    
                    if created:
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"✅ Loja {loja.slug} ({loja.nome}): Configuração criada com colunas padrão"
                            )
                        )
                        atualizadas += 1
                        continue
                    
                    # Verificar se valor_estimado está nas colunas
                    if 'valor_estimado' not in config.colunas_leads:
                        # Adicionar valor_estimado
                        config.colunas_leads.append('valor_estimado')
                        config.save(update_fields=['colunas_leads', 'updated_at'])
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
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"❌ Erro na loja {loja.slug}: {e}")
                )
        
        self.stdout.write(
            self.style.SUCCESS(f"\n✅ Processo concluído! {atualizadas} lojas atualizadas.")
        )
