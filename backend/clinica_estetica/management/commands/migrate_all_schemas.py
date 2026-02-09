"""
Comando para aplicar migrations em todos os schemas de lojas
"""
from django.core.management.base import BaseCommand
from django.db import connection
from django.core.management import call_command


class Command(BaseCommand):
    help = 'Aplica migrations em todos os schemas de lojas'

    def handle(self, *args, **options):
        from superadmin.models import Loja
        
        # Listar todas as lojas
        lojas = Loja.objects.filter(is_active=True)
        
        self.stdout.write(self.style.SUCCESS(f'📋 Encontradas {lojas.count()} lojas ativas'))
        self.stdout.write('')
        
        for loja in lojas:
            schema_name = loja.database_name.replace('-', '_')
            
            self.stdout.write(f'🔄 Aplicando migrations no schema: {schema_name} (Loja: {loja.nome})')
            
            try:
                # Configurar search_path para o schema da loja
                with connection.cursor() as cursor:
                    cursor.execute(f"SET search_path TO {schema_name}, public")
                    
                    # Verificar se a coluna loja_id já existe
                    cursor.execute("""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_schema = %s 
                        AND table_name = 'clinica_bloqueios_agenda' 
                        AND column_name = 'loja_id'
                    """, [schema_name])
                    
                    coluna_existe = cursor.fetchone() is not None
                    
                    if coluna_existe:
                        self.stdout.write(self.style.WARNING(f'  ⚠️  Coluna loja_id já existe'))
                    else:
                        # Adicionar coluna loja_id
                        self.stdout.write(f'  ➕ Adicionando coluna loja_id...')
                        cursor.execute(f"""
                            ALTER TABLE {schema_name}.clinica_bloqueios_agenda 
                            ADD COLUMN IF NOT EXISTS loja_id INTEGER NOT NULL DEFAULT {loja.id}
                        """)
                        
                        # Criar índice
                        cursor.execute(f"""
                            CREATE INDEX IF NOT EXISTS clinica_bloqueios_agenda_loja_id_idx 
                            ON {schema_name}.clinica_bloqueios_agenda (loja_id)
                        """)
                        
                        self.stdout.write(self.style.SUCCESS(f'  ✅ Coluna loja_id adicionada com sucesso'))
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ❌ Erro: {str(e)}'))
                continue
        
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('✅ Migrations aplicadas em todos os schemas!'))
