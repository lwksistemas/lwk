"""
Comando para verificar se há dados no schema public (compartilhado)
"""
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Verifica se há dados de clínica no schema public (compartilhado)'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*100)
        self.stdout.write('🔍 VERIFICAÇÃO DE DADOS NO SCHEMA PUBLIC (COMPARTILHADO)')
        self.stdout.write('='*100 + '\n')

        tabelas = [
            'clinica_estetica_cliente',
            'clinica_estetica_profissional',
            'clinica_estetica_procedimento',
            'clinica_estetica_agendamento',
            'clinica_estetica_consulta',
            'clinica_estetica_funcionario',
        ]

        self.stdout.write('Contagem de dados no schema PUBLIC:')
        self.stdout.write('-' * 100)

        total_registros = 0
        tabelas_com_dados = []

        with connection.cursor() as cursor:
            for tabela in tabelas:
                try:
                    cursor.execute(f'SELECT COUNT(*) FROM public.{tabela}')
                    count = cursor.fetchone()[0]
                    
                    if count > 0:
                        self.stdout.write(self.style.WARNING(f'⚠️  {tabela:50s}: {count:5d} registros'))
                        tabelas_com_dados.append((tabela, count))
                        total_registros += count
                    else:
                        self.stdout.write(f'✅ {tabela:50s}: {count:5d} registros')
                except Exception as e:
                    self.stdout.write(f'❌ {tabela:50s}: Erro - {e}')

        self.stdout.write('-' * 100)

        if total_registros > 0:
            self.stdout.write(self.style.ERROR(f'\n❌ PROBLEMA CRÍTICO: {total_registros} registros encontrados no schema PUBLIC!'))
            self.stdout.write(self.style.ERROR('❌ Dados no schema public são compartilhados entre TODAS as lojas!'))
            self.stdout.write(self.style.ERROR('❌ Por isso novas lojas já vêm com cadastros!\n'))
            
            self.stdout.write(self.style.WARNING('📋 Tabelas com dados no schema public:'))
            for tabela, count in tabelas_com_dados:
                self.stdout.write(f'   - {tabela}: {count} registros')
            
            self.stdout.write(self.style.WARNING('\n⚠️  SOLUÇÃO: Limpar dados do schema public'))
            self.stdout.write('   Execute: python manage.py limpar_schema_public --confirmar')
        else:
            self.stdout.write(self.style.SUCCESS('\n✅ Schema public está limpo (sem dados de clínica)'))
            self.stdout.write(self.style.SUCCESS('✅ Cada loja deve ter seus dados no próprio schema isolado'))

        self.stdout.write('\n' + '='*100 + '\n')
