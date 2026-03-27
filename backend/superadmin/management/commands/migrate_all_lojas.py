"""
Comando para aplicar migrations em todos os schemas das lojas
✅ OTIMIZADO: Fecha conexões após cada loja para evitar "too many connections"
"""
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.conf import settings
from django.db import connections
from superadmin.models import Loja
import os


class Command(BaseCommand):
    help = 'Aplica migrations em todos os schemas das lojas'

    def handle(self, *args, **options):
        """
        ✅ FIX: Retry logic para evitar timeout do PostgreSQL
        """
        from django.db import OperationalError
        import time
        
        self.stdout.write("🔧 Aplicando migrations em todas as lojas...\n")
        
        # ✅ FIX: Retry logic para buscar lojas
        max_retries = 3
        retry_delay = 2
        lojas = None
        
        for attempt in range(max_retries):
            try:
                lojas = list(Loja.objects.all())
                self.stdout.write(f"📊 Total de lojas: {len(lojas)}\n")
                break
            except OperationalError as e:
                if 'timeout' in str(e).lower() and attempt < max_retries - 1:
                    self.stdout.write(
                        self.style.WARNING(
                            f"⚠️ Timeout ao buscar lojas (tentativa {attempt + 1}/{max_retries}). "
                            f"Tentando novamente em {retry_delay}s..."
                        )
                    )
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    self.stdout.write(
                        self.style.ERROR(
                            f"❌ Falha ao buscar lojas após {max_retries} tentativas: {e}"
                        )
                    )
                    return
        
        if not lojas:
            self.stdout.write(self.style.ERROR("❌ Nenhuma loja encontrada"))
            return
        
        # Configurar bancos das lojas
        DATABASE_URL = os.environ.get('DATABASE_URL')
        if not DATABASE_URL:
            self.stdout.write(self.style.ERROR("❌ DATABASE_URL não configurada"))
            return
        
        for loja in lojas:
            self.stdout.write(f"\n{'='*60}")
            self.stdout.write(f"Loja: {loja.nome} (ID: {loja.id})")
            self.stdout.write(f"Database: {loja.database_name}")

            from core.db_config import ensure_loja_database_config
            if ensure_loja_database_config(loja.database_name, conn_max_age=0):
                self.stdout.write(f"✅ Banco configurado")
            
            # Aplicar migrations
            tipo_slug = loja.tipo_loja.slug if loja.tipo_loja else 'unknown'
            
            # Apps base (sempre aplicar)
            base_apps = ['stores', 'products']
            
            # Apps específicos por tipo de app (whatsapp = config isolada por loja para Clínica da Beleza)
            tipo_apps = {
                'clinica-de-estetica': ['clinica_estetica'],
                'clinica-estetica': ['clinica_estetica'],
                'clinica-da-beleza': ['clinica_beleza', 'whatsapp'],
                'e-commerce': ['ecommerce'],
                'restaurante': ['restaurante'],
                'servicos': ['servicos'],
                'cabeleireiro': ['cabeleireiro'],
                'crm-vendas': ['crm_vendas'],
            }
            
            apps_to_migrate = base_apps + tipo_apps.get(tipo_slug, [])
            
            for app in apps_to_migrate:
                # ✅ FIX: Retry logic para cada migration
                for attempt in range(max_retries):
                    try:
                        self.stdout.write(f"  Migrando {app}... (tentativa {attempt + 1})")
                        call_command(
                            'migrate', 
                            app, 
                            '--database', loja.database_name,
                            verbosity=0
                        )
                        self.stdout.write(self.style.SUCCESS(f"  ✅ {app} migrado"))
                        break  # Sucesso, sair do loop
                    except OperationalError as e:
                        if 'timeout' in str(e).lower() and attempt < max_retries - 1:
                            self.stdout.write(
                                self.style.WARNING(
                                    f"  ⚠️ Timeout em {app} (tentativa {attempt + 1}/{max_retries}). "
                                    f"Tentando novamente em {retry_delay}s..."
                                )
                            )
                            time.sleep(retry_delay)
                        else:
                            self.stdout.write(
                                self.style.WARNING(
                                    f"  ⚠️ Erro em {app} após {max_retries} tentativas: {e}"
                                )
                            )
                            break
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f"  ⚠️ Erro em {app}: {e}"))
                        break
            
            # ✅ CRÍTICO: Fechar todas as conexões desta loja antes de processar a próxima
            # Evita "too many connections for role" ao processar múltiplas lojas
            if loja.database_name in connections:
                try:
                    connections[loja.database_name].close()
                    self.stdout.write(f"✅ Conexões fechadas para {loja.database_name}")
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"⚠️ Erro ao fechar conexões: {e}"))
            
            # Remover banco das configurações para liberar memória
            if loja.database_name in settings.DATABASES:
                del settings.DATABASES[loja.database_name]
                self.stdout.write(f"✅ Banco removido das configurações")
        
        # Corrige colunas em schemas que têm crm_vendas_atividade
        self.stdout.write(f"\n{'='*60}")
        self.stdout.write("🔧 Verificando colunas em schemas com CRM...")
        try:
            call_command('fix_google_event_id_column', verbosity=1)
            call_command('fix_duracao_minutos_column', verbosity=1)
            call_command('fix_vendedor_column', verbosity=1)
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"  ⚠️ fix columns: {e}"))
        
        self.stdout.write(f"\n{'='*60}")
        self.stdout.write(self.style.SUCCESS("\n✅ Processo concluído!"))
