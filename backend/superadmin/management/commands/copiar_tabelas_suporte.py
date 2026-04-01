"""
Comando para copiar estrutura das tabelas do app suporte do schema public para o schema suporte.
"""
from django.core.management.base import BaseCommand
from django.db import connection
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Copia estrutura das tabelas do app suporte para o schema suporte'

    def handle(self, *args, **options):
        schema_destino = 'suporte'
        schema_origem = 'public'
        
        # Tabelas do app suporte
        tabelas_suporte = [
            'suporte_chamado',
            'suporte_errofrontend',
            'suporte_respostachamado',
        ]
        
        self.stdout.write(f'📋 Copiando estrutura de {len(tabelas_suporte)} tabela(s) do schema {schema_origem} para {schema_destino}...\n')
        
        try:
            with connection.cursor() as cursor:
                for tabela in tabelas_suporte:
                    try:
                        self.stdout.write(f'  🔄 Copiando {tabela}...')
                        
                        # Verificar se tabela existe no schema origem
                        cursor.execute("""
                            SELECT 1 FROM information_schema.tables 
                            WHERE table_schema = %s AND table_name = %s
                        """, [schema_origem, tabela])
                        
                        if not cursor.fetchone():
                            self.stdout.write(self.style.WARNING(f'    ⚠️  Tabela {tabela} não existe no schema {schema_origem}'))
                            continue
                        
                        # Verificar se tabela já existe no schema destino
                        cursor.execute("""
                            SELECT 1 FROM information_schema.tables 
                            WHERE table_schema = %s AND table_name = %s
                        """, [schema_destino, tabela])
                        
                        if cursor.fetchone():
                            self.stdout.write(self.style.WARNING(f'    ⚠️  Tabela {tabela} já existe no schema {schema_destino}'))
                            continue
                        
                        # Copiar estrutura da tabela (sem dados)
                        cursor.execute(f"""
                            CREATE TABLE {schema_destino}.{tabela} 
                            (LIKE {schema_origem}.{tabela} INCLUDING ALL)
                        """)
                        
                        self.stdout.write(self.style.SUCCESS(f'    ✅ {tabela} copiada'))
                        
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'    ❌ Erro ao copiar {tabela}: {e}'))
                        logger.exception(f'Erro ao copiar tabela {tabela}')
            
            # Verificar tabelas criadas
            self.stdout.write(f'\n📊 Verificando tabelas no schema {schema_destino}...')
            
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = %s AND table_type = 'BASE TABLE'
                    ORDER BY table_name
                """, [schema_destino])
                
                tabelas = cursor.fetchall()
                
                if tabelas:
                    self.stdout.write(self.style.SUCCESS(f'\n✅ {len(tabelas)} tabela(s) no schema {schema_destino}:'))
                    for tabela in tabelas:
                        self.stdout.write(f'  - {tabela[0]}')
                else:
                    self.stdout.write(self.style.WARNING('⚠️  Nenhuma tabela encontrada'))
            
            self.stdout.write(self.style.SUCCESS(f'\n✅ Cópia concluída!'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ Erro: {e}'))
            logger.exception('Erro ao copiar tabelas')
