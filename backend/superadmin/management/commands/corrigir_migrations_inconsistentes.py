"""
Comando para corrigir migrations inconsistentes em schemas de lojas.
Marca stores.0001_initial como aplicada quando necessário.

Uso:
    python manage.py corrigir_migrations_inconsistentes
"""
from django.core.management.base import BaseCommand
from django.db import connections
from superadmin.models import Loja
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Corrige migrations inconsistentes em schemas de lojas'

    def handle(self, *args, **options):
        # Buscar todas as lojas
        lojas = list(Loja.objects.using('default').all())
        
        if not lojas:
            self.stdout.write(self.style.WARNING('Nenhuma loja encontrada'))
            return
        
        self.stdout.write(f'Encontradas {len(lojas)} loja(s)')
        
        corrigidas = 0
        for loja in lojas:
            db_name = loja.database_name
            schema_name = db_name.replace('-', '_')
            
            try:
                # Configurar banco
                from core.db_config import ensure_loja_database_config
                if not ensure_loja_database_config(db_name, conn_max_age=0):
                    continue
                
                # Conectar ao banco da loja
                conn = connections[db_name]
                conn.ensure_connection()
                
                with conn.cursor() as cursor:
                    # Definir search_path
                    cursor.execute(f'SET search_path TO "{schema_name}", public;')
                    
                    # Verificar se stores.0001_initial já está aplicada
                    cursor.execute("""
                        SELECT EXISTS (
                            SELECT 1 FROM django_migrations 
                            WHERE app = 'stores' AND name = '0001_initial'
                        );
                    """)
                    
                    existe = cursor.fetchone()[0]
                    
                    if not existe:
                        # Inserir migration
                        cursor.execute("""
                            INSERT INTO django_migrations (app, name, applied)
                            VALUES ('stores', '0001_initial', NOW());
                        """)
                        self.stdout.write(self.style.SUCCESS(
                            f'  ✅ Loja {loja.nome} (ID: {loja.id}): Migration stores.0001_initial marcada'
                        ))
                        corrigidas += 1
                    else:
                        self.stdout.write(f'  ℹ️  Loja {loja.nome} (ID: {loja.id}): Já corrigida')
                
                # Fechar conexão
                conn.close()
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(
                    f'  ❌ Loja {loja.nome} (ID: {loja.id}): Erro - {e}'
                ))
                logger.exception(f'Erro ao corrigir loja {loja.id}')
        
        self.stdout.write(self.style.SUCCESS(
            f'\n✅ Processamento concluído: {corrigidas} loja(s) corrigida(s)'
        ))
