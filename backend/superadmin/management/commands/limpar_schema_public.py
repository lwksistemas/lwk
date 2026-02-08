"""
Comando para limpar dados de clínica do schema public (compartilhado)
"""
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Limpa dados de clínica do schema public (compartilhado)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirmar',
            action='store_true',
            help='Confirma a operação de limpeza (OBRIGATÓRIO)',
        )

    def handle(self, *args, **options):
        confirmar = options.get('confirmar')

        if not confirmar:
            self.stdout.write(self.style.ERROR('❌ Erro: --confirmar é obrigatório'))
            self.stdout.write('⚠️  Esta operação apagará dados do schema PUBLIC (compartilhado)!')
            self.stdout.write('Uso: python manage.py limpar_schema_public --confirmar')
            return

        self.stdout.write('\n' + '='*100)
        self.stdout.write(self.style.WARNING('🗑️  LIMPEZA DO SCHEMA PUBLIC (COMPARTILHADO)'))
        self.stdout.write('='*100 + '\n')

        # Contar ANTES
        self.stdout.write('📊 Dados ANTES da limpeza:')
        with connection.cursor() as cursor:
            tabelas = [
                'clinica_estetica_transacao',
                'clinica_estetica_categoriafinanceira',
                'clinica_estetica_historicologin',
                'clinica_estetica_consulta',
                'clinica_estetica_evolucaopaciente',
                'clinica_estetica_anamnese',
                'clinica_estetica_anamnesestemplate',
                'clinica_estetica_agendamento',
                'clinica_estetica_bloqueioagenda',
                'clinica_estetica_horariofuncionamento',
                'clinica_estetica_protocoloprocedimento',
                'clinica_estetica_procedimento',
                'clinica_estetica_profissional',
                'clinica_estetica_cliente',
                'clinica_estetica_funcionario',
            ]

            for tabela in tabelas:
                try:
                    cursor.execute(f'SELECT COUNT(*) FROM public.{tabela}')
                    count = cursor.fetchone()[0]
                    if count > 0:
                        self.stdout.write(f'   {tabela}: {count}')
                except Exception as e:
                    pass

        # Limpar
        self.stdout.write('\n🗑️  Limpando dados do schema public...')
        with connection.cursor() as cursor:
            for tabela in tabelas:
                try:
                    cursor.execute(f'DELETE FROM public.{tabela}')
                    deleted = cursor.rowcount
                    if deleted > 0:
                        self.stdout.write(f'   ✓ {tabela}: {deleted} registros deletados')
                except Exception as e:
                    self.stdout.write(f'   ⚠️  {tabela}: {e}')

        # Contar DEPOIS
        self.stdout.write('\n📊 Dados DEPOIS da limpeza:')
        with connection.cursor() as cursor:
            total = 0
            for tabela in tabelas:
                try:
                    cursor.execute(f'SELECT COUNT(*) FROM public.{tabela}')
                    count = cursor.fetchone()[0]
                    total += count
                    if count > 0:
                        self.stdout.write(f'   {tabela}: {count}')
                except Exception as e:
                    pass

        if total == 0:
            self.stdout.write(self.style.SUCCESS('\n✅ Schema public limpo com sucesso!'))
            self.stdout.write(self.style.SUCCESS('✅ Novas lojas não terão mais cadastros pré-existentes'))
        else:
            self.stdout.write(self.style.WARNING(f'\n⚠️  Ainda há {total} registros no schema public'))

        self.stdout.write('\n' + '='*100 + '\n')
