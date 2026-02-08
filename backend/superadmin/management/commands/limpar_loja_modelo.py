"""
Comando para limpar dados da loja modelo/dashboard padrão
"""
from django.core.management.base import BaseCommand
from django.db import connection
from superadmin.models import Loja


class Command(BaseCommand):
    help = 'Limpa todos os dados de cadastro de uma loja específica (loja modelo)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--loja-slug',
            type=str,
            help='Slug da loja que deseja limpar (ex: harmonis-000126)',
        )
        parser.add_argument(
            '--confirmar',
            action='store_true',
            help='Confirma a operação de limpeza (OBRIGATÓRIO)',
        )

    def handle(self, *args, **options):
        loja_slug = options.get('loja_slug')
        confirmar = options.get('confirmar')

        if not loja_slug:
            self.stdout.write(self.style.ERROR('❌ Erro: --loja-slug é obrigatório'))
            self.stdout.write('Uso: python manage.py limpar_loja_modelo --loja-slug harmonis-000126 --confirmar')
            return

        if not confirmar:
            self.stdout.write(self.style.ERROR('❌ Erro: --confirmar é obrigatório'))
            self.stdout.write('⚠️  Esta operação é IRREVERSÍVEL e apagará TODOS os dados da loja!')
            self.stdout.write('Uso: python manage.py limpar_loja_modelo --loja-slug harmonis-000126 --confirmar')
            return

        # Buscar loja
        try:
            loja = Loja.objects.get(slug=loja_slug)
        except Loja.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'❌ Loja com slug "{loja_slug}" não encontrada!'))
            return

        self.stdout.write('\n' + '='*100)
        self.stdout.write(self.style.WARNING('🗑️  LIMPEZA DE DADOS DA LOJA MODELO'))
        self.stdout.write('='*100)
        self.stdout.write(f'\n✅ Loja encontrada: {loja.nome} (ID: {loja.id})')
        self.stdout.write(f'   Database: {loja.database_name}')
        self.stdout.write(f'   Tipo: {loja.tipo_loja.nome if loja.tipo_loja else "N/A"}')

        schema_name = loja.database_name.replace('-', '_')

        # Contar dados ANTES
        self.stdout.write('\n📊 Dados ANTES da limpeza:')
        with connection.cursor() as cursor:
            try:
                cursor.execute(f'SELECT COUNT(*) FROM "{schema_name}".clinica_estetica_cliente')
                clientes = cursor.fetchone()[0]
                self.stdout.write(f'   Clientes: {clientes}')

                cursor.execute(f'SELECT COUNT(*) FROM "{schema_name}".clinica_estetica_profissional')
                profissionais = cursor.fetchone()[0]
                self.stdout.write(f'   Profissionais: {profissionais}')

                cursor.execute(f'SELECT COUNT(*) FROM "{schema_name}".clinica_estetica_procedimento')
                procedimentos = cursor.fetchone()[0]
                self.stdout.write(f'   Procedimentos: {procedimentos}')

                cursor.execute(f'SELECT COUNT(*) FROM "{schema_name}".clinica_estetica_agendamento')
                agendamentos = cursor.fetchone()[0]
                self.stdout.write(f'   Agendamentos: {agendamentos}')

                cursor.execute(f'SELECT COUNT(*) FROM "{schema_name}".clinica_estetica_consulta')
                consultas = cursor.fetchone()[0]
                self.stdout.write(f'   Consultas: {consultas}')
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'   Erro ao contar: {e}'))

        # Limpar dados
        self.stdout.write('\n🗑️  Limpando dados...')
        with connection.cursor() as cursor:
            try:
                # Ordem de deleção respeitando foreign keys
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
                ]

                for tabela in tabelas:
                    try:
                        cursor.execute(f'DELETE FROM "{schema_name}".{tabela}')
                        deleted = cursor.rowcount
                        if deleted > 0:
                            self.stdout.write(f'   ✓ {tabela}: {deleted} registros deletados')
                    except Exception as e:
                        self.stdout.write(f'   ⚠️  {tabela}: {e}')

                # Limpar funcionários (manter apenas o owner)
                cursor.execute(f'''
                    DELETE FROM "{schema_name}".clinica_estetica_funcionario 
                    WHERE user_id != %s
                ''', [loja.owner_id])
                deleted = cursor.rowcount
                if deleted > 0:
                    self.stdout.write(f'   ✓ clinica_estetica_funcionario: {deleted} registros deletados (admin mantido)')

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'❌ Erro ao limpar dados: {e}'))
                return

        # Contar dados DEPOIS
        self.stdout.write('\n📊 Dados DEPOIS da limpeza:')
        with connection.cursor() as cursor:
            try:
                cursor.execute(f'SELECT COUNT(*) FROM "{schema_name}".clinica_estetica_cliente')
                clientes = cursor.fetchone()[0]
                self.stdout.write(f'   Clientes: {clientes}')

                cursor.execute(f'SELECT COUNT(*) FROM "{schema_name}".clinica_estetica_profissional')
                profissionais = cursor.fetchone()[0]
                self.stdout.write(f'   Profissionais: {profissionais}')

                cursor.execute(f'SELECT COUNT(*) FROM "{schema_name}".clinica_estetica_procedimento')
                procedimentos = cursor.fetchone()[0]
                self.stdout.write(f'   Procedimentos: {procedimentos}')

                cursor.execute(f'SELECT COUNT(*) FROM "{schema_name}".clinica_estetica_agendamento')
                agendamentos = cursor.fetchone()[0]
                self.stdout.write(f'   Agendamentos: {agendamentos}')

                cursor.execute(f'SELECT COUNT(*) FROM "{schema_name}".clinica_estetica_funcionario')
                funcionarios = cursor.fetchone()[0]
                self.stdout.write(f'   Funcionários: {funcionarios} (apenas admin)')
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'   Erro ao contar: {e}'))

        self.stdout.write('\n' + '='*100)
        self.stdout.write(self.style.SUCCESS('✅ Limpeza concluída com sucesso!'))
        self.stdout.write(self.style.SUCCESS(f'✅ A loja {loja.nome} está agora limpa e pronta para uso.'))
        self.stdout.write('='*100 + '\n')
