"""
Comando para listar profissionais no schema de uma loja específica
"""
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Lista profissionais no schema de uma loja específica'

    def add_arguments(self, parser):
        parser.add_argument('loja_id', type=int, help='ID da loja')

    def handle(self, *args, **options):
        loja_id = options['loja_id']
        
        # Buscar a loja
        from superadmin.models import Loja
        try:
            loja = Loja.objects.get(id=loja_id)
        except Loja.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'❌ Loja {loja_id} não encontrada'))
            return
        
        schema_name = loja.database_name.replace('-', '_')
        self.stdout.write(self.style.SUCCESS(f'✅ Loja: {loja.nome} (ID: {loja.id})'))
        self.stdout.write(self.style.SUCCESS(f'✅ Schema: {schema_name}'))
        self.stdout.write('')
        
        # Configurar search_path para o schema da loja
        with connection.cursor() as cursor:
            cursor.execute(f"SET search_path TO {schema_name}, public")
            
            # Listar profissionais
            cursor.execute("""
                SELECT id, nome, especialidade, email, telefone, is_active, loja_id
                FROM clinica_profissionais
                ORDER BY id
            """)
            
            profissionais = cursor.fetchall()
            
            if not profissionais:
                self.stdout.write(self.style.WARNING('⚠️ Nenhum profissional encontrado neste schema'))
                return
            
            self.stdout.write(self.style.SUCCESS(f'📋 Profissionais no schema {schema_name}:'))
            self.stdout.write('')
            
            for prof in profissionais:
                prof_id, nome, especialidade, email, telefone, is_active, prof_loja_id = prof
                status = '✅' if is_active else '❌'
                self.stdout.write(
                    f'{status} ID: {prof_id} | {nome} | {especialidade} | '
                    f'{email} | {telefone} | loja_id: {prof_loja_id}'
                )
            
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS(f'Total: {len(profissionais)} profissionais'))
